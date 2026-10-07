---
name: obsidian
description: Read, search, create, and edit notes, documentation, and knowledge bases in the Obsidian vault adhering strictly to vault writing rules and standards.
version: 2.0.0
author: Krishna Kanth
license: MIT
platforms: [macos, linux, windows]
metadata:
  tags: [obsidian, notes, markdown, vault, knowledge-base, wikilinks, standards, rules]
---

# 📜 Obsidian Vault Management & Writing Standards (v2.0)

Use this skill for all filesystem-first Obsidian vault workflows: reading notes, discovering notes, searching note contents, creating structured markdown notes, editing existing notes, and maintaining wikilinks.

> [!IMPORTANT] Core Directive for AI Agents
> Any agent, LLM, or automated script generating, updating, or modifying notes in the Obsidian vault **MUST** strictly adhere to the guidelines and standards defined in this skill.

---

## 1. Vault Location & Path Resolution

* **Master Vault Path**: `/Users/krishnakanth/Documents/Obsidian Vault`
* **Path Resolution**: Always resolve paths to absolute paths before calling filesystem tools.
* **Spaces in Names**: Vault folders and file names frequently contain spaces (e.g., `Obsidian Vault`, `Daily/`, `Key Projects Portfolio.md`). Ensure strings and command arguments handle spaces safely.

---

## 2. Core Operational Toolchain

* **Read a Note**: Use `view_file` with the exact absolute path to the `.md` file.
* **List Notes & Discover Structure**: Use `list_dir` or `find_by_name` (pattern: `*.md`) within the vault or specific subdirectories (`Projects/`, `Notes/`, `Daily/`, etc.).
* **Search Content & Tags**: Use `grep_search` to find text snippets, tags (`#tag`), headings, or specific wikilinks (`[[...]]`) across the vault.
* **Create a Note**: Use `write_to_file` (or `call_mcp_tool fs_write`) with full, validated markdown content and complete YAML frontmatter.
* **Edit / Patch a Note**: Use `replace_file_content` for precise block edits, status updates, or appending sections.

---

## 3. Folder Organization Matrix

Every note in the vault must be placed in its designated directory based on type and intent:

| Folder | Purpose & Note Types | Example Files |
| :--- | :--- | :--- |
| **`Development/`** | Technical guides, terminal setups, API bridges, software architectures, coding rules | `Development/rules.md`, `Termux Android Setup.md` |
| **`Projects/`** | Active & completed project specs, system designs, portfolios, automation pipelines | `Key Projects Portfolio.md`, `VidyaSetu AI.md` |
| **`Research/`** | Deep dives, technical comparisons, benchmarks, paper summaries, AI evaluations | `Best TTS Models for Mac.md` |
| **`Notes/`** | General knowledge base, concepts, system administration, quick guides | `AI Models Configuration.md`, `Home Lab Setup.md` |
| **`Daily/`** | Daily briefing logs, chronological logs, automated reports (`YYYY-MM-DD.md`) | `Daily/2026-09-12.md` |
| **`Learning/`** | Study notes, courses, tutorials, roadmaps, skill trees | `AWS SAA-C03 Roadmap.md`, `System Design Learning Path.md` |
| **`Career/` & `Personal/`** | Career plans, achievements, personal tracking, certifications | `LeetCode Profile.md`, `Certifications & Leadership.md` |
| **`Todos/`** | Action lists, backlogs, master project roadmaps, sprint planning | `Todos/Todos.md`, `Todos/technical-to-do.md` |
| **`Ideas/`** | Conceptual drafts, exploratory designs, prospective features | `Ideas/TermuxAura.md` |
| **`Creative/`** | Creative writing, brainstorming, non-technical thoughts | `Creative/Brainstorm.md` |

---

## 4. Note Structure & Mandatory Frontmatter

Every note created or maintained in the vault must begin with standard YAML frontmatter:

```yaml
---
title: "Descriptive Note Title"
date: YYYY-MM-DD
tags:
  - primary-topic
  - secondary-topic
  - sub-category
status: completed # [in-progress | completed | reference | draft]
---
```

