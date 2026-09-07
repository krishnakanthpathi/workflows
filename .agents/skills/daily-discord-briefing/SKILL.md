---
name: daily-discord-briefing
description: Automated daily executive briefing pipeline. Delivers real-time market pulse (Nifty, Sensex, S&P 500, Nasdaq, Gold, USD/INR), hyper-local weather, dynamic stock market roadmap progression with auto-generated sub-notes, backlog recommendations from Todos hub, Anti-Gravity (agy) native news synthesis, high-efficiency AAC Tara voice audio, 4K anime wallpaper (Death Note, HxH, Vinland Saga, Bleach), Obsidian vault rules compliance, and Discord thread delivery.
version: 2.0.0
author: Krishna Kanth
license: MIT
---

# 🌅 Daily Executive Briefing, Stock Market Masterclass & Life Operations Skill (v2.0)

An end-to-end automated executive intelligence and life operations pipeline powered by Google Anti-Gravity (`agy`), live zero-cost financial APIs, Obsidian Vault knowledge graph, and Discord thread orchestration.

---

## ⚡ Key Capabilities (v2.0)

1. **Dynamic Stock Market Roadmap Progression & Study Note Generation**:
   * Inspects `Learning/Stock Market & Trading Mastery Roadmap.md` for completed items (`- [x]`) and extracts the next active curriculum milestone (`- [ ]`).
   * Automatically creates a dedicated, high-signal, zero-jargon study sub-note in `/Learning/Day XX - [Title].md` strictly compliant with `rules.md` (YAML frontmatter, everyday analogies, jargon buster table, and golden rules).
   * Ticks off the completed milestone in the master roadmap with verified timestamp (`- [x] [[Learning/...]] ✅ YYYY-MM-DD`).

2. **Todos Hub & Project Backlog Recommendation Engine**:
   * Scans `/Todos/*.md` across active projects (VidyaSetu AI, Android Edge Sentinel, Obsidian Semantizer, System Design).
   * Generates actionable daily recommendations and strategic focus items directly embedded in today's daily note and Discord briefing.

3. **Live Zero-Token Market Pulse**:
   * Live snapshot of Indian indices (**NIFTY 50**, **SENSEX**), US indices (**S&P 500**, **NASDAQ**), Commodities (**GOLD**), and Forex (**USD/INR**) via Yahoo Finance chart endpoints.
   * Formats into visual sentiment tickers (`🟢 Bullish`, `🔴 Bearish`) and Markdown tables.

4. **Hyper-Local Weather Intelligence**:
   * Fetches live conditions (temperature, humidity, wind speed, precipitation) for Annavaram via `wttr.in`.

5. **Anti-Gravity (`agy`) Native Breakthrough Synthesis**:
   * Native agentic research via `agy` CLI using its built-in toolchain and sandboxed execution to curate the top 5 AI, compute, and science breakthroughs with verified clickable source links.

6. **High-Efficiency Compressed Audio (Tara `en-IN` + FFmpeg AAC)**:
   * Generates natural spoken briefings with macOS native `say -v Tara`.
   * Compresses audio using FFmpeg (`-c:a aac -b:a 128k`) with ID3 track metadata (Artist: Armin Intelligence Agent, Album: Executive Daily Briefings), achieving a **71% file size reduction** (sub-800 KB) for instant streaming.

7. **Curated 4K Anime Desktop Wallpaper**:
   * Fetches 16:9 / 16:10 wallpapers via Wallhaven API with an expanded series pool:
     * *Death Note*, *Hunter x Hunter*, *Vinland Saga*, *Bleach*, *Attack on Titan*, *Jujutsu Kaisen*, *Demon Slayer*, *Solo Leveling*, *Naruto*.

8. **Obsidian Vault & Discord Thread Synchronization**:
   * Creates `/Daily/YYYY-MM-DD.md` with strict YAML frontmatter, morning overview callout, timetable, and workout routine adhering to `/rules.md`.
   * Delivers single-payload report (formatted card + clickable links + playable AAC audio + 4K wallpaper) to dedicated Discord thread.

---

## 🛠️ CLI Reference & Flags

| Action | Command |
| :--- | :--- |
| **Run Full Production Pipeline** | `python3 scripts/daily_briefing.py` |
| **Dry Run (Zero Disk/Network Side-Effects)** | `python3 scripts/daily_briefing.py --dry-run` |
| **Skip Voice Audio Synthesis** | `python3 scripts/daily_briefing.py --no-audio` |
| **Skip Anime Wallpaper Download** | `python3 scripts/daily_briefing.py --no-wallpaper` |
| **Test Discord Delivery Only** | `python3 scripts/daily_briefing.py --test-discord` |
| **Test Market Pulse Fetcher** | `python3 scripts/market_pulse.py` |
| **Test Weather Fetcher** | `python3 scripts/weather_service.py` |
| **Test Roadmap Manager** | `python3 scripts/roadmap_manager.py` |
| **Test Todos Analyzer** | `python3 scripts/todo_analyzer.py` |

---

## 🏗️ Architecture & Modules

```text
daily-discord-briefing/
├── SKILL.md                 # Documentation and operational manual
└── scripts/
    ├── daily_briefing.py        # Master pipeline orchestrator & Discord delivery
    ├── daily_briefing_prompt.md # Headless prompt configuration for agy CLI
    ├── market_pulse.py          # Zero-key live quotes (Nifty, Sensex, S&P, Nasdaq, Gold, USD/INR)
    ├── weather_service.py       # Zero-key weather integration for Annavaram
    ├── roadmap_manager.py       # Learning roadmap reader, sub-note creator & tick manager
    └── todo_analyzer.py         # Todos hub scanner & strategic recommendations engine
```

---

## ⏰ Automated Scheduling

### macOS `launchd` Service (System Level)
Runs every morning at 08:00 AM:
* **Plist Path**: `~/Library/LaunchAgents/com.armin.dailybriefing.plist`
* **Target Script**: `/Users/krishnakanth/Projects/armin/cron/daily-briefing/daily_briefing.py`

### Antigravity Daemon Scheduler
```text
CronExpression: "0 8 * * *"
IsDaemon: true
Prompt: "python3 /Users/krishnakanth/.gemini/config/skills/daily-discord-briefing/scripts/daily_briefing.py"
```
