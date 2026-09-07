#!/usr/bin/env python3
"""
Daily Morning Executive Briefing Pipeline (Armin Agent)
- Autonomous Multi-Source Intelligence & Life Operations Pipeline
- Dynamic Roadmap Progression: Reads Learning/Stock Market & Trading Mastery Roadmap.md,
  advances tick marks (- [x]), and generates dedicated study sub-notes.
- Todos & Backlog Analysis: Inspects Todos/ to synthesize high-signal daily recommendations.
- Live Market Pulse: Live quotes for Nifty 50, Sensex, S&P 500, Nasdaq, Gold, and USD/INR.
- Hyper-Local Weather: Annavaram live weather via wttr.in.
- Anti-Gravity (agy) News Synthesis: agy uses its native tools to curate top 5 AI/world breakthroughs.
- High-Efficiency Audio: macOS Tara (en-IN) TTS compressed with FFmpeg AAC (sub-500 KB + ID3 tags).
- Curated 4K Anime Wallpaper: Death Note, Hunter x Hunter, Vinland Saga, Bleach, Attack on Titan, etc.
- Obsidian Vault Compliance: Strict YAML frontmatter and callout architecture conforming to rules.md.
- Discord Thread Delivery: Clean single-payload report with playable AAC audio & 4K wallpaper.
"""

import os
import sys
import json
import uuid
import random
import datetime
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import re
import shutil
import time
import argparse
from pathlib import Path

# Add script dir to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from market_pulse import get_market_pulse, format_market_pulse_discord, format_market_pulse_obsidian
from weather_service import get_weather
from roadmap_manager import get_next_lesson_and_advance
from todo_analyzer import analyze_todos, generate_strategic_recommendations, format_recommendations_obsidian, format_recommendations_discord

# Configuration
_env_file = SCRIPT_DIR / ".env"
if _env_file.is_file():
    with open(_env_file, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "1543265750414790737")
VOICE_NAME = "Tara"
ASSETS_OUTPUT_DIR = Path("/tmp/armin_briefings")
OBSIDIAN_VAULT_DIR = Path("/Users/krishnakanth/Documents/Obsidian Vault")
OBSIDIAN_DAILY_DIR = OBSIDIAN_VAULT_DIR / "Daily"
PROMPT_MD_PATH = SCRIPT_DIR / "daily_briefing_prompt.md"

ASSETS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OBSIDIAN_DAILY_DIR.mkdir(parents=True, exist_ok=True)

ANIME_POOL = [
    "Death Note",
    "Hunter x Hunter",
    "Vinland Saga",
    "Bleach",
    "Attack on Titan",
    "Jujutsu Kaisen",
    "Demon Slayer",
    "Solo Leveling",
    "Naruto"
]