### Standard Section Hierarchy
1. **Title (# Header):** Clean, recognizable title with relevant emoji icon.
2. **Executive Summary Callout:** Quick 2–3 line summary (`> [!abstract] Executive Summary`).
3. **Core Content / Architecture:** Mermaid diagram (if architectural) + structured subheadings.
4. **Problems & Fixes (if technical):** Structured as *Symptom → Root Cause → Resolution*.
5. **Master Command / Code Reference:** Fenced copyable blocks.
6. **Related Notes Footer:** Wikilinks linking to contextually relevant notes in the vault.

---

## 5. Obsidian Syntax & Linking Standards

### Wikilinks (MANDATORY)
* Connect related notes using double square brackets:
  * `[[Note Name]]` — Links directly to `Note Name.md`
  * `[[Note Name|Custom Label]]` — Links to `Note Name.md` with display alias `Custom Label`
  * `[[Folder/Note Name|Custom Label]]` — Explicit path link when disambiguation is required
* **Rule:** Never use broken web paths or markdown relative links (`./file.md`) for internal notes. Always use `[[Wikilinks]]`.

### Callout Standards
Use standard Obsidian / GitHub callouts for emphasis:
* `> [!abstract]` — Executive summaries and high-level overviews
* `> [!info]` — General background context
* `> [!tip]` — Best practices, performance shortcuts, tips
* `> [!note]` — Important context and operational notes
* `> [!important]` — Must-know requirements and core rules
* `> [!warning]` — Known caveats, common traps, breaking changes
* `> [!danger]` — High-risk commands (data loss, hardware risk, reset)

---

## 6. Copyability & Code Block Rules

> [!TIP] Obsidian 1-Click Copy Rule
> **Every runnable command and code snippet must be placed in a dedicated, syntax-highlighted code block.**
> Avoid placing runnable commands inside markdown tables where the Obsidian copy button cannot copy them cleanly.

* **Format:**
  1. Short, 1-line bold description above the block.
  2. Dedicated fenced code block with correct language tag (`bash`, `python`, `json`, `yaml`, `javascript`, `typescript`, etc.).

**Example:**
* **Run production server with Uvicorn:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 7. To-Do List & Task Management Standards (MANDATORY)

> [!IMPORTANT] Interactive Checklist & Date Linking Standard
> Whenever creating or updating to-do lists in `Todos/`, `Daily/`, or project notes:

1. **Interactive Checklist Format (Strike-out Ready):**
   * Every to-do item **MUST** be an interactive markdown checkbox:
     * `- [ ]` for pending or scheduled tasks.
     * `- [x]` or `- [x] ~~Task~~` for completed tasks so the user can easily strike them out or check them off in Obsidian.
   * Never use plain text bullets (`*` without brackets) for action items.
2. **Mandatory Explicit Date on Every Item:**
   * Every single to-do item **MUST** explicitly state its date:
     * `📅 YYYY-MM-DD` for scheduled/upcoming tasks (e.g., `📅 2026-09-15`).
     * `✅ YYYY-MM-DD` for completed tasks (e.g., `✅ 2026-09-12`).
3. **Contextual Note Linking (Bi-directional):**
   * Every to-do item or category must link to its dedicated documentation or project note in the vault (e.g., `[[Notes/Home Lab Setup|Home Lab]]`, `[[Projects/VidyaSetu AI|VidyaSetu]]`, `[[Learning/AWS SAA-C03 Roadmap|AWS SAA-C03]]`).
   * Detailed technical checklists must reside in `Notes/` or `Projects/` and be linked from `Todos/Todos.md` and daily notes.

### Compliant To-Do Example
```markdown
### 📱 Edge Gateway & Hardware Infrastructure
- [x] Configure Termux with SSH on port `8022` ✅ 2026-09-10
- [x] Bridge `Termux:API` companion app with hardware permissions ✅ 2026-09-11
- [ ] Install `llama.cpp` ARM64 for offline local SLM inference 📅 2026-09-15
- [ ] [[Notes/Home Lab Setup|Home Lab]]: Verify Tailscale mesh exit node 📅 2026-09-16
```

---

## 8. Technical Troubleshooting Standard

When documenting technical problems or debugging sessions, always follow this 3-part format:

```markdown
### [Issue Title]
* **Symptom:** Exact error message or observable behavior.
* **Root Cause:** Deep technical explanation of why it occurred.
* **Resolution:** Exact command or steps that resolved the issue.
```

---

## 9. Artifact Generation, Finder Reveal & Multi-Device Standards

1. **Automatic Finder Reveal for File Artifacts:**
   * Whenever creating standalone documents, exported PDFs, charts, canvas files, or media assets, AI agents **MUST** automatically reveal the file in macOS Finder using system MCP tools (`call_mcp_tool native-assistant-mcp reveal_in_finder`) and output the clickable direct file link (`file:///...`).
2. **Dedicated Scratch & Download Scoping:**
   * When handling external media, scraped content, or temporary downloads, output must be constrained to `<SKILL_DIR>/downloads/` or `dist/` subdirectories to prevent vault clutter.
3. **Master Vault Authority:**
   * The local macOS vault at `/Users/krishnakanth/Documents/Obsidian Vault` is the single source of truth. Secondary headless machines (e.g. remote servers) must not run unmonitored git auto-merge cron jobs that risk corrupting vault HEAD.

---

## 10. Pre-Flight Quality Checklist for AI Agents

Before concluding any note creation or edit in the Obsidian vault, verify:
- [ ] Valid YAML frontmatter included with title, date, tags, and status.
- [ ] Executive summary callout present at the top (`> [!abstract]`).
- [ ] High signal-to-noise ratio: concise, direct, zero fluff.
- [ ] All terminal commands placed in dedicated copyable fenced code blocks.
- [ ] All to-dos use interactive checkboxes (`- [ ]` / `- [x]`) with explicit dates (`📅 YYYY-MM-DD` / `✅ YYYY-MM-DD`).
- [ ] Contextual wikilinks (`[[Note Name]]`) used for note-to-note navigation.
- [ ] Auto-reveal generated file artifacts in macOS Finder and output clickable file link.
- [ ] Mermaid diagrams used for workflows and architectures where applicable.
- [ ] Target file placed in the correct vault folder matching the Folder Organization Matrix.
