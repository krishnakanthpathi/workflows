---
name: live-search
description: Fast, zero-token, zero-API-key live web search and deep page reader for real-time research, documentation, and verified sources.
version: 1.1.0
---

# Live Web Search & Reader

Zero-cost real-time web search and HTML-to-Markdown reader for autonomous agents and terminal workflows.

## Quick Reference

| Task | Command |
| :--- | :--- |
| **Live Search** | `python3 scripts/live_search.py "query"` |
| **Search + Deep Read Top N** | `python3 scripts/live_search.py --deep 2 "query"` |
| **Read Webpage to Markdown** | `python3 scripts/live_search.py --read "https://..."` |
| **Agent JSON Output** | `python3 scripts/live_search.py --deep 2 --json "query"` |
| **URLs & Titles Only** | `python3 scripts/live_search.py --sources-only "query"` |
| **Wikipedia Overview Only** | `python3 scripts/live_search.py --wiki-only "topic"` |
| **Custom Result Count** | `python3 scripts/live_search.py -n 8 "query"` |

---

## CLI Examples

```bash
# 1. Search with Wikipedia overview & web results
python3 scripts/live_search.py "nuclear fusion energy"

# 2. Extract full clean Markdown from any URL (untruncated by default)
python3 scripts/live_search.py --read "https://docs.python.org/3/whatsnew/3.13.html"

# 3. Search and extract full content from top 2 results
python3 scripts/live_search.py --deep 2 "DeepSeek V3 architecture"

# 4. JSON output for agent workflows
python3 scripts/live_search.py --deep 1 --json "quantum entanglement"
```

---