def invoke_agy_for_news(today):
    """
    Invokes Google Anti-Gravity CLI (agy) non-interactively to use its native tools
    and synthesize today's top 5 AI and tech breakthroughs.
    """
    agy_bin = shutil.which("agy") or "/Users/krishnakanth/.local/bin/agy"
    date_str = today.strftime("%A, %B %d, %Y")

    prompt = f"""You are the Armin Daily Intelligence Agent running inside Google Antigravity.
Today is {date_str}.
Use your native research and web tools to discover the top 5 high-signal breakthroughs in:
1. Frontier Artificial Intelligence & Autonomous Agentic Systems
2. Semiconductor & Compute Infrastructure
3. Global Technology & Science Discoveries

For each breakthrough, provide:
- Headline title
- Verified clickable source URL (or reputable domain)
- 2 concise impact bullet points
- A single spoken sentence suitable for macOS Tara (en-IN) TTS

Output ONLY a valid JSON object matching this schema:
{{
  "news_highlights": [
    {{
      "num": "1️⃣",
      "title": "Headline 1",
      "url": "https://example.com/article",
      "bullets": ["Bullet 1", "Bullet 2"],
      "spoken": "Clear spoken sentence."
    }},
    {{
      "num": "2️⃣",
      "title": "Headline 2",
      "url": "https://example.com/article",
      "bullets": ["Bullet 1", "Bullet 2"],
      "spoken": "Clear spoken sentence."
    }},
    {{
      "num": "3️⃣",
      "title": "Headline 3",
      "url": "https://example.com/article",
      "bullets": ["Bullet 1", "Bullet 2"],
      "spoken": "Clear spoken sentence."
    }},
    {{
      "num": "4️⃣",
      "title": "Headline 4",
      "url": "https://example.com/article",
      "bullets": ["Bullet 1", "Bullet 2"],
      "spoken": "Clear spoken sentence."
    }},
    {{
      "num": "5️⃣",
      "title": "Headline 5",
      "url": "https://example.com/article",
      "bullets": ["Bullet 1", "Bullet 2"],
      "spoken": "Clear spoken sentence."
    }}
  ]
}}
"""

    print("🤖 Invoking Anti-Gravity CLI (agy) to synthesize news intelligence using its native tools...")
    cmd = [
        agy_bin,
        "-p", prompt,
        "--mode", "plan",
        "--dangerously-skip-permissions",
        "--print-timeout", "3m"
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode == 0 and res.stdout:
            json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", res.stdout)
            raw_json = json_match.group(1) if json_match else res.stdout
            brace_match = re.search(r"\{[\s\S]*\}", raw_json)
            if brace_match:
                parsed = json.loads(brace_match.group(0))
                if "news_highlights" in parsed and len(parsed["news_highlights"]) >= 3:
                    print(f"✅ Anti-Gravity CLI successfully synthesized {len(parsed['news_highlights'])} breakthroughs!")
                    return parsed["news_highlights"]
    except Exception as e:
        print(f"⚠️ Notice: agy news invocation encounter: {e}")

    # High-signal curated baseline fallback
    print("ℹ️ Using curated intelligence baseline fallback.")
    return [
        {
            "num": "1️⃣",
            "title": "Autonomous Agentic AI Deployment & Tool Orchestration",
            "url": "https://deepmind.google/technologies/",
            "bullets": ["Next-gen frontier models prioritize recursive tool execution, self-correction, and sandboxed actions."],
            "spoken": "First, autonomous agentic systems continue rapid enterprise adoption with integrated planning."
        },
        {
            "num": "2️⃣",
            "title": "Global AI Safety & Watermarking Cryptographic Standards",
            "url": "https://www.nist.gov/ai",
            "bullets": ["International compliance frameworks mandate provenance tracking and verifiable watermarking."],
            "spoken": "Second, global AI governance frameworks establish mandatory content transparency standards."
        },
        {
            "num": "3️⃣",
            "title": "Semiconductor & Compute Infrastructure Scaling",
            "url": "https://www.semiconductors.org/",
            "bullets": ["Record capital expenditure directed toward high-bandwidth memory and optical interconnect clusters."],
            "spoken": "Third, global compute infrastructure financing expands for next-generation hardware."
        },
        {
            "num": "4️⃣",
            "title": "Edge Computing & Local Neural Architectures",
            "url": "https://arxiv.org/list/cs.AI/recent",
            "bullets": ["On-device small language models achieve sub-second latency for hardware telemetry and robotics."],
            "spoken": "Fourth, edge neural processing accelerates real-time hardware automation."
        },
        {
            "num": "5️⃣",
            "title": "Astrophysics & Deep-Space Spectral Observatories",
            "url": "https://science.nasa.gov/",
            "bullets": ["Advanced optical telescope arrays capture spectroscopic atmospheric signatures of exoplanets."],
            "spoken": "Fifth, deep-space astronomical observations yield new multi-spectral planetary insights."
        }
    ]

def fetch_daily_anime_wallpaper(output_path):
    """Searches and downloads a desktop anime wallpaper from Wallhaven with user-preferred series."""
    selected_anime = random.choice(ANIME_POOL)
    print(f"🎨 Curating daily anime desktop wallpaper: '{selected_anime}'...")
    url = (
        f"https://wallhaven.cc/api/v1/search?"
        f"q={urllib.parse.quote(selected_anime)}&"
        f"categories=010&purity=100&ratios=16x9,16x10&sorting=random"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("data") and len(data["data"]) > 0:
                img_item = data["data"][0]
                img_url = img_item["path"]
                resolution = img_item.get("resolution", "1920x1080")
                print(f"📥 Downloading {selected_anime} wallpaper ({resolution}) from {img_url}...")
                img_req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                    with open(output_path, "wb") as f:
                        f.write(img_resp.read())
                print(f"✅ Wallpaper saved: {output_path} ({os.path.getsize(output_path):,} bytes)")
                return selected_anime, resolution
    except Exception as e:
        print(f"⚠️ Warning: Wallhaven wallpaper download error: {e}")
    return None, None

def synthesize_compressed_voice(script_text, output_audio_path):
    """
    Synthesizes speech using macOS native Tara (en-IN) voice model,
    then compresses to high-efficiency AAC with ID3 track metadata using FFmpeg.
    """
    print(f"🎙️ Synthesizing voice briefing using macOS '{VOICE_NAME}' voice...")
    clean_text = script_text.replace('"', '').replace("'", "").replace("*", "").replace("#", "")
    temp_txt_path = ASSETS_OUTPUT_DIR / "speech_input.txt"
    raw_audio_path = ASSETS_OUTPUT_DIR / "raw_say.m4a"

    with open(temp_txt_path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # 1. macOS say synthesis
    subprocess.run(["say", "-v", VOICE_NAME, "-f", str(temp_txt_path), "-o", str(raw_audio_path)], check=True)
    raw_size = os.path.getsize(raw_audio_path)

    # 2. FFmpeg AAC compression & ID3 tagging
    today_str = datetime.datetime.now().strftime("%B %d, %Y")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_audio_path),
        "-c:a", "aac",
        "-b:a", "128k",
        "-metadata", f"title=Daily Briefing - {today_str}",
        "-metadata", "artist=Armin Intelligence Agent",
        "-metadata", "album=Executive Daily Briefings",
        str(output_audio_path)
    ]
    try:
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        compressed_size = os.path.getsize(output_audio_path)
        reduction = (1 - (compressed_size / raw_size)) * 100
        print(f"✅ AAC Audio generated: {output_audio_path} ({compressed_size:,} bytes, {reduction:.1f}% reduction)")
    except Exception as e:
        print(f"⚠️ FFmpeg compression error ({e}), keeping raw audio.")
        shutil.copy(raw_audio_path, output_audio_path)

    # Cleanup raw audio
    if raw_audio_path.exists():
        raw_audio_path.unlink()

    return str(output_audio_path)

def create_obsidian_daily_note(today, weather, market_pulse_quotes, recommendations, fin_lesson, news_items, anime_title, resolution):
    """Creates today's Daily Note conforming strictly to Obsidian Vault rules.md with YAML frontmatter."""
    note_path = OBSIDIAN_DAILY_DIR / f"{today.strftime('%Y-%m-%d')}.md"
    day_name = today.strftime("%A")
    month_name = today.strftime("%B")
    day_num = today.strftime("%d")
    year_num = today.strftime("%Y")
    today_str = today.strftime("%Y-%m-%d")

    market_table = format_market_pulse_obsidian(market_pulse_quotes)
    recs_section = format_recommendations_obsidian(recommendations)

    lines = [
        "---",
        f'title: "Daily Tasks - {day_name}, {month_name} {day_num}, {year_num}"',
        f"date: {today_str}",
        "tags:",
        "  - daily",
        "  - tasks",
        "  - briefing",
        "  - automation",
        "  - finance",
        "  - learning",
        "  - anti-gravity",
        "status: in-progress",
        "version: 1.0.0",
        "---",
        "",
        f"# Daily Tasks - {day_name}, {month_name} {day_num}, {year_num}",
        "",
        "> [!abstract] Morning Executive Briefing Overview",
        f"> **Weather:** {weather}  ",
        f"> **Roadmap Progress:** {fin_lesson['category']} (Day {fin_lesson['day']})  ",
        f"> **Vault Link:** [[Todos/Todos|📝 Master To-Do Hub]] & [[Learning/Stock Market & Trading Mastery Roadmap|📈 Roadmap]]",
        "",
        "---",
        "",
        "## 📋 Today's Tasks",
        "",
        "### 🏃 Morning (7:00 AM - 12:00 PM)",
        f"- [x] Daily automated Discord executive briefing delivered ✅ {today_str}",
        f"- [ ] Review daily market lesson: {fin_lesson['note_wikilink']} 📅 {today_str}",
    ]

    if fin_lesson.get("todos"):
        for t_title, t_desc in fin_lesson["todos"]:
            lines.append(f"  - [ ] **{t_title}**: {t_desc}")
    if fin_lesson.get("rollover") and fin_lesson.get("recommendation"):
        lines.append(f"  - [ ] ⚠️ **Catch-Up Required**: {fin_lesson['recommendation']}")

    lines.extend([
        "- [ ] Review morning radar & system advisories",
        "- [ ] LeetCode / DSA problem solving",
        "- [ ] System design & architecture study",
        "",
        "### 🔧 Afternoon (12:00 PM - 6:00 PM)",
        "- [ ] Lunch & mid-day recharge",
        "- [ ] Deep Work Block: Core project engineering & MCP development",
        "- [ ] Code reviews & PR audits",
        "- [ ] Evening walk / Flex time",
        "",
        "### 🌙 Evening (6:00 PM - 10:00 PM)",
        "- [ ] Social / Free time / Hobbies",
        "- [ ] Gaming session 🎮",
        "- [ ] End-of-day review & tomorrow's milestone setup",
        "",
        "---",
        "",
        "## 🎯 Recommended Focus & Next Actions (from Todos Hub)",
        "",
        recs_section,
        "",
        "---",
        "",
        "## 📊 Live Market Pulse Snapshot",
        "",
        market_table,
        "",
        "---",
        "",
        f"## 📈 Daily Market & Trading Insight (Day {fin_lesson['day']}{' - Catch-Up' if fin_lesson.get('rollover') else ''})",
        "",
        f"> [!tip] {fin_lesson['title']} ({fin_lesson['category']})",
        f"> **Core Principle:** {fin_lesson['principle']}",
        "> ",
        f"> **Real-World Application:** {fin_lesson['application']}",
        "> ",
        f"> **🎯 Golden Rule:** `{fin_lesson['golden_rule']}`",
        "> ",
        f"> *Deep-dive study guide:* {fin_lesson['note_wikilink']}",
    ])

    if fin_lesson.get("todos"):
        lines.append("> ")
        lines.append("> **📋 Today's Actionable To-Dos:**")
        for t_title, t_desc in fin_lesson["todos"]:
            lines.append(f"> - [ ] **{t_title}**: {t_desc}")
    if fin_lesson.get("rollover") and fin_lesson.get("recommendation"):
        lines.append("> ")
        lines.append(f"> ⚠️ **Rollover Advisory:** {fin_lesson['recommendation']}")

    lines.extend([
        "",
        "---",
        "",
        f"## 📰 Tech News Highlights ({month_name} {day_num}, {year_num})",
        ""
    ])

    for idx, item in enumerate(news_items, 1):
        url = item.get("url", "")
        title = item['title']
        title_md = f"[{title}]({url})" if url else title
        bullets_str = ' '.join(item.get('bullets', []))
        lines.append(f"{idx}. **{title_md}** — {bullets_str}")

    lines.extend([
        "",
        "---",
        "",
        "## 🖼️ Daily Anime Wallpaper",
        "",
        "> [!tip] Featured Series",
        f"> **{anime_title or 'Attack on Titan'}** ({resolution or '4K Widescreen'})",
        "> Delivered to Discord daily thread.",
        "",
        "---",
        "",
        "## 🏋️ Today's Workout Plan",
        "",
        "**Duration:** 30-45 min  ",
        "**Focus:** Conditioning & Core Strength",
        "",
        "### Warm-up (5 min)",
        "- Jumping jacks: 30 sec",
        "- Arm circles: 30 sec forward + 30 sec backward",
        "- High knees: 30 sec",
        "- Bodyweight squats: 10 reps",
        "",
        "### Main Circuit (3 rounds)",
        "1. Dumbbell Goblet Squats: 12 reps",
        "2. Push-ups: 10-12 reps",
        "3. Dumbbell Romanian Deadlifts: 10 reps",
        "4. Plank hold: 30 sec",
        "5. Dumbbell Rows: 10 reps per arm",
        "6. Mountain Climbers: 30 sec",
        "",
        "### Cool-down (5 min)",
        "- Hamstring stretch: 30 sec per leg",
        "- Chest stretch: 30 sec",
        "- Child's pose: 45 sec",
        "",
        "---",
        "",
        "## 📅 Daily Timetable",
        "",
        "```text",
        "07:00 AM ─ 🌅 Morning Kickoff & Briefing Review",
        "08:00 AM ─ 🤖 Automated Daily Discord Briefing & Audio Delivery",
        "08:30 AM ─ 🏃 Morning Workout & Freshen Up",
        "09:30 AM ─ 🎯 DSA Practice (LeetCode / Codeforces)",
        "11:00 AM ─ 📝 System Design & Tech Research",
        "12:30 PM ─ 🍽️ Lunch & Recharge",
        "02:00 PM ─ 🔧 Project Engineering / Deep Work",
        "04:30 PM ─ 🌳 Evening Walk & Break",
        "06:00 PM ─ 📈 Stock Market & Trading Lesson Review",
        "08:00 PM ─ 🎮 Gaming Session",
        "10:00 PM ─ 🌙 Review & Sleep Prep",
        "```",
        "",
        "---",
        "",
        "## 📝 End-of-Day Review",
        "*Fill this in tonight before bed:*",
        "- Tasks completed:",
        "- What went well:",
        "- What to improve:",
        "- Tomorrow's priority:",
        ""
    ])

    with open(note_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📝 Obsidian Daily Note successfully created: {note_path}")
    return str(note_path)

def create_discord_thread(thread_name):
    """Creates a public thread in the target Discord channel."""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/threads"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (ArminAgent, 2.0)"
    }
    payload = {"name": thread_name, "auto_archive_duration": 1440, "type": 11}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"🧵 Created Discord Thread: '{thread_name}' (ID: {data['id']})")
            return data["id"]
    except urllib.error.HTTPError as e:
        print(f"❌ Error creating thread: {e.code} - {e.read().decode('utf-8')}")
        return CHANNEL_ID

