"""
Model Manager — Download, list, switch SLMs via Ollama.
"""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.warning("Ollama package not installed. Model management will not be available.")


class ModelManager:
    """Manages SLM lifecycle: list installed, download, switch active model."""

    def __init__(self):
        self.active_model: str = "qwen3:4b"  # default
        self._client = None

    def _get_client(self):
        """Lazy init Ollama client."""
        if not HAS_OLLAMA:
            raise RuntimeError("Ollama package not installed. Run: pip install ollama")
        if not self._client:
            self._client = ollama.AsyncClient()
        return self._client

    async def list_installed(self) -> List[Dict]:
        """List all locally installed models."""
        try:
            client = self._get_client()
            response = await client.list()

            # Ollama Python API returns ListResponse object with .models attribute
            models_list = getattr(response, 'models', None)
            if models_list is None:
                # Fallback: try dict-style access
                models_list = response.get("models", []) if isinstance(response, dict) else []

            models = []
            for model in models_list:
                # Model objects have attributes, not dict keys
                name = getattr(model, 'model', None) or getattr(model, 'name', 'unknown')
                size = getattr(model, 'size', 0)
                modified = getattr(model, 'modified_at', '')
                details = getattr(model, 'details', None)

                family = ''
                quant = ''
                if details:
                    family = getattr(details, 'family', '') or ''
                    quant = getattr(details, 'quantization_level', '') or ''

                models.append({
                    "name": name,
                    "size_gb": round(size / (1024**3), 2) if size else 0,
                    "modified": str(modified),
                    "family": family,
                    "quantization": quant,
                })

            # Auto-set active model if none set and models exist
            if models and self.active_model == "qwen3:4b":
                installed_names = [m["name"] for m in models]
                if self.active_model not in installed_names and not any(
                    self.active_model in n or n in self.active_model for n in installed_names
                ):
                    # Active model not installed, pick first available
                    self.active_model = installed_names[0]

            return models
        except Exception as e:
            error_str = str(e).lower()
            if "connect" in error_str or "refused" in error_str:
                return []  # Ollama not running — return empty, not error
            return []

    async def download(self, model_name: str):
        """Download a model via Ollama pull. Consumes the full async stream."""
        try:
            client = self._get_client()
            # pull() returns an async iterator that MUST be consumed
            response = await client.pull(model_name, stream=False)
            return response
        except Exception as e:
            error_str = str(e).lower()
            if "connect" in error_str or "refused" in error_str:
                raise ConnectionError(
                    "Ollama is not running. Start it with 'ollama serve' or install from https://ollama.com"
                )
            raise

    async def switch(self, model_name: str):
        """Switch to a different model (must be installed)."""
        installed = await self.list_installed()
        installed_names = [m.get("name", "") for m in installed]

        # Ollama names can have :tag — do flexible matching
        matched = False
        for name in installed_names:
            if model_name in name or name in model_name:
                self.active_model = name
                matched = True
                break

        if not matched:
            # If model just downloaded, accept it directly but log a warning
            logger.warning(
                f"Model '{model_name}' not found in installed list. "
                "Setting as active anyway (may have just been downloaded)."
            )
            self.active_model = model_name
            return

    async def delete(self, model_name: str):
        """Delete a locally installed model."""
        client = self._get_client()
        await client.delete(model_name)
