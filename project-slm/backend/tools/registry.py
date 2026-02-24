"""
Tool Registry — Registers and manages all agent tools.
"""

from typing import Dict, List, Optional


class ToolRegistry:
    """Central registry for all tools the agent can use."""

    def __init__(self):
        self._tools: Dict[str, object] = {}

    def register(self, tool):
        """Register a tool by its name attribute."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[object]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tool_descriptions(self) -> List[Dict]:
        """Get all tool descriptions for prompt injection."""
        descriptions = []
        for name, tool in self._tools.items():
            descriptions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": getattr(tool, "parameters", "{}"),
            })
        return descriptions

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