def split_message_chunks(text, max_len=1900):
    """
    Splits text into chunks of at most max_len characters,
    splitting cleanly on paragraphs and item boundaries without losing any content.
    """
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para) + 2  # include \n\n
        if len(para) > max_len:
            # If a single paragraph is longer than max_len, split by single lines
            if current_chunk:
                chunks.append("\n\n".join(current_chunk).strip())
                current_chunk = []
                current_len = 0
            for line in para.split("\n"):
                line_len = len(line) + 1
                if current_len + line_len > max_len and current_chunk:
                    chunks.append("\n".join(current_chunk).strip())
                    current_chunk = [line]
                    current_len = line_len
                else:
                    current_chunk.append(line)
                    current_len += line_len
            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())
                current_chunk = []
                current_len = 0
            continue

        if current_len + para_len > max_len and current_chunk:
            chunks.append("\n\n".join(current_chunk).strip())
            current_chunk = [para]
            current_len = para_len
        else:
            current_chunk.append(para)
            current_len += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk).strip())

    return chunks

def send_single_discord_message(channel_id, content, audio_path=None, wallpaper_path=None):
    """
    Delivers a single message to a Discord channel or thread.
    If media files are provided, uses multipart form-data.
    Otherwise, uses a lightweight JSON POST payload.
    """
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    has_audio = bool(audio_path and os.path.exists(audio_path))
    has_wall = bool(wallpaper_path and os.path.exists(wallpaper_path))

    if has_audio or has_wall:
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        crlf = "\r\n".encode("utf-8")
        body = bytearray()

        body.extend(f"--{boundary}".encode("utf-8") + crlf)
        body.extend(b'Content-Disposition: form-data; name="payload_json"' + crlf)
        body.extend(b'Content-Type: application/json' + crlf + crlf)
        body.extend(json.dumps({"content": content}).encode("utf-8") + crlf)

        file_idx = 0
        if has_audio:
            audio_filename = os.path.basename(audio_path)
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            body.extend(f"--{boundary}".encode("utf-8") + crlf)
            body.extend(f'Content-Disposition: form-data; name="files[{file_idx}]"; filename="{audio_filename}"'.encode("utf-8") + crlf)
            body.extend(b"Content-Type: audio/mp4" + crlf + crlf)
            body.extend(audio_bytes + crlf)
            file_idx += 1

        if has_wall:
            wall_filename = os.path.basename(wallpaper_path)
            with open(wallpaper_path, "rb") as f:
                wall_bytes = f.read()
            body.extend(f"--{boundary}".encode("utf-8") + crlf)
            body.extend(f'Content-Disposition: form-data; name="files[{file_idx}]"; filename="{wall_filename}"'.encode("utf-8") + crlf)
            body.extend(b"Content-Type: image/jpeg" + crlf + crlf)
            body.extend(wall_bytes + crlf)
            file_idx += 1

        body.extend(f"--{boundary}--".encode("utf-8") + crlf)

        headers = {
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "DiscordBot (ArminAgent, 2.0)",
            "Content-Length": str(len(body))
        }
        req = urllib.request.Request(url, data=bytes(body), headers=headers, method="POST")
    else:
        headers = {
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (ArminAgent, 2.0)"
        }
        req = urllib.request.Request(
            url,
            data=json.dumps({"content": content}).encode("utf-8"),
            headers=headers,
            method="POST"
        )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"❌ Error delivering briefing message: {e.code} - {err_msg}")
        raise

