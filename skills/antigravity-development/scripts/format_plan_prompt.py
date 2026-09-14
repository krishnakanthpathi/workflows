#!/usr/bin/env python3
"""
Prompt Formatter & CLI Command Builder for Antigravity Development.

Generates structured planning and execution prompts, and builds valid `agy` CLI commands.
"""

import argparse
import sys
import shlex
from typing import List, Optional


def build_plan_prompt(
    feature_name: str,
    requirements: Optional[List[str]] = None,
    tech_stack: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
) -> str:
    """Constructs a structured planning prompt."""
    lines = [f"Plan the implementation of {feature_name}:", ""]

    if requirements:
        lines.append("Requirements:")
        for req in requirements:
            lines.append(f"- {req}")
        lines.append("")

    if tech_stack:
        lines.append("Tech Stack & Dependencies:")
        for tech in tech_stack:
            lines.append(f"- {tech}")
        lines.append("")

    if constraints:
        lines.append("Constraints & Edge Cases:")
        for c in constraints:
            lines.append(f"- {c}")
        lines.append("")

    lines.append("Deliverables:")
    lines.append("1. Clear Goal and Executive Summary")
    lines.append("2. Files to create ([NEW]), modify ([MODIFY]), or delete ([DELETE])")
    lines.append("3. Verification plan with automated unit/integration tests and manual checks")
    lines.append("4. Phased execution breakdown with risk mitigations")

    return "\n".join(lines)


def build_execution_prompt(
    task_description: str,
    phase: Optional[str] = None,
    target_files: Optional[List[str]] = None,
    tests_to_run: Optional[List[str]] = None,
) -> str:
    """Constructs a structured implementation/execution prompt."""
    lines = []
    if phase:
        lines.append(f"Execute {phase}: {task_description}")
    else:
        lines.append(f"Implement: {task_description}")
    lines.append("")

    if target_files:
        lines.append("Target Files:")
        for f in target_files:
            lines.append(f"- {f}")
        lines.append("")

    if tests_to_run:
        lines.append("Verification Requirements:")
        for t in tests_to_run:
            lines.append(f"- Run: {t}")
        lines.append("")

    lines.append("Instructions:")
    lines.append("- Write clean, modular, production-ready code with complete type safety.")
    lines.append("- Follow the architectural design outlined in the approved plan.")
    lines.append("- Verify that all automated tests pass before concluding.")

    return "\n".join(lines)


def build_agy_command(
    prompt: str,
    mode: str = "plan",
    effort: Optional[str] = None,
    timeout: Optional[str] = None,
    model: Optional[str] = None,
    add_dirs: Optional[List[str]] = None,
    output_format: Optional[str] = None,
    auto_approve: bool = True,
    continue_session: bool = False,
    conversation_id: Optional[str] = None,
) -> List[str]:
    """
    Builds a compliant agy CLI command list.
    Ensures disallowed flags like --cwd are never used.
    """
    cmd = ["agy"]

    if mode:
        cmd.extend(["--mode", mode])

    if effort:
        cmd.extend(["--effort", effort])

    if timeout:
        cmd.extend(["--print-timeout", timeout])

    if model:
        cmd.extend(["--model", model])

    if add_dirs:
        for d in add_dirs:
            cmd.extend(["--add-dir", d])

    if output_format:
        cmd.extend(["--output-format", output_format])

    if conversation_id:
        cmd.extend(["--conversation", conversation_id])

    if auto_approve:
        cmd.append("--dangerously-skip-permissions")

    if continue_session:
        cmd.extend(["-c", prompt])
    else:
        cmd.extend(["-p", prompt])

    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured prompts and valid agy CLI commands for Antigravity Development."
    )
    parser.add_argument("feature_name", help="Name of the feature or task")
    parser.add_argument("-r", "--requirement", action="append", default=[], help="Feature requirements")
    parser.add_argument("-t", "--tech", action="append", default=[], help="Tech stack items")
    parser.add_argument("-c", "--constraint", action="append", default=[], help="Constraints & edge cases")
    parser.add_argument("--mode", choices=["plan", "accept-edits"], default="plan", help="Execution mode")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default="medium", help="Reasoning effort")
    parser.add_argument("--timeout", default="10m", help="Print timeout (e.g. 10m, 20m)")
    parser.add_argument("--model", help="Model override")
    parser.add_argument("--add-dir", action="append", default=[], help="Add directories to context")
    parser.add_argument("--continue-session", action="store_true", help="Continue previous session with -c")

    args = parser.parse_args()

    prompt = build_plan_prompt(
        feature_name=args.feature_name,
        requirements=args.requirement,
        tech_stack=args.tech,
        constraints=args.constraint,
    )

    cmd = build_agy_command(
        prompt=prompt,
        mode=args.mode,
        effort=args.effort,
        timeout=args.timeout,
        model=args.model,
        add_dirs=args.add_dir,
        continue_session=args.continue_session,
    )

    print("📝 Generated Prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    print("\n⚡ Generated CLI Command:")
    print(" ".join(shlex.quote(arg) for arg in cmd))


if __name__ == "__main__":
    main()
