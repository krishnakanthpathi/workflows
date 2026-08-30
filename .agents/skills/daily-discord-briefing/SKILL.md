---
name: daily-discord-briefing
description: Automated daily executive briefing pipeline. Curates top 5 AI & world breakthroughs, synthesizes macOS Tara (en-IN) voice briefing, fetches a daily 4K anime desktop wallpaper, and delivers a unified blockquote card with playable media to a dedicated Discord thread.
version: 1.0.0
author: Krishna Kanth
license: MIT
---

# Daily Discord Briefing & Anime Wallpaper Skill

An end-to-end automated executive briefing system that performs real-time research, generates macOS native speech audio, curates widescreen anime desktop wallpapers, and delivers a clean single-payload report directly to Discord threads.

---

## Capabilities

1. **Live World & AI Intelligence**:
   * Scrapes breaking AI/tech breakthroughs and major global news.
   * Formats reports into clean, mobile-optimized Discord **Blockquote Bullet Cards**.

2. **Tara (`en-IN`) Voice Synthesis**:
   * Generates natural speech using macOS native `say -v Tara` voice model.
   * Exports Apple AAC `.m4a` audio format.

3. **Daily Anime Desktop Wallpaper**:
   * Fetches high-resolution 16:9 / 16:10 desktop wallpapers (1080p, 1440p, 4K) via Wallhaven API.
   * Curated pool: *Attack on Titan, Bleach, Naruto, Jujutsu Kaisen, Demon Slayer, Solo Leveling, One Piece, Death Note, Dragon Ball*.

4. **Discord Thread Delivery**:
   * Dynamically creates a public daily thread: `📅 Daily Briefing – [Current Date]`.
   * Posts formatted markdown report, inline playable audio player, and high-res wallpaper in a single unified message.

---

## Quick Reference

| Action | Command |
| :--- | :--- |
| **Run Daily Briefing Pipeline** | `python3 scripts/daily_briefing.py` |
| **Custom Channel Target** | `DISCORD_CHANNEL_ID="<id>" python3 scripts/daily_briefing.py` |
| **Custom Bot Token** | `DISCORD_BOT_TOKEN="<token>" python3 scripts/daily_briefing.py` |

---

## Execution Modes & Automation

### 1. Standalone Terminal / Script Execution
```bash
python3 /Users/krishnakanth/Projects/workflow/.agents/skills/daily-discord-briefing/scripts/daily_briefing.py
```

### 2. macOS `launchd` Service (System Level)
Runs every morning even across laptop sleep/wake cycles:
* **Plist Path**: `~/Library/LaunchAgents/com.armin.dailybriefing.plist`
* **Schedule**: Daily at `08:00 AM`

### 3. Antigravity Daemon Scheduler
```text
CronExpression: "0 8 * * *"
IsDaemon: true
Prompt: "python3 /Users/krishnakanth/Projects/workflow/.agents/skills/daily-discord-briefing/scripts/daily_briefing.py"
```

---

## File Structure

```text
daily-discord-briefing/
├── SKILL.md                 # Skill documentation and operational guide
└── scripts/
    └── daily_briefing.py     # Main Python pipeline (Search -> Voice -> Wallpaper -> Discord)
```
