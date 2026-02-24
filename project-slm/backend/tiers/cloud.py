"""
Cloud Inference — API-based inference for cloud tier.
Supports OpenAI-compatible APIs (OpenAI, Anthropic, Google).
"""

import json
from typing import List, Dict, AsyncGenerator

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# Provider configs
PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "default_model": "gpt-4o-mini",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "default_model": "claude-sonnet-4-20250514",
        "auth_header": "x-api-key",
        "auth_prefix": "",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "default_model": "gemini-2.0-flash",
        "auth_header": None,  # uses query param
        "auth_prefix": "",
    },
}


class CloudInference:
    """Cloud inference via API — fallback for users without local hardware."""

    def __init__(self):
        self.api_key = None
        self.provider = None
        self.provider_config = None

    def configure(self, api_key: str, provider: str = "openai"):
        """Configure cloud provider and API key."""
        self.api_key = api_key
        self.provider = provider
        self.provider_config = PROVIDERS.get(provider, PROVIDERS["openai"])

    async def generate(self, model: str, system_prompt: str,
                       messages: List[Dict]) -> str:
        """Generate response via cloud API (non-streaming)."""
        if not self.api_key:
            return "⚠️ Cloud tier requires an API key. Set it in Settings → Tier."

        if not HAS_HTTPX:
            return "⚠️ Cloud tier requires httpx. Run: pip install httpx"

        if self.provider == "openai":
            return await self._openai_generate(model, system_prompt, messages)
        elif self.provider == "anthropic":
            return await self._anthropic_generate(model, system_prompt, messages)
        elif self.provider == "google":
            return await self._google_generate(model, system_prompt, messages)
        else:
            return f"⚠️ Unknown provider: {self.provider}"

    async def generate_stream(self, model: str, system_prompt: str,
                              messages: List[Dict]) -> AsyncGenerator:
        """Streaming cloud response — falls back to non-streaming + yields all at once."""
        # Simplified: full response then yield
        # Full streaming per provider can be added later
        response = await self.generate(model, system_prompt, messages)
        yield response

    # ── OpenAI Compatible ─────────────────────────────────

    async def _openai_generate(self, model: str, system_prompt: str,
                               messages: List[Dict]) -> str:
        config = self.provider_config
        use_model = model if model != "qwen3:4b" else config["default_model"]

        payload = {
            "model": use_model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        headers = {
            "Content-Type": "application/json",
            config["auth_header"]: f"{config['auth_prefix']}{self.api_key}",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(config["base_url"], json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Anthropic ─────────────────────────────────────────

    async def _anthropic_generate(self, model: str, system_prompt: str,
                                  messages: List[Dict]) -> str:
        config = self.provider_config
        use_model = model if model != "qwen3:4b" else config["default_model"]

        payload = {
            "model": use_model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": 2048,
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(config["base_url"], json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    # ── Google Gemini ─────────────────────────────────────

    async def _google_generate(self, model: str, system_prompt: str,
                               messages: List[Dict]) -> str:
        config = self.provider_config
        use_model = model if model != "qwen3:4b" else config["default_model"]

        url = f"{config['base_url']}/{use_model}:generateContent?key={self.api_key}"

        # Convert to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
        }

        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
