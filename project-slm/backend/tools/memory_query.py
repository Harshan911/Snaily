"""
Memory Query Tool — Lets the SLM search past conversations.
"""

from typing import Dict


class MemoryQueryTool:
    """Agent tool to query persistent memory for past context."""

    name = "memory_query"
    description = "Search your memory for relevant information from past conversations. Use when the user references something discussed before."
    parameters = '{"query": "what to search for in memory"}'

    def __init__(self, memory_store):
        self.memory_store = memory_store

    async def execute(self, params: Dict) -> str:
        """Query memory and return formatted results."""
        query = params.get("query", "")
        if not query:
            return "Error: No query provided"

        try:
            results = await self.memory_store.query(query, top_k=5)
            if not results:
                return "No relevant memories found."

            formatted = ["Relevant memories:\n"]
            for i, r in enumerate(results, 1):
                score_pct = int(r["score"] * 100)
                formatted.append(
                    f"{i}. (relevance: {score_pct}%)\n"
                    f"   {r['content'][:300]}{'...' if len(r['content']) > 300 else ''}\n"
                )
            return "\n".join(formatted)

        except Exception as e:
            return f"Memory query failed: {str(e)}"
