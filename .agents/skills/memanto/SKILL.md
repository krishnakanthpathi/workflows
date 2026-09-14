---
name: memanto
description: Store, recall, and manage long-term agent memory across sessions using the Memanto CLI connected to our shared on-prem Moorcheh backend.
---

# Memanto Memory Skill

Memanto acts as an active companion memory agent. It automatically reconciles conflicts, expires stale information, and shares durable knowledge across sessions and agents.

---

## 1. Quick Reference Commands

```bash
# Store a new memory
memanto remember "<content>" --type <type> --confidence <0.6-1.0> --provenance <provenance> --tags "<tag1,tag2>"

# Search / recall memories before complex tasks
memanto recall "<search query>" --limit 5

# Ask a direct grounded question synthesized from memory
memanto answer "<question>"

# Resolve memory conflicts
memanto conflicts

# View estate dashboard
memanto status
```

---

## 2. When to Remember (Memory Types Matrix)

Always persist meaningful, durable insights—never log chat narratives or ephemeral activity.

| Type | When to Use | Default Confidence | Example |
|---|---|---|---|
| `decision` | Architectural choices, library/tool selections, API designs | 0.95 - 1.0 | "Use port 8180 for Moorcheh Docker container on host hp." |
| `instruction` | Standing constraints, user guidelines, project rules | 1.0 | "Always summarize intent before modifying files (persona skill)." |
| `preference` | User preferences, preferred models, style choices | 0.85 - 1.0 | "Use Ollama nomic-embed-text for embeddings and gemma4:31b-cloud for LLM." |
| `learning` | Workarounds, discovered bug fixes, post-error insights | 0.9 - 1.0 | "Host Ollama in Docker requires host.docker.internal:11434." |
| `fact` | Verified technical facts, environment details, ports, IPs | 0.9 - 1.0 | "SSH host hp is located at 100.75.149.115 on Tailscale." |
| `commitment` | Deliverables agreed upon, ongoing milestones | 1.0 | "Deploy Memanto skill to Hermes on hp and Antigravity locally." |

---

## 3. Provenance Standards

Every memory must have an accurate `--provenance`:
- `explicit_statement`: User explicitly stated this rule, fact, or preference.
- `inferred`: Deduced logically from code structure or user actions.
- `observed`: Witnessed directly during test execution, CLI outputs, or logs.
- `corrected`: Formulated after correcting a previous error or user feedback.
- `validated`: Verified against documentation or source code.

---

## 4. Standard Workflows

### Task Start / Context Briefing
Before embarking on multi-step implementations or architectural choices:
```bash
memanto recall "<relevant topic or component>" --limit 5
```

### User Decision / Constraint Set
Whenever the user sets a standing constraint or design rule:
```bash
memanto remember "<rule or decision>" --type decision --tags "<tag1,tag2>" --confidence 1.0 --provenance explicit_statement
```

### Learning from Errors
After diagnosing and solving a tricky problem:
```bash
memanto remember "<root cause and solution>" --type learning --tags "<tag1,tag2>" --confidence 0.95 --provenance corrected
```
