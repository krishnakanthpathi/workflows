#!/usr/bin/env python3
"""
Unit tests for Antigravity Development Skill Metadata & Frontmatter.
"""

import unittest
from pathlib import Path
import re

try:
    import yaml
except ImportError:
    yaml = None


SKILL_ROOT = Path(__file__).resolve().parent.parent


class TestSkillMetadata(unittest.TestCase):
    """Test SKILL.md metadata, frontmatter, and file references."""

    def setUp(self):
        self.skill_md_path = SKILL_ROOT / "SKILL.md"
        self.assertTrue(self.skill_md_path.exists(), "SKILL.md must exist in root.")
        self.skill_content = self.skill_md_path.read_text(encoding="utf-8")

    def test_yaml_frontmatter_exists_and_parses(self):
        """Ensure frontmatter is valid YAML and has required fields."""
        match = re.match(r"^---\n(.*?)\n---", self.skill_content, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must contain valid YAML frontmatter between '---' delimiters.")
        
        frontmatter_text = match.group(1)
        if yaml:
            meta = yaml.safe_load(frontmatter_text)
            self.assertIsInstance(meta, dict, "Frontmatter must parse to a dictionary.")
            self.assertIn("name", meta, "Frontmatter must include 'name'.")
            self.assertEqual(meta["name"], "antigravity-development")
            self.assertIn("description", meta, "Frontmatter must include 'description'.")
            self.assertTrue(len(meta["description"]) > 20, "Description should be sufficiently descriptive.")
            self.assertIn("version", meta, "Frontmatter must include 'version'.")

    def test_directory_structure_exists(self):
        """Ensure expected subdirectories exist."""
        references_dir = SKILL_ROOT / "references"
        templates_dir = SKILL_ROOT / "templates"
        scripts_dir = SKILL_ROOT / "scripts"
        tests_dir = SKILL_ROOT / "tests"

        self.assertTrue(references_dir.is_dir(), "references/ directory must exist.")
        self.assertTrue(templates_dir.is_dir(), "templates/ directory must exist.")
        self.assertTrue(scripts_dir.is_dir(), "scripts/ directory must exist.")
        self.assertTrue(tests_dir.is_dir(), "tests/ directory must exist.")

    def test_markdown_links_resolve(self):
        """Ensure all relative markdown links in SKILL.md point to real files."""
        # Find markdown links: [text](./relative/path) or [text](relative/path)
        links = re.findall(r"\[.*?\]\(((?:\./|\w)[^)]+)\)", self.skill_content)
        for link in links:
            # Strip anchors if any
            clean_link = link.split("#")[0].strip()
            if not clean_link or clean_link.startswith("http"):
                continue
            target_path = (SKILL_ROOT / clean_link).resolve()
            self.assertTrue(
                target_path.exists(),
                f"Broken markdown link in SKILL.md: '{link}' -> '{target_path}'"
            )


if __name__ == "__main__":
    unittest.main()
