---
name: uhdmovies-downloader
description: "Search, inspect catalog releases, solve link gate shorteners, and automate video downloads with multi-source fallback (Instant Download, DriveSeed, Telegram Bot) from UHDMovies."
version: 1.0.0
author: Krishna Kanth
license: MIT
platforms: [macos, linux]
metadata:
  icon: "🎬"
hermes:
  tags: [UHDMovies, Video, Downloader, Anime, Movies, Telegram, DriveSeed, Media]
  related_skills: [media, youtube-downloader]
---

# 🎬 UHDMovies Downloader Skill

End-to-end automation pipeline to search the UHDMovies catalog, inspect release tiers (resolution, codec, file size per episode), bypass intermediate redirect gates (`unblockedgames.world`), and dispatch downloads via direct CDN links or hands-free macOS Telegram bot links.

---

## Tool Architecture & Available Scripts

All scripts are located in the skill's `scripts/` directory:

| Script | Purpose | Command Example |
| :--- | :--- | :--- |
| **`search.py`** | Search catalog for matching titles & URLs | `python3 scripts/search.py "<query>"` |
| **`inspect_post.py`** | In-depth breakdown of releases, sizes, & episode links | `python3 scripts/inspect_post.py "<post_url>"` |
| **`get_links.py`** | 2-second link locker solver -> final host & Telegram URLs | `python3 scripts/get_links.py --post "<url>" --tier 1 --episodes 1-5` |
| **`telegram.py`** | macOS Telegram launcher & AppleScript prompt accepter | `python3 scripts/telegram.py "<tg_url_or_proto>"` |
| **`batch_downloader.py`** | Full pipeline: solves gates, tests instant CDN, falls back to Telegram | `python3 scripts/batch_downloader.py "<url>" --tier 1 --episodes 7-16` |

---

## Step-by-Step Workflow

### Step 1: Search the Catalog
Search any movie or anime title to get a numbered list of post URLs:
```bash
python3 scripts/search.py "attack on titan"
```

### Step 2: Inspect Post Releases
Inspect the exact quality tiers, file size per episode, and episode counts:
```bash
python3 scripts/inspect_post.py "<POST_URL>"
```
- Add `--all` to print all raw episode gate links.
- Add `--json` for machine-readable JSON output.

### Step 3: Resolve Final Link Pages (Get Links)
Bypasses the 10-second link locker verification in ~2 seconds per episode and outputs the final DriveSeed page and Telegram transfer link:
```bash
# By Post & Episode Range:
python3 scripts/get_links.py \
  --post "<POST_URL>" \
  --tier 2 \
  --episodes 1-5

# Or for a single gate URL:
python3 scripts/get_links.py "<GATE_URL>"
```

### Step 4: Batch Download with Telegram Fallback
Automates the full loop across an entire season or episode list:
```bash
python3 scripts/batch_downloader.py \
  "<POST_URL>" \
  --tier 2 \
  --episodes 7-16
```
- Solves each gate link automatically.
- Tests if Instant Download CDN is alive.
- If dead/404, automatically launches `/Applications/Telegram.app` with `tg://resolve?domain=tgcdn_bot&start=...` and sends the `START` prompt via AppleScript hands-free.
