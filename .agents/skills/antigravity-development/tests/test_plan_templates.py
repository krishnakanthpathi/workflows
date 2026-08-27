#!/usr/bin/env python3
"""
Unit tests for Plan Templates & Validator Script.
"""

import unittest
from pathlib import Path
import json
import sys

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

# pyrefly: ignore [missing-import]
from validate_plan import validate_plan_content, validate_plan_file
    

class TestPlanTemplates(unittest.TestCase):
    """Test plan template structure and validation logic."""

    def test_example_plan_passes_validation(self):
        """Ensure references/example-plan.md passes full validation."""
        example_plan_path = SKILL_ROOT / "references" / "example-plan.md"
        self.assertTrue(example_plan_path.exists(), "references/example-plan.md must exist.")

        is_valid, errors, warnings = validate_plan_file(example_plan_path)
        self.assertTrue(is_valid, f"example-plan.md failed validation with errors: {errors}")
        self.assertEqual(len(errors), 0, f"Expected 0 errors, got: {errors}")

    def test_validate_plan_detects_missing_sections(self):
        """Ensure validator flags incomplete plans."""
        incomplete_plan = """
# Implementation Plan: Incomplete Feature

## Goal
Do something quick.
"""
        is_valid, errors, warnings = validate_plan_content(incomplete_plan)
        self.assertFalse(is_valid, "Incomplete plan should not pass validation.")
        self.assertTrue(any("Proposed Changes" in err for err in errors))
        self.assertTrue(any("Testing Strategy" in err for err in errors))

    def test_validate_plan_empty_content(self):
        """Ensure validator handles empty plan content gracefully."""
        is_valid, errors, warnings = validate_plan_content("")
        self.assertFalse(is_valid)
        self.assertIn("Plan content is empty.", errors)

    def test_json_schema_in_commands_is_valid_json(self):
        """Ensure all JSON schema snippets in commands.md are valid JSON schemas."""
        commands_md = (SKILL_ROOT / "templates" / "commands.md").read_text(encoding="utf-8")
        
        # Extract --json-schema '{ ... }'
        import re
        schema_matches = re.findall(r"--json-schema\s+'(\{.*?\})'", commands_md, re.DOTALL)
        self.assertTrue(len(schema_matches) > 0, "commands.md should contain at least one json schema example.")
        
        for schema_str in schema_matches:
            parsed = json.loads(schema_str)
            self.assertIsInstance(parsed, dict)
            self.assertEqual(parsed.get("type"), "object")
            self.assertIn("properties", parsed)


if __name__ == "__main__":
    unittest.main()
