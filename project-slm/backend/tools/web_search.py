"""
Web Search Tool — Firecrawl Search API.
Uses Firecrawl to search the web and return LLM-ready snippets.
Requires: Firecrawl API Key.
"""

import json
import asyncio
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Config file for storing search credentials
SEARCH_CONFIG_PATH = Path(__file__).parent.parent / "search_config.json"

FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v1/search"


class WebSearchTool:
    """Searches the web via Firecrawl Search API."""

    name = "web_search"
    description = "Search the web for current information using Firecrawl."
    parameters = '{"query": "search query string"}'

    def __init__(self):
        self._api_key = None
        self._load_config()

    def _load_config(self):
        """Load saved Firecrawl credentials from disk."""
        try:
            if SEARCH_CONFIG_PATH.exists():
                with open(SEARCH_CONFIG_PATH, "r") as f:
                    config = json.load(f)
                self._api_key = config.get("firecrawl_api_key", "")
                if self._api_key:
                    logger.info("Firecrawl API credentials loaded")
                else:
                    logger.info("Firecrawl API credentials not configured yet")
        except Exception as e:
            logger.warning(f"Failed to load search config: {e}")

    def save_config(self, api_key: str):
        """Save Firecrawl Search credentials to disk."""
        self._api_key = api_key.strip()
        try:
            with open(SEARCH_CONFIG_PATH, "w") as f:
                json.dump({
                    "firecrawl_api_key": self._api_key,
                }, f, indent=2)
            logger.info("Firecrawl API credentials saved")
        except Exception as e:
            logger.warning(f"Failed to save search config: {e}")

    def get_config_status(self) -> dict:
        """Return whether search is configured (without exposing full keys)."""
        configured = bool(self._api_key)
        return {
            "configured": configured,
            "has_api_key": bool(self._api_key),
            # Show masked key for UI feedback
            "api_key_preview": f"...{self._api_key[-6:]}" if self._api_key and len(self._api_key) > 6 else "",
        }

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def execute(self, params: Dict) -> str:
        """Run a Firecrawl search and return formatted results."""
        query = params.get("query", "").strip()
        if not query:
            return "Error: No search query provided"

        if not self._api_key:
            return ("Error: Firecrawl Search not configured. "
                    "Go to Settings → Web Search and enter your Firecrawl API Key.")

        # Truncate very long queries
        if len(query) > 500:
            query = query[:500]

        try:
            results = await asyncio.to_thread(self._search, query, 5)
            if not results:
                return f"No results found for: {query}"

            formatted = [f"Web search results for: '{query}' (via Firecrawl)\n"]
            for i, r in enumerate(results, 1):
                title = r.get('title') or r.get('metadata', {}).get('title', 'No Title')
                snippet = r.get('description') or r.get('markdown', '')[:300] or 'No description available'
                url = r.get('url') or r.get('metadata', {}).get('sourceURL', 'Unknown source')
                
                formatted.append(
                    f"{i}. **{title}**\n"
                    f"   {snippet}...\n"
                    f"   Source: {url}\n"
                )
            return "\n".join(formatted)

        except Exception as e:
            logger.warning(f"Firecrawl search failed: {e}")
            return f"Search failed: {str(e)}"

    def _search(self, query: str, limit: int = 5) -> List[Dict]:
        """Perform Firecrawl search (synchronous, runs in thread)."""
        data = json.dumps({
            "query": query,
            "limit": limit,
            "lang": "en"
        }).encode("utf-8")

        req = urllib.request.Request(
            FIRECRAWL_SEARCH_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Snaily/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 401:
                raise RuntimeError("Firecrawl API key invalid or expired.")
            elif e.code == 429:
                raise RuntimeError("Firecrawl rate limit exceeded.")
            else:
                raise RuntimeError(f"Firecrawl API error {e.code}: {body[:200]}")

        # Firecrawl returns results in 'data'
        return res_data.get("data", [])
