"""
Web Search Tool — DuckDuckGo search, no API key needed.
"""

from duckduckgo_search import DDGS
from typing import Dict, List


class WebSearchTool:
    """Searches the web via DuckDuckGo. Free. No key. No rate limits."""

    name = "web_search"
    description = "Search the web for current information. Use when you need facts, recent data, or to verify claims."
    parameters = '{"query": "search query string"}'

    async def execute(self, params: Dict) -> str:
        """Run a web search and return formatted results."""
        query = params.get("query", "")
        if not query:
            return "Error: No search query provided"

        try:
            results = self._search(query, max_results=5)
            if not results:
                return f"No results found for: {query}"

            formatted = [f"Web search results for: '{query}'\n"]
            for i, r in enumerate(results, 1):
                formatted.append(
                    f"{i}. **{r['title']}**\n"
                    f"   {r['body']}\n"
                    f"   Source: {r['href']}\n"
                )
            return "\n".join(formatted)

        except Exception as e:
            return f"Search failed (you may be offline): {str(e)}"

    def _search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Perform DuckDuckGo search."""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
