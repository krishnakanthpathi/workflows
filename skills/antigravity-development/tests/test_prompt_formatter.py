#!/usr/bin/env python3
"""
Unit tests for Prompt Formatter & Command Builder Script.
"""

import unittest
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from format_plan_prompt import build_plan_prompt, build_execution_prompt, build_agy_command


class TestPromptFormatter(unittest.TestCase):
    """Test format_plan_prompt logic and command builder."""

    def test_build_plan_prompt_structure(self):
        """Ensure generated prompt contains all provided sections."""
        prompt = build_plan_prompt(
            feature_name="OAuth2 Authentication",
            requirements=["Google SSO", "GitHub SSO", "JWT Callback"],
            tech_stack=["FastAPI", "Redis", "Authlib"],
            constraints=["Sub-50ms response", "Zero plaintext secret storage"]
        )

        self.assertIn("Plan the implementation of OAuth2 Authentication", prompt)
        self.assertIn("Requirements:", prompt)
        self.assertIn("Google SSO", prompt)
        self.assertIn("Tech Stack & Dependencies:", prompt)
        self.assertIn("FastAPI", prompt)
        self.assertIn("Constraints & Edge Cases:", prompt)
        self.assertIn("Zero plaintext secret storage", prompt)
        self.assertIn("Verification plan", prompt)

    def test_build_execution_prompt_structure(self):
        """Ensure generated execution prompt contains files and test requirements."""
        prompt = build_execution_prompt(
            task_description="Implement JWT issuance and claims validation",
            phase="Phase 1",
            target_files=["src/auth/jwt.py", "tests/test_jwt.py"],
            tests_to_run=["pytest tests/test_jwt.py -v"]
        )

        self.assertIn("Execute Phase 1: Implement JWT issuance", prompt)
        self.assertIn("Target Files:", prompt)
        self.assertIn("src/auth/jwt.py", prompt)
        self.assertIn("Verification Requirements:", prompt)
        self.assertIn("pytest tests/test_jwt.py -v", prompt)

    def test_build_agy_command_flags(self):
        """Ensure command list contains required flags and avoids disallowed flags."""
        cmd = build_agy_command(
            prompt="Plan user billing flow",
            effort="high",
            timeout="20m",
            model="Gemini 3.7 Flash",
            add_dirs=["./src", "./tests"],
            output_format="json",
            auto_approve=True,
        )

        self.assertEqual(cmd[0], "agy")
        self.assertIn("--mode", cmd)
        self.assertEqual(cmd[cmd.index("--mode") + 1], "plan")
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertIn("--effort", cmd)
        self.assertEqual(cmd[cmd.index("--effort") + 1], "high")
        self.assertIn("--print-timeout", cmd)
        self.assertEqual(cmd[cmd.index("--print-timeout") + 1], "20m")
        self.assertIn("--model", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "Gemini 3.7 Flash")
        self.assertIn("--output-format", cmd)
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "json")
        self.assertIn("-p", cmd)
        self.assertEqual(cmd[cmd.index("-p") + 1], "Plan user billing flow")

        # Explicitly check that --cwd is NOT present
        self.assertNotIn("--cwd", cmd)

    def test_build_agy_execution_command_with_session_continuation(self):
        """Ensure continue_session creates command using -c instead of -p."""
        cmd = build_agy_command(
            prompt="Approved. Implement Phase 1 from the plan.",
            mode="accept-edits",
            continue_session=True,
            conversation_id="conv-12345",
            auto_approve=True
        )

        self.assertEqual(cmd[0], "agy")
        self.assertIn("--mode", cmd)
        self.assertEqual(cmd[cmd.index("--mode") + 1], "accept-edits")
        self.assertIn("--conversation", cmd)
        self.assertEqual(cmd[cmd.index("--conversation") + 1], "conv-12345")
        self.assertIn("-c", cmd)
        self.assertEqual(cmd[cmd.index("-c") + 1], "Approved. Implement Phase 1 from the plan.")
        self.assertNotIn("-p", cmd)


if __name__ == "__main__":
    unittest.main()
