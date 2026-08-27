# Anti-Gravity Development Command Templates

A collection of tested, valid `agy` command templates for autonomous agents and developer sessions across planning, implementation, and self-correction.

---

## Quick Reference

### 1. Planning Commands (Phase 1)
```bash
# Standard Plan
agy --mode plan -p "<task description>" --dangerously-skip-permissions --print-timeout 10m

# Deep Architectural Plan (High Effort)
agy --mode plan --effort high -p "<task description>" --dangerously-skip-permissions --print-timeout 25m

# Multi-Directory Workspace Plan
agy --mode plan --add-dir ./src --add-dir ./docs -p "<task description>" --dangerously-skip-permissions

# Structured JSON Schema Output
agy --mode plan -p "<task description>" \
  --output-format json \
  --json-schema '{
    "type": "object",
    "required": ["goal", "files_to_modify", "files_to_create", "steps", "risks"],
    "properties": {
      "goal": {"type": "string"},
      "files_to_modify": {"type": "array", "items": {"type": "string"}},
      "files_to_create": {"type": "array", "items": {"type": "string"}},
      "steps": {"type": "array", "items": {"type": "string"}},
      "risks": {"type": "array", "items": {"type": "string"}}
    }
  }' \
  --dangerously-skip-permissions
```

### 2. Implementation Commands (Phase 3 - Single Session Continuation)
```bash
# Implement All Planned Changes in Same Session
agy -c "Approved. Implement the plan we discussed." --mode accept-edits --dangerously-skip-permissions

# Implement Phase 1 Only (Step-by-Step)
agy -c "Approved. Implement Phase 1: Data models and database migrations." --mode accept-edits --dangerously-skip-permissions

# Implement Phase 2 (Continuing Same Session)
agy -c "Proceed to Phase 2: Core authentication services and JWT handling." --mode accept-edits --dangerously-skip-permissions
```

### 3. Self-Correction & Error Feedback Loops (Phase 5)
```bash
# Feed Test Trace Back to Fix Code
agy -c "Tests failed with:
[PASTE ERROR TRACE HERE]
Fix the implementation in [TARGET_FILE] and ensure tests pass." --mode accept-edits --dangerously-skip-permissions

# Fix Linter & Type Errors
agy -c "Run ruff / flake8 and fix all reported type and linting errors." --mode accept-edits --dangerously-skip-permissions
```

---

## Templates by Use Case

### 1. Feature Development: Full End-to-End Workflow

#### Step 1: Generate Plan
```bash
agy --mode plan -p "
Plan the implementation of [FEATURE_NAME]:

Requirements:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

Tech Stack:
- [Language / Framework]
- [Database / Cache]
- [Key Libraries]

Constraints:
- [Latency / Performance SLA]
- [Security requirements]

Include:
1. Files to create and modify
2. API contract definitions
3. Comprehensive verification plan (automated tests)
4. Risk assessment
" --dangerously-skip-permissions --print-timeout 15m > PLAN.md
```

#### Step 2: Validate Plan
```bash
python3 scripts/validate_plan.py PLAN.md
```

#### Step 3: Implement Code (Same Session)
```bash
agy -c "Approved. Implement the feature according to PLAN.md." \
    --mode accept-edits \
    --dangerously-skip-permissions
```

#### Step 4: Verify Tests
```bash
pytest tests/
```

---

### 2. Refactoring & Code Decoupling

```bash
# Step 1: Plan Refactor
agy --mode plan --effort high -p "
Analyze and plan the refactoring of [MODULE/COMPONENT]:

Current Bottlenecks:
- [Issue 1: High coupling]
- [Issue 2: Low test coverage]

Goals:
- [Goal 1: Decouple with clear interfaces]
- [Goal 2: Increase test coverage]

Constraints:
- Maintain full backwards compatibility
- Existing test suite must pass after each step
" --dangerously-skip-permissions --print-timeout 20m > REFACTOR_PLAN.md

# Step 2: Execute Refactor Step-by-Step
agy -c "Approved. Execute Step 1 of REFACTOR_PLAN.md: Extract interfaces." \
    --mode accept-edits \
    --dangerously-skip-permissions
```

---

### 3. Technology Migration (e.g. SQLite to PostgreSQL)

```bash
# Step 1: Plan Migration
agy --mode plan --effort high -p "
Plan migration from [OLD_TECH] to [NEW_TECH]:

Scope:
- Affected modules: [List directories]
- Data migration requirements: [Schemas/State]
- Dependency changes: [Libraries to replace]

Migration Strategy:
- Dual-write / adapter layer strategy
- Rollback procedures
- End-to-end benchmark & verification
" --dangerously-skip-permissions --print-timeout 30m

# Step 2: Implement Migration
agy -c "Implement the database adapter layer and migration scripts." \
    --mode accept-edits \
    --dangerously-skip-permissions
```

---

### 4. Bug Investigation & Remediation

```bash
# Step 1: Analyze & Plan Fix
agy --mode plan -p "
Investigate and plan fix for:

Symptom: [Observed behavior]
Expected: [Expected behavior]
Traceback:
[PASTE TRACEBACK]

Provide root cause analysis, target files to fix, and regression test cases.
" --dangerously-skip-permissions --print-timeout 10m

# Step 2: Apply Fix
agy -c "Apply the proposed fix and write regression tests." \
    --mode accept-edits \
    --dangerously-skip-permissions
```

---

## Autonomous Agent Integration (Python / Hermes)

```python
import subprocess
from typing import Optional

def execute_development_step(
    prompt: str,
    mode: str = "accept-edits",
    continue_session: bool = True,
    timeout: str = "15m",
    effort: Optional[str] = None,
) -> str:
    """Executes a development turn with agy preserving session context."""
    cmd = ["agy", "--mode", mode, "--dangerously-skip-permissions", "--print-timeout", timeout]
    
    if effort:
        cmd.extend(["--effort", effort])
        
    if continue_session:
        cmd.extend(["-c", prompt])
    else:
        cmd.extend(["-p", prompt])
        
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


# Example 1: Planning Turn (New Session)
plan_output = execute_development_step(
    prompt="Plan user registration and password hashing flow",
    mode="plan",
    continue_session=False,
    effort="high"
)
print("Plan Generated.")

# Example 2: Implementation Turn (Continuous Session)
code_output = execute_development_step(
    prompt="Approved. Implement Phase 1: User models and password hashing utility.",
    mode="accept-edits",
    continue_session=True
)
print("Code Implemented.")
```
