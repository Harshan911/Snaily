"""
Skill Parser — Reads .md/.yaml skill files, extracts structure for prompt injection.
"""

import os
import frontmatter
from typing import List, Dict, Optional
from pathlib import Path


SKILL_DOCK_DIR = Path(__file__).parent / "dock"


class SkillParser:
    """
    Parses skill files from the dock directory.
    Skill format: YAML frontmatter + Markdown body.
    """

    def __init__(self, dock_dir: Path = None):
        self.dock_dir = dock_dir or SKILL_DOCK_DIR
        self.dock_dir.mkdir(parents=True, exist_ok=True)
        self.active_skills: List[Dict] = []
        self._all_skills: Dict[str, Dict] = {}  # filename → parsed skill

    def load_all_skills(self):
        """Scan dock directory and parse all valid skill files."""
        self._all_skills = {}
        for filepath in self.dock_dir.iterdir():
            if filepath.suffix in (".md", ".yaml", ".yml"):
                try:
                    parsed = self._parse_file(filepath)
                    if parsed:
                        self._all_skills[filepath.name] = parsed
                except Exception as e:
                    print(f"⚠️  Failed to parse skill '{filepath.name}': {e}")

    def list_skills(self) -> List[Dict]:
        """List all parsed skills with metadata."""
        skills = []
        for filename, skill in self._all_skills.items():
            skills.append({
                "filename": filename,
                "name": skill.get("name", filename),
                "description": skill.get("description", ""),
                "version": skill.get("version", "1.0"),
                "active": filename in [s.get("_filename") for s in self.active_skills],
                "requires": skill.get("requires", {}),
            })
        return skills

    def activate(self, filename: str) -> Dict:
        """Activate a skill by filename."""
        if filename not in self._all_skills:
            # Try reloading
            filepath = self.dock_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Skill file '{filename}' not found in dock")
            parsed = self._parse_file(filepath)
            if not parsed:
                raise ValueError(f"Failed to parse '{filename}'")
            self._all_skills[filename] = parsed

        skill = self._all_skills[filename]

        # Don't activate twice
        if any(s.get("_filename") == filename for s in self.active_skills):
            return skill

        skill_copy = dict(skill)
        skill_copy["_filename"] = filename
        self.active_skills.append(skill_copy)
        return skill

    def deactivate(self, filename: str):
        """Deactivate a skill by filename."""
        self.active_skills = [
            s for s in self.active_skills if s.get("_filename") != filename
        ]

    def _parse_file(self, filepath: Path) -> Optional[Dict]:
        """
        Parse a single skill file.
        Extracts YAML frontmatter + Markdown sections.
        """
        content = filepath.read_text(encoding="utf-8")
        post = frontmatter.loads(content)

        # Extract frontmatter metadata
        skill = {
            "name": post.get("name", filepath.stem),
            "description": post.get("description", ""),
            "version": post.get("version", "1.0"),
            "triggers": post.get("triggers", []),
            "requires": post.get("requires", {}),
        }

        # Parse markdown body into sections
        body = post.content
        sections = self._parse_sections(body)

        # Map sections to skill structure
        skill["guardrails"] = self._extract_list(sections.get("guardrails", ""))
        skill["workflow"] = self._extract_list(sections.get("workflow", ""))
        skill["output_format"] = self._extract_list(sections.get("output format", ""))
        skill["examples"] = sections.get("examples", "").strip()
        skill["raw_body"] = body  # keep full body for direct injection if needed

        return skill

    def _parse_sections(self, body: str) -> Dict[str, str]:
        """Split markdown body by ## headers into named sections."""
        sections = {}
        current_section = ""
        current_content = []

        for line in body.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip().lower()
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_list(self, text: str) -> List[str]:
        """Extract bullet points or numbered items from text."""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                items.append(line[2:].strip())
            elif line and line[0].isdigit() and ". " in line:
                items.append(line.split(". ", 1)[1].strip())
        return items
