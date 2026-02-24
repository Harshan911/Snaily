"""
Skill Validator — Security sandbox for skill files.
Text-only. No code execution. Ever.
"""

from pathlib import Path
from typing import Dict
import frontmatter

SKILL_DOCK_DIR = Path(__file__).parent / "dock"

# Dangerous patterns that should NEVER appear in a skill file
BLOCKED_PATTERNS = [
    "exec(",
    "eval(",
    "import os",
    "import subprocess",
    "os.system(",
    "subprocess.",
    "__import__",
    "open(",
    "shutil.",
    "requests.",
    "urllib.",
    "<script",
    "javascript:",
    "rm -rf",
    "del /f",
    "format c:",
]

REQUIRED_FIELDS = ["name", "description"]
MAX_FILE_SIZE_KB = 100  # skill files should be tiny


class SkillValidator:
    """Validates skill files for safety and format correctness."""

    def validate_file(self, filename: str) -> Dict:
        """
        Validate a skill file. Returns result dict.

        Checks:
        1. File exists and is small enough
        2. Has valid YAML frontmatter
        3. Has required fields
        4. Contains no dangerous patterns
        5. Is plain text only
        """
        filepath = SKILL_DOCK_DIR / filename
        result = {
            "filename": filename,
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Check existence
        if not filepath.exists():
            result["valid"] = False
            result["errors"].append(f"File not found: {filename}")
            return result

        # Check extension
        if filepath.suffix not in (".md", ".yaml", ".yml"):
            result["valid"] = False
            result["errors"].append(f"Invalid extension: {filepath.suffix}. Must be .md, .yaml, or .yml")
            return result

        # Check file size
        size_kb = filepath.stat().st_size / 1024
        if size_kb > MAX_FILE_SIZE_KB:
            result["valid"] = False
            result["errors"].append(f"File too large: {size_kb:.1f} KB (max {MAX_FILE_SIZE_KB} KB)")
            return result

        # Read content
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Cannot read file: {e}")
            return result

        # Check for dangerous patterns
        content_lower = content.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in content_lower:
                result["valid"] = False
                result["errors"].append(f"Blocked pattern detected: '{pattern}'")

        # Check YAML frontmatter
        try:
            post = frontmatter.loads(content)
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Invalid frontmatter: {e}")
            return result

        # Check required fields
        for field in REQUIRED_FIELDS:
            if not post.get(field):
                result["valid"] = False
                result["errors"].append(f"Missing required field: '{field}'")

        # Check for markdown body
        if not post.content.strip():
            result["warnings"].append("Skill file has no body content (only frontmatter)")

        # Check for guardrails section
        if "## Guardrails" not in content and "## guardrails" not in content.lower():
            result["warnings"].append("No '## Guardrails' section found — consider adding one")

        return result
