# Custom Workflow Skills

This directory is set up for creating and managing custom skills and workflows.

## Skill Structure

```text
skills/<skill_name>/
├── SKILL.md          # Required: Main instruction file with YAML frontmatter
├── scripts/          # Optional: Helper scripts and utilities
├── examples/         # Optional: Reference implementations
├── resources/        # Optional: Additional assets or templates
└── references/       # Optional: Detailed documentation or manuals
```

### Example `SKILL.md`

```markdown
---
name: my-custom-skill
description: >-
  Describe what the skill does and when the agent should use it.
---

# My Custom Skill

Step-by-step instructions and runbooks for the agent.
```
