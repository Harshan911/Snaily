"""
Skill Validator — Security sandbox for skill files.
Text-only. No code execution. Ever.
"""

from pathlib import Path
from typing import Dict
import frontmatter
import logging

logger = logging.getLogger(__name__)

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
    "!!python",  # YAML deserialization exploit
    "!!binary",
    "!!map",
    "!!omap",
    "!!pairs",
    "!!set",
    "__class__",
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "os.path",
    "sys.exit",
    "importlib",
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
        # Sanitize filename — prevent path traversal
        safe_name = Path(filename).name
        if safe_name != filename or '..' in filename:
            return {
                "filename": filename,
                "valid": False,
                "errors": ["Invalid filename: contains path traversal characters"],
                "warnings": [],
            }

        filepath = SKILL_DOCK_DIR / safe_name
        result = {
            "filename": safe_name,
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Check existence
        if not filepath.exists():
            result["valid"] = False
            result["errors"].append(f"File not found: {safe_name}")
            return result

        # Verify the resolved path stays within dock directory
        try:
            filepath.resolve().relative_to(SKILL_DOCK_DIR.resolve())
        except ValueError:
            result["valid"] = False
            result["errors"].append("File path escapes skill dock directory")
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
