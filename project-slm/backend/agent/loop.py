"""
Agent Loop — The brain's reasoning cycle.
Reason → Tool Call → Observe → Respond.
"""

import uuid
import json
import re
from typing import Optional, List, Dict, AsyncGenerator


class AgentLoop:
    """
    Core agent loop that orchestrates:
    1. Build system prompt (base + active skills)
    2. Retrieve relevant memory
    3. Send to SLM (local or cloud)
    4. Parse tool calls from SLM response
    5. Execute tools → feed results back
    6. Return final response + save to memory
    """

    def __init__(self, prompt_builder, tool_registry, local_inference,
                 cloud_inference, memory_store, model_manager):
        self.prompt_builder = prompt_builder
        self.tool_registry = tool_registry
        self.local_inference = local_inference
        self.cloud_inference = cloud_inference
        self.memory_store = memory_store
        self.model_manager = model_manager
        self.current_tier = "local"  # default
        self.api_key = None
        self.api_provider = None
        self.conversations: Dict[str, List[Dict]] = {}  # in-memory conversation history

    def set_tier(self, tier: str, api_key: str = None, api_provider: str = None):
        """Switch between local and cloud inference."""
        self.current_tier = tier
        self.api_key = api_key
        self.api_provider = api_provider

    def _get_inference(self):
        """Get the active inference backend."""
        if self.current_tier == "cloud":
            self.cloud_inference.configure(self.api_key, self.api_provider)
            return self.cloud_inference
        return self.local_inference

    def _get_or_create_conversation(self, conversation_id: Optional[str]) -> tuple:
        """Get existing or create new conversation."""
        if conversation_id and conversation_id in self.conversations:
            return conversation_id, self.conversations[conversation_id]
        new_id = conversation_id or str(uuid.uuid4())
        self.conversations[new_id] = []
        return new_id, self.conversations[new_id]

    async def run(self, user_message: str, conversation_id: Optional[str] = None,
                  active_skills: List[dict] = None) -> dict:
        """
        Full agent loop — non-streaming.
        Returns: {"reply": str, "conversation_id": str, "tools_used": list}
        """
        conv_id, history = self._get_or_create_conversation(conversation_id)
        tools_used = []

        # Step 1: Retrieve relevant memory
        memory_context = await self._retrieve_memory(user_message)

        # Step 2: Build system prompt with skills + memory
        system_prompt = self.prompt_builder.build(
            active_skills=active_skills or [],
            memory_context=memory_context,
            available_tools=self.tool_registry.get_tool_descriptions(),
        )

        # Step 3: Add user message to history
        history.append({"role": "user", "content": user_message})

        # Step 4: Run inference loop (may loop for tool calls)
        max_tool_rounds = 3
        for _ in range(max_tool_rounds):
            inference = self._get_inference()
            response = await inference.generate(
                model=self.model_manager.active_model,
                system_prompt=system_prompt,
                messages=history,
            )

            # Step 5: Check for tool calls in response
            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                # No tool calls — this is the final response
                break

            # Step 6: Execute tools and feed results back
            tool_results = await self._execute_tools(tool_calls)
            tools_used.extend([tc["tool"] for tc in tool_calls])

            # Add assistant's tool-calling message + tool results to history
            history.append({"role": "assistant", "content": response})
            for result in tool_results:
                history.append({
                    "role": "user",
                    "content": f"[Tool Result: {result['tool']}]\n{result['result']}"
                })

        # Step 7: Clean response (remove tool call syntax if any leaked)
        final_reply = self._clean_response(response)

        # Step 8: Save to history and memory
        history.append({"role": "assistant", "content": final_reply})
        await self._save_to_memory(user_message, final_reply, conv_id)

        return {
            "reply": final_reply,
            "conversation_id": conv_id,
            "tools_used": tools_used,
        }

    async def run_stream(self, user_message: str, conversation_id: Optional[str] = None,
                         active_skills: List[dict] = None) -> AsyncGenerator:
        """
        Streaming agent loop — yields token chunks.
        For tool calls, runs non-streaming first, then streams final response.
        """
        conv_id, history = self._get_or_create_conversation(conversation_id)
        tools_used = []

        # Retrieve memory
        memory_context = await self._retrieve_memory(user_message)

        # Build prompt
        system_prompt = self.prompt_builder.build(
            active_skills=active_skills or [],
            memory_context=memory_context,
            available_tools=self.tool_registry.get_tool_descriptions(),
        )

        history.append({"role": "user", "content": user_message})

        # First pass: check for tool calls (non-streaming)
        inference = self._get_inference()
        first_response = await inference.generate(
            model=self.model_manager.active_model,
            system_prompt=system_prompt,
            messages=history,
        )

        tool_calls = self._parse_tool_calls(first_response)

        if tool_calls:
            # Execute tools
            tool_results = await self._execute_tools(tool_calls)
            tools_used.extend([tc["tool"] for tc in tool_calls])

            history.append({"role": "assistant", "content": first_response})
            for result in tool_results:
                history.append({
                    "role": "user",
                    "content": f"[Tool Result: {result['tool']}]\n{result['result']}"
                })

        # Stream final response
        collected = ""
        async for token in inference.generate_stream(
            model=self.model_manager.active_model,
            system_prompt=system_prompt,
            messages=history,
        ):
            collected += token
            yield {"token": token, "conversation_id": conv_id}

        final_reply = self._clean_response(collected)
        history.append({"role": "assistant", "content": final_reply})
        await self._save_to_memory(user_message, final_reply, conv_id)

        yield {
            "done": True,
            "conversation_id": conv_id,
            "tools_used": tools_used,
        }

    async def _retrieve_memory(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant past context from memory."""
        try:
            results = await self.memory_store.query(query, top_k=top_k)
            if not results:
                return ""
            memory_lines = []
            for r in results:
                memory_lines.append(f"- {r['content']} (relevance: {r['score']:.2f})")
            return "\n".join(memory_lines)
        except Exception:
            return ""

    async def _save_to_memory(self, user_msg: str, assistant_msg: str, conv_id: str):
        """Save conversation turn to persistent memory."""
        try:
            combined = f"User: {user_msg}\nAssistant: {assistant_msg}"
            await self.memory_store.add(
                content=combined,
                metadata={"conversation_id": conv_id},
            )
        except Exception:
            pass  # Memory save failure should not break chat

    def _parse_tool_calls(self, response: str) -> List[dict]:
        """
        Parse tool calls from SLM response.
        Expected format:
        [TOOL_CALL: tool_name]
        {"param": "value"}
        [/TOOL_CALL]
        """
        tool_calls = []
        pattern = r'\[TOOL_CALL:\s*(\w+)\]\s*(\{.*?\})\s*\[/TOOL_CALL\]'
        matches = re.findall(pattern, response, re.DOTALL)

        for tool_name, params_str in matches:
            try:
                params = json.loads(params_str)
                tool_calls.append({"tool": tool_name, "params": params})
            except json.JSONDecodeError:
                continue

        return tool_calls

    async def _execute_tools(self, tool_calls: List[dict]) -> List[dict]:
        """Execute parsed tool calls and return results."""
        results = []
        for tc in tool_calls:
            tool = self.tool_registry.get(tc["tool"])
            if tool:
                try:
                    result = await tool.execute(tc["params"])
                    results.append({"tool": tc["tool"], "result": result})
                except Exception as e:
                    results.append({"tool": tc["tool"], "result": f"Error: {str(e)}"})
            else:
                results.append({"tool": tc["tool"], "result": f"Unknown tool: {tc['tool']}"})
        return results

    def _clean_response(self, response: str) -> str:
        """Remove tool call syntax from final response."""
        cleaned = re.sub(
            r'\[TOOL_CALL:\s*\w+\]\s*\{.*?\}\s*\[/TOOL_CALL\]',
            '', response, flags=re.DOTALL
        )
        return cleaned.strip()