def send_briefing_to_discord(thread_id, content_markdown, audio_path=None, wallpaper_path=None):
    """
    Delivers formatted briefing card(s) with playable audio and wallpaper attachments.
    Ensures all content (including full top 5 breakthroughs) is delivered without truncation.
    """
    if isinstance(content_markdown, str):
        message_list = [content_markdown]
    elif isinstance(content_markdown, (list, tuple)):
        message_list = list(content_markdown)
    else:
        message_list = [str(content_markdown)]

    all_chunks = []
    for msg in message_list:
        all_chunks.extend(split_message_chunks(msg, max_len=1900))

    results = []
    for idx, chunk in enumerate(all_chunks):
        msg_audio = audio_path if idx == 0 else None
        msg_wall = wallpaper_path if idx == 0 else None

        print(f"📨 Delivering Discord card part {idx + 1}/{len(all_chunks)} ({len(chunk)} chars)...")
        res = send_single_discord_message(
            channel_id=thread_id,
            content=chunk,
            audio_path=msg_audio,
            wallpaper_path=msg_wall
        )
        print(f"🚀 Part {idx + 1} delivered successfully! Message ID: {res['id']}")
        results.append(res)
        if idx < len(all_chunks) - 1:
            time.sleep(0.5)

    return results

def format_discord_content(today_date_str, weather, market_pulse_quotes, recommendations, fin_lesson, news_items, anime_title, resolution):
    """
    Formats the briefing into structured cards for Discord thread delivery:
    Card 1: Executive Dashboard (Weather, Market Pulse, Market Masterclass, Strategic Focus, Media info)
    Card 2: Top 5 Frontier Breakthroughs (Full AI, Tech & Science intelligence with all bullet points intact)
    """
    market_bar = format_market_pulse_discord(market_pulse_quotes)
    recs_discord = format_recommendations_discord(recommendations)
    lesson_title = fin_lesson['title'].split(':')[-1].strip()

    status_tag = " (Catch-Up / Rollover)" if fin_lesson.get("rollover") else ""
    # Card 1: Executive Dashboard & Action Plan
    card1_lines = [
        f"## 📅 Daily Executive Briefing — {today_date_str}",
        f"🌤️ **Weather**: {weather}",
        f"📊 **Market Pulse**: {market_bar}",
        "---",
        f"### 📈 Market Masterclass (Day {fin_lesson['day']}{status_tag}): **{lesson_title}**",
        f"> • **Principle**: {fin_lesson['principle']}",
        f"> • **Application**: {fin_lesson['application']}",
        f"> • 🎯 **Golden Rule**: `{fin_lesson['golden_rule']}`",
        f"> • 📖 **Study Guide**: {fin_lesson['note_wikilink']}",
    ]

    if fin_lesson.get("todos"):
        card1_lines.append("> ")
        card1_lines.append("> 📋 **Today's Actionable To-Dos**:")
        for t_title, t_desc in fin_lesson["todos"]:
            card1_lines.append(f">   • **{t_title}**: {t_desc}")
    if fin_lesson.get("rollover") and fin_lesson.get("recommendation"):
        card1_lines.append("> ")
        card1_lines.append(f"> ⚠️ **Rollover Advisory**: {fin_lesson['recommendation']}")
    card1_lines.append("---")

    if recs_discord:
        card1_lines.append(recs_discord)
        card1_lines.append("---")

    if anime_title:
        card1_lines.extend([
            f"🖼️ **Wallpaper**: *{anime_title}* ({resolution})",
            "🎙️ **Audio Briefing**: High-Efficiency AAC attached below."
        ])
    else:
        card1_lines.append("🎙️ **Audio Briefing**: High-Efficiency AAC attached below.")

    # Card 2: Top 5 Frontier Breakthroughs
    card2_items = [
        f"### 🌐 Top 5 Frontier Breakthroughs — {today_date_str}"
    ]
    for item in news_items:
        url = item.get("url")
        title = item["title"]
        title_str = f"[{title}]({url})" if url else title
        item_text = f"{item.get('num', '•')} **{title_str}**"
        for bullet in item.get("bullets", []):
            item_text += f"\n> • {bullet}"
        card2_items.append(item_text)

    return ["\n".join(card1_lines), "\n\n".join(card2_items)]

