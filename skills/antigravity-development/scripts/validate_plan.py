#!/usr/bin/env python3
"""
Plan Validator Script for Antigravity Development.

Validates implementation plans against quality and completeness guidelines.
Checks for required sections: Goal, Proposed Changes, Testing Strategy / Verification Plan, and Risks.
"""

import sys
import re
from pathlib import Path
from typing import Tuple, List

REQUIRED_SECTIONS = [
    ("Goal", [r"#+\s*(?:Goal|Executive Summary|Objective)"]),
    ("Proposed Changes", [r"#+\s*(?:Proposed Changes|Files to Modify|File Changes|Implementation Details)"]),
    ("Testing Strategy", [r"#+\s*(?:Testing Strategy|Verification Plan|Automated Tests|Testing)"]),
]

RECOMMENDED_SECTIONS = [
    ("Risks", [r"#+\s*(?:Risks|Risk Assessment|Mitigation|Edge Cases)"]),
    ("Phases", [r"#+\s*(?:Phases|Execution Phases|Implementation Steps|Tasks)"]),
]


def validate_plan_content(content: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validates markdown plan content.

    Returns:
        (is_valid, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not content or not content.strip():
        return False, ["Plan content is empty."], []

    # Check required sections
    for section_name, patterns in REQUIRED_SECTIONS:
        found = False
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break
        if not found:
            errors.append(f"Missing required section: '{section_name}'.")

    # Check recommended sections
    for section_name, patterns in RECOMMENDED_SECTIONS:
        found = False
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break
        if not found:
            warnings.append(f"Recommended section missing: '{section_name}'.")

    # Check for file demarcation markers if Proposed Changes exists
    if any("Proposed Changes" in err for err in errors):
        pass
    else:
        file_markers = re.findall(r"\[(NEW|MODIFY|DELETE)\]", content, re.IGNORECASE)
        backtick_files = re.findall(r"`(?:src|app|tests|lib|pkg|cmd|internal|components)/[^`]+`", content)
        if not file_markers and not backtick_files:
            warnings.append("No explicit file demarcation tags found (e.g., [NEW], [MODIFY], [DELETE]).")

    # Check minimum length
    if len(content.strip().splitlines()) < 10:
        errors.append("Plan is too brief (less than 10 lines of content).")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_plan_file(file_path: Path | str) -> Tuple[bool, List[str], List[str]]:
    """
    Validates a plan markdown file from disk.
    """
    path = Path(file_path)
    if not path.exists():
        return False, [f"File not found: {path}"], []

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"Error reading file '{path}': {e}"], []

    return validate_plan_content(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_plan.py <path_to_plan.md>")
        sys.exit(1)

    target_file = Path(sys.argv[1])
    is_valid, errors, warnings = validate_plan_file(target_file)

    print(f"🔍 Validating plan: {target_file.name}")
    print("=" * 50)

    if warnings:
        print(f"⚠️  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"❌ Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print()
        print("❌ Result: FAILED")
        sys.exit(1)

    print("✅ Result: PASSED (Plan is structurally complete and ready for execution)")
    sys.exit(0)


if __name__ == "__main__":
    main()
