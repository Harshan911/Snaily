"""
Local Inference — Calls Ollama for local SLM inference.
"""

import ollama
from typing import List, Dict, AsyncGenerator


class LocalInference:
    """Local inference via Ollama (wraps llama.cpp)."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            self._client = ollama.AsyncClient()
        return self._client

    async def generate(self, model: str, system_prompt: str,
                       messages: List[Dict]) -> str:
        """Generate a complete response (non-streaming)."""
        client = self._get_client()

        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        try:
            response = await client.chat(
                model=model,
                messages=full_messages,
                stream=False,
            )
            # Ollama returns ChatResponse object — access via attribute
            if hasattr(response, 'message'):
                return response.message.content
            elif isinstance(response, dict):
                return response.get("message", {}).get("content", "")
            else:
                return str(response)
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                return (
                    "⚠️ Cannot connect to Ollama. "
                    "Make sure Ollama is running (start it with `ollama serve` in terminal). "
                    "If not installed, download from https://ollama.com"
                )
            if "not found" in error_msg.lower():
                return (
                    f"⚠️ Model '{model}' not found. "
                    "Please download a model first from the Model Portal."
                )
            raise

    async def generate_stream(self, model: str, system_prompt: str,
                              messages: List[Dict]) -> AsyncGenerator:
        """Generate a streaming response — yields tokens one by one."""
        client = self._get_client()

        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        try:
            stream = await client.chat(
                model=model,
                messages=full_messages,
                stream=True,
            )
            async for chunk in stream:
                # ChatResponse chunks have .message.content
                if hasattr(chunk, 'message'):
                    token = chunk.message.content or ""
                elif isinstance(chunk, dict):
                    token = chunk.get("message", {}).get("content", "")
                else:
                    token = ""

                if token:
                    yield token
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                yield (
                    "⚠️ Cannot connect to Ollama. "
                    "Make sure Ollama is running."
                )
            elif "not found" in error_msg.lower():
                yield (
                    f"⚠️ Model '{model}' not found. "
                    "Download one from the Model Portal (click 'Download Models' in sidebar)."
                )
            else:
                yield f"⚠️ Error: {error_msg}"