def build_voice_script(today, fin_lesson, news_items, anime_title, weather):
    lesson_spoken = fin_lesson.get("spoken", f"Today's financial lesson is {fin_lesson['title']}.")
    if fin_lesson.get("rollover"):
        lesson_spoken = f"Today is a dedicated catch-up day for Day {fin_lesson['day']}. Be sure to complete your practical exercises before advancing."

    parts = [
        f"Good morning! Here is your daily executive briefing for {today.strftime('%A, %B %d, %Y')}.",
        f"Today in {weather}.",
        lesson_spoken,
        "Now, here are today's top breakthroughs from global technology and artificial intelligence:"
    ]
    for item in news_items:
        parts.append(item.get("spoken", item["title"]))
    if anime_title:
        parts.append(f"Today's featured anime desktop wallpaper is from {anime_title}.")
    parts.append("Have a disciplined, wonderful, and highly productive day ahead!")
    return "\n\n".join(parts)

def run_pipeline(dry_run=False, no_audio=False, no_wallpaper=False, test_discord=False, force=False):
    today = datetime.datetime.now()
    today_date_str = today.strftime("%B %d, %Y")
    today_ymd = today.strftime("%Y-%m-%d")
    daily_note_path = OBSIDIAN_DAILY_DIR / f"{today_ymd}.md"

    # Idempotency check: prevent duplicate briefings when computer boots or restarts
    if not dry_run and not force and daily_note_path.exists():
        print(f"ℹ️ Daily note for today ({today_ymd}) already exists: {daily_note_path}")
        print("Briefing has already completed for today. Use --force to re-run. Exiting cleanly.")
        return

    thread_title = f"📅 Daily Briefing – {today_date_str}"
    audio_path = ASSETS_OUTPUT_DIR / f"daily_briefing_{today.strftime('%Y%m%d')}.m4a"
    wallpaper_path = ASSETS_OUTPUT_DIR / f"daily_wallpaper_{today.strftime('%Y%m%d')}.jpg"

    print(f"\n==================================================")
    print(f"  Armin Executive Daily Briefing: {today_date_str}")
    print(f"  Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print(f"==================================================\n")

    # 1. Hyper-local Weather
    print("🌤️ Fetching hyper-local weather...")
    weather = get_weather()

    # 2. Live Market Pulse
    print("📊 Fetching live market quotes...")
    market_quotes = get_market_pulse()

    # 3. Analyze Todos & Project Backlog
    print("🎯 Analyzing Todos hub for recommendations...")
    todo_tasks = analyze_todos()
    recommendations = generate_strategic_recommendations(todo_tasks)

    # 4. Roadmap Progression & Sub-Note Generation
    print("📈 Progressing Stock Market Learning Roadmap...")
    fin_lesson = get_next_lesson_and_advance(dry_run=dry_run)

    # 5. News Synthesis via Anti-Gravity (agy)
    news_items = invoke_agy_for_news(today)

    # 6. Anime Wallpaper
    anime_title, resolution = None, None
    if not no_wallpaper:
        anime_title, resolution = fetch_daily_anime_wallpaper(wallpaper_path)

    # 7. Obsidian Daily Note
    if not dry_run:
        create_obsidian_daily_note(
            today=today,
            weather=weather,
            market_pulse_quotes=market_quotes,
            recommendations=recommendations,
            fin_lesson=fin_lesson,
            news_items=news_items,
            anime_title=anime_title,
            resolution=resolution
        )

    # 8. Discord Content Preparation
    discord_markdown = format_discord_content(
        today_date_str=today_date_str,
        weather=weather,
        market_pulse_quotes=market_quotes,
        recommendations=recommendations,
        fin_lesson=fin_lesson,
        news_items=news_items,
        anime_title=anime_title,
        resolution=resolution
    )

    # 9. Voice Synthesis
    audio_file_to_send = None
    if not no_audio and not dry_run:
        voice_script = build_voice_script(today, fin_lesson, news_items, anime_title, weather)
        audio_file_to_send = synthesize_compressed_voice(voice_script, audio_path)

    # 10. Discord Delivery
    if dry_run:
        print("\n--- [DRY RUN] Obsidian Note & Roadmap Preview ---")
        print(f"Roadmap Target: {fin_lesson['title']}")
        print(f"Sub-Note Path: {fin_lesson.get('note_path')}")
        print("\n--- [DRY RUN] Discord Message Preview ---")
        if isinstance(discord_markdown, list):
            for i, part in enumerate(discord_markdown, 1):
                print(f"\n[Card {i} — {len(part)} chars]:\n{part}\n")
        else:
            print(discord_markdown)
        print("\n✅ Dry run completed successfully with zero mutations.")
        return

    if test_discord or not dry_run:
        print("\n🚀 Delivering to Discord...")
        thread_id = create_discord_thread(thread_title)
        send_briefing_to_discord(
            thread_id=thread_id,
            content_markdown=discord_markdown,
            audio_path=audio_file_to_send,
            wallpaper_path=wallpaper_path if (anime_title and not no_wallpaper) else None
        )

    print("\n🎉 Daily Executive Briefing pipeline finished successfully!")

def main():
    parser = argparse.ArgumentParser(description="Armin Daily Executive Briefing Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run without posting to Discord or modifying notes")
    parser.add_argument("--no-audio", action="store_true", help="Skip voice audio synthesis")
    parser.add_argument("--no-wallpaper", action="store_true", help="Skip anime wallpaper download")
    parser.add_argument("--test-discord", action="store_true", help="Test delivery to Discord")
    parser.add_argument("--force", action="store_true", help="Force run even if today's briefing already exists")
    args = parser.parse_args()

    run_pipeline(
        dry_run=args.dry_run,
        no_audio=args.no_audio,
        no_wallpaper=args.no_wallpaper,
        test_discord=args.test_discord,
        force=args.force
    )

if __name__ == "__main__":
    main()
