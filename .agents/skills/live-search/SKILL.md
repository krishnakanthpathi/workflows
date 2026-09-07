---
name: live-search
description: Fast, zero-token, zero-API-key live web search for retrieving real-time information, documentation, and verified links.
version: 1.0.0
author: Krishna Kanth
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [search, web, research, fast-search, zero-token, live-web, terminal]
    category: research
    related_skills: [grounded-citations, arxiv, research-paper-writing]
---

# Live Web Search Skill

A lightweight, zero-token, zero-API-key real-time web search tool built for terminal workflows and autonomous AI agents.

It queries the live web without running JavaScript, bypasses bot detection, extracts clean direct URLs (unwrapping tracker redirects), and returns exact page titles and verbatim snippets in under 300ms.

---

## When to Use

- **Real-Time Fact Retrieval**: Finding latest software versions, package changelogs, breaking news, contact numbers, or schedules.
- **Agent Web Research**: Providing autonomous agents with live search results using the `--json` output flag.
- **Zero-Cost Verification**: Fact-checking claims without consuming LLM tokens or API credits.
- **Quick Terminal Search**: Finding official documentation or download URLs without leaving the terminal.

---

## Quick Reference

| Task | Command |
| :--- | :--- |
| **Basic Search** | `python3 scripts/live_search.py "query"` or `live-search "query"` |
| **Custom Result Count** | `python3 scripts/live_search.py -n 8 "query"` |
| **Agent JSON Output** | `python3 scripts/live_search.py --json "query"` |
| **URLs & Titles Only** | `python3 scripts/live_search.py --sources-only "query"` |

---

## Usage Examples

### 1. Standard Live Search (Terminal Human Output)
```bash
python3 scripts/live_search.py "gas booking in india number for hp in ap"
```
**Output**:
```text
🔍 Searching live web for: 'gas booking in india number for hp in ap'...

=================================================================
🌐 LIVE SEARCH RESULTS (5 Found):
=================================================================
[1] HP Gas Refill Booking Options - Hindustan Petroleum Corporation Ltd.
    🔗 URL: https://www.hindustanpetroleum.com/pages/hp-gas-refill-booking-options
    📝 Dial from your registered mobile to IVRS 88888 23456. Missed Call: 94936 02222...

[2] HP Anywhere | Official Website of HPCL
    🔗 URL: https://www.hindustanpetroleum.com/pages/hp-anytime
    📝 HP Anytime 24x7 IVRS based refill booking system...
```

---

### 2. Machine-Readable JSON Mode (For Autonomous Subagents)
```bash
python3 scripts/live_search.py --json "Claude SDK overview"
```
**Output**:
```json
{
  "query": "Claude SDK overview",
  "total_results": 5,
  "results": [
    {
      "index": 1,
      "title": "Agent SDK overview - Claude Code Docs",
      "url": "https://code.claude.com/docs/en/agent-sdk/overview",
      "snippet": "The Agent SDK gives you the same tools, agent loop, and context management that power Claude Code..."
    }
  ]
}
```

---

### 3. Programmatic Python Import
You can also import and use the search function directly inside other Python scripts:

```python
from scripts.live_search import search_live_web

results = search_live_web("Python 3.13 changelog", max_results=5)
for r in results:
    print(f"[{r['index']}] {r['title']} -> {r['url']}")
    print(f"    {r['snippet']}\n")
```

---

## Key Features

1. **Zero Tokens / $0 Cost**: Completely free, unlimited queries.
2. **Zero Dependencies**: Uses only Python 3 standard libraries (`urllib`, `re`, `html`, `json`).
3. **Clean URLs**: Unwraps all redirect trackers (`uddg=`) to provide real destination links.
4. **Fast**: Average execution time under 0.3 seconds.
