#!/usr/bin/env python3
"""
Unit tests for Antigravity CLI Syntax & Flag Compliance.
"""

import unittest
from pathlib import Path
import re
import shlex

SKILL_ROOT = Path(__file__).resolve().parent.parent

# Allowed flags supported by agy CLI v1.1.20
VALID_AGY_FLAGS = {
    "--add-dir",
    "--agent",
    "-c",
    "--continue",
    "--conversation",
    "--dangerously-skip-permissions",
    "--disable-slash-commands",
    "--effort",
    "-i",
    "--input-format",
    "--json-schema",
    "--log-file",
    "--mode",
    "--model",
    "--new-project",
    "--output-format",
    "-p",
    "--print",
    "--print-timeout",
    "--project",
    "--prompt",
    "--prompt-interactive",
    "--sandbox",
}

# Subcommands
VALID_SUBCOMMANDS = {
    "agent",
    "agents",
    "changelog",
    "help",
    "install",
    "mcp",
    "mic-serve",
    "models",
    "plugin",
    "plugins",
    "update",
    "version",
    "--version",
    "-v",
}

# Known deprecated or invalid flags
DISALLOWED_FLAGS = {
    "--cwd",
    "--accept-edits", # --accept-edits is a value for --mode accept-edits, not a flag
}


class TestCliSyntax(unittest.TestCase):
    """Test all agy commands mentioned in documentation and templates."""

    def extract_agy_commands(self, file_path: Path):
        """Extract lines or code blocks starting with 'agy '."""
        content = file_path.read_text(encoding="utf-8")
        commands = []
        
        # Match bash code blocks
        code_blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("agy "):
                    commands.append((file_path.name, line))
        
        return commands

    def test_no_disallowed_flags_in_docs_and_templates(self):
        """Assert no commands use disallowed flags like --cwd."""
        files_to_check = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "templates" / "commands.md",
        ]

        for file_path in files_to_check:
            self.assertTrue(file_path.exists(), f"{file_path} must exist.")
            content = file_path.read_text(encoding="utf-8")
            for flag in DISALLOWED_FLAGS:
                pattern = rf"\bagy\b[^\n]*\b{re.escape(flag)}\b"
                match = re.search(pattern, content)
                self.assertIsNone(
                    match,
                    f"Found disallowed flag '{flag}' in {file_path.name}: {match.group(0) if match else ''}"
                )

    def test_all_extracted_agy_commands_use_valid_flags(self):
        """Verify that all flags in extracted commands are in the allowed flag set."""
        files_to_check = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "templates" / "commands.md",
        ]

        all_commands = []
        for f in files_to_check:
            all_commands.extend(self.extract_agy_commands(f))

        self.assertTrue(len(all_commands) > 0, "Should have extracted at least one agy command.")

        for source_file, cmd_str in all_commands:
            # Handle multi-line commands or trailing quotes
            cleaned_cmd = cmd_str.replace("\\\n", " ").split("#")[0].strip()
            if not cleaned_cmd:
                continue

            try:
                tokens = shlex.split(cleaned_cmd)
            except ValueError:
                # If template contains placeholders like "<task description>", tokenise simply
                tokens = cleaned_cmd.split()

            self.assertEqual(tokens[0], "agy")
            for token in tokens[1:]:
                if token.startswith("-"):
                    # Check flag name before '=' if flag=value syntax used
                    flag_name = token.split("=")[0]
                    self.assertIn(
                        flag_name,
                        VALID_AGY_FLAGS.union(VALID_SUBCOMMANDS),
                        f"Unrecognized flag '{flag_name}' in command '{cleaned_cmd}' in {source_file}"
                    )


if __name__ == "__main__":
    unittest.main()
