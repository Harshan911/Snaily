"""
Prompt Builder — Assembles the system prompt from base + skills + memory + tools.
"""

from typing import List


BASE_SYSTEM_PROMPT = """You are Snaily — a helpful, precise, and honest assistant running locally on the user's machine.

Core Rules:
- Be direct. No fluff. Get the job done.
- If you are uncertain about a fact, say so explicitly. Never fabricate information.
- If a question requires current information, use the web_search tool.
- If you recall something relevant from past conversations, mention it.
- Keep responses concise unless the user asks for detail.
- Respect privacy — all data stays local on this machine.

Tool Usage:
When you need to use a tool, format your call exactly like this:
[TOOL_CALL: tool_name]
{"param1": "value1", "param2": "value2"}
[/TOOL_CALL]

After using a tool, incorporate the result naturally into your response.
Only use tools when genuinely needed — don't use them for questions you can answer directly.
"""


class PromptBuilder:
    """Builds the full system prompt by combining base + skills + memory + tools."""

    def build(self, active_skills: List[dict] = None,
              memory_context: str = "",
              available_tools: List[dict] = None,
              web_context: str = "") -> str:
        """
        Assemble final system prompt.

        Args:
            active_skills: List of parsed skill dicts (from SkillParser)
            memory_context: Relevant past context from memory RAG
            available_tools: List of tool descriptions for the SLM
            web_context: Live web search results to ground the response
        """
        parts = [BASE_SYSTEM_PROMPT]

        # Inject active skills
        if active_skills:
            parts.append(self._build_skills_section(active_skills))

        # Inject available tools
        if available_tools:
            parts.append(self._build_tools_section(available_tools))

        # Inject web search results (highest priority context)
        if web_context:
            parts.append(self._build_web_section(web_context))

        # Inject memory context
        if memory_context:
            parts.append(self._build_memory_section(memory_context))

        return "\n\n".join(parts)

    def _build_skills_section(self, skills: List[dict]) -> str:
        """Build the skills injection block."""
        lines = ["## Active Skills (follow these strictly)"]
        for skill in skills:
            lines.append(f"\n### Skill: {skill.get('name', 'unnamed')}")
            lines.append(f"Description: {skill.get('description', 'N/A')}")

            # Guardrails
            guardrails = skill.get("guardrails", [])
            if guardrails:
                lines.append("\nGuardrails (NEVER violate):")
                for g in guardrails:
                    lines.append(f"  - {g}")

            # Workflow
            workflow = skill.get("workflow", [])
            if workflow:
                lines.append("\nWorkflow (follow in order):")
                for i, step in enumerate(workflow, 1):
                    lines.append(f"  {i}. {step}")

            # Output format
            output_format = skill.get("output_format", [])
            if output_format:
                lines.append("\nOutput Format:")
                for f in output_format:
                    lines.append(f"  - {f}")

            # Examples
            examples = skill.get("examples", "")
            if examples:
                lines.append(f"\nExamples:\n{examples}")

        return "\n".join(lines)

    def _build_tools_section(self, tools: List[dict]) -> str:
        """Build the available tools reference block."""
        lines = ["## Available Tools"]
        for tool in tools:
            lines.append(f"- **{tool['name']}**: {tool['description']}")
            if tool.get("parameters"):
                lines.append(f"  Parameters: {tool['parameters']}")
        return "\n".join(lines)

    def _build_memory_section(self, memory_context: str) -> str:
        """Build the memory context block."""
        return (
            "## Relevant Context from Past Conversations\n"
            "Use this if relevant to the current question:\n"
            f"{memory_context}"
        )

    def _build_web_section(self, web_context: str) -> str:
        """Build the web search results block."""
        return (
            "## Live Web Search Results\n"
            "The user has web search ENABLED. The following are FRESH results "
            "from the web for this query. Use these as your PRIMARY source of "
            "truth. Cite sources when possible. If the results are relevant, "
            "incorporate them into your answer. If not relevant, answer from "
            "your own knowledge and mention the search didn't find useful results.\n\n"
            f"{web_context}"
        )
