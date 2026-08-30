---
name: obsidian
description: Read, search, create, and edit notes, documentation, and knowledge bases in the Obsidian vault.
version: 1.0.0
author: Krishna Kanth
license: MIT
platforms: [macos, linux, windows]
metadata:
  tags: [obsidian, notes, markdown, vault, knowledge-base, wikilinks]
---

# Obsidian Vault Management

Use this skill for filesystem-first Obsidian vault workflows: reading notes, discovering notes, searching note contents, creating structured markdown notes, editing existing notes, and maintaining wikilinks.

---

## 1. Vault Path

* **Default Vault Path**: `/Users/krishnakanth/Documents/Obsidian Vault`
* Always resolve paths to absolute paths before calling file operations. Note that folder and file names inside the vault often contain spaces (e.g. `Obsidian Vault`, `Daily Notes`, `Key Projects Portfolio.md`).

---

## 2. Reading & Searching Notes

* **Read a Note**: Use `view_file` with the exact absolute path to the `.md` file.
* **List Notes & Structure**: Use `list_dir` or `find_by_name` (pattern: `*.md`) within the vault path or subdirectories (`Projects/`, `Notes/`, `Daily Summaries/`, etc.).
* **Content Search**: Use `grep_search` to find text, tags (`#tag`), headings, or specific wikilinks across the vault.

---

## 3. Creating & Updating Notes

* **Create a Note**: Use `write_to_file` (or script execution) with the full markdown content.
* **Edit / Patch a Note**: Use `replace_file_content` for targeted block edits or additions.

---

## 4. Obsidian Syntax & Conventions

### Wikilinks
Obsidian connects notes using double square brackets:
* `[[Note Name]]` — Links to `Note Name.md`
* `[[Note Name|Custom Label]]` — Links to `Note Name.md` with display alias `Custom Label`

### Callouts
Use GitHub / Obsidian standard callouts for structured emphasis:
* `> [!abstract] Executive Summary`
* `> [!info] Overview`
* `> [!tip] Best Practices`
* `> [!note] Important Context`
* `> [!warning] Caution / Risk`

### Tags & Frontmatter
Include tags in markdown body (e.g. `#automation #projects #research`) or YAML frontmatter:
```yaml
---
tags:
  - automation
  - projects
  - research
date: 2026-08-30
---
```
