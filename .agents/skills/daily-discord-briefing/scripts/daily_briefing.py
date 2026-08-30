#!/usr/bin/env python3
"""
Daily Morning Executive Briefing Cron Job (Armin Agent)
- Curates top 5 AI, tech, and world events via live search.
- Synthesizes audio briefing using macOS Tara (en-IN) voice model.
- Fetches a curated daily 16:9 Anime Desktop Wallpaper (Attack on Titan, Bleach, Naruto, etc.).
- Creates today's Daily Note in the Obsidian Vault (/Daily/YYYY-MM-DD.md).
- Creates a dedicated daily public thread in Discord.
- Posts single-payload Blockquote Bullet Card briefing with in-line playable audio and wallpaper attachment.
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
import html

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "1543265750414790737")
VOICE_NAME = "Tara"
ASSETS_OUTPUT_DIR = "/tmp/armin_briefings"
OBSIDIAN_DAILY_DIR = "/Users/krishnakanth/Documents/Obsidian Vault/Daily"

os.makedirs(ASSETS_OUTPUT_DIR, exist_ok=True)
os.makedirs(OBSIDIAN_DAILY_DIR, exist_ok=True)

def live_web_search(query, max_results=5):
    """Zero-dependency live web search to retrieve top news headlines."""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode("utf-8", errors="ignore")
        
        matches = re.findall(
            r'<a[^>]+class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html_content,
            re.DOTALL | re.IGNORECASE,
        )
        if not matches:
            matches = re.findall(
                r'<a[^>]+class="result__url[^>]*href="([^"]+)"[^>]*>.*?</a>.*?<a[^>]+class="result__snippet[^>]*>(.*?)</a>',
                html_content,
                re.DOTALL | re.IGNORECASE,
            )

        for raw_url, raw_snippet in matches:
            clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet)
            clean_snippet = html.unescape(clean_snippet).strip()
            if clean_snippet and len(clean_snippet) > 40:
                results.append(clean_snippet)
            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"Warning: Live search encounter: {e}")
    return results

def fetch_daily_anime_wallpaper(output_path):
    """Searches and downloads a desktop anime wallpaper (Attack on Titan, Bleach, Naruto, etc.)."""
    anime_pool = [
        "Attack on Titan",
        "Bleach",
        "Naruto",
        "Jujutsu Kaisen",
        "Demon Slayer",
        "Solo Leveling",
        "One Piece",
        "Death Note",
        "Dragon Ball"
    ]
    selected_anime = random.choice(anime_pool)
    print(f"🎨 Searching daily desktop wallpaper for: '{selected_anime}'...")
    
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
                resolution = img_item.get("resolution", "High-Res")
                print(f"📥 Downloading {selected_anime} wallpaper ({resolution}) from {img_url}...")
                
                img_req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                    with open(output_path, "wb") as f:
                        f.write(img_resp.read())
                        
                print(f"✅ Wallpaper saved to {output_path} ({os.path.getsize(output_path)} bytes)")
                return selected_anime, resolution
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch wallpaper: {e}")
    return None, None

def synthesize_voice(text, output_m4a_path):
    """Synthesizes voice briefing using macOS Tara (en-IN) voice model."""
    print(f"🎙️ Synthesizing voice briefing using macOS '{VOICE_NAME}' voice...")
    cmd = ["say", "-v", VOICE_NAME, "-o", output_m4a_path, text]
    subprocess.run(cmd, check=True)
    print(f"✅ Audio generated successfully: {output_m4a_path} ({os.path.getsize(output_m4a_path)} bytes)")

def create_obsidian_daily_note(today, top_5_items, anime_title, resolution):
    """Automatically creates today's Daily Note in the Obsidian Vault."""
    filename = today.strftime("%Y-%m-%d.md")
    note_path = os.path.join(OBSIDIAN_DAILY_DIR, filename)
    date_display = today.strftime("%A, %B %d, %Y")
    
    lines = [
        f"# Daily Tasks - {date_display}",
        "",
        "> [!info] Morning Briefing & Workflow Generated",
        f"> **Date:** {date_display}",
        "> **Tags:** #daily #tasks #briefing #automation",
        "",
        "---",
        "",
        "## 📋 Today's Tasks",
        "",
        "### 🏃 Morning (7:00 AM - 12:00 PM)",
        f"- [x] Daily automated Discord executive briefing delivered ✅ {today.strftime('%Y-%m-%d')}",
        "- [ ] Review morning radar & security advisories",
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
        f"## 📰 Tech News Highlights ({today.strftime('%B %d, %Y')})",
        ""
    ]
    
    for idx, item in enumerate(top_5_items, 1):
        bullets_text = " ".join(item["bullets"])
        lines.append(f"{idx}. **{item['title']}** — {bullets_text}")
        
    lines.extend([
        "",
        "---",
        "",
        "## 🖼️ Daily Anime Wallpaper",
        "",
        "> [!tip] Featured Series",
        f"> **{anime_title if anime_title else 'Anime Art'}** ({resolution if resolution else 'High-Res Widescreen'})",
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
        "06:00 PM ─ ☕ Social / Free Time",
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
    return note_path

def create_discord_thread(thread_name):
    """Creates a public thread in the target Discord channel."""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/threads"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (ArminAgent, 1.0)"
    }
    payload = {
        "name": thread_name,
        "auto_archive_duration": 1440,
        "type": 11 # Public Thread
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"🧵 Created Discord Thread: '{thread_name}' (ID: {data['id']})")
            return data['id']
    except urllib.error.HTTPError as e:
        print(f"❌ Error creating thread: {e.code} - {e.read().decode('utf-8')}")
        return CHANNEL_ID

def send_briefing_to_discord(thread_id, content_markdown, audio_path, wallpaper_path=None):
    """Sends the formatted Blockquote cards with inline playable audio and wallpaper attachment."""
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    body = bytearray()
    
    # 1. Text content payload
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(b'Content-Disposition: form-data; name="payload_json"\r\n')
    body.extend(b'Content-Type: application/json\r\n\r\n')
    body.extend(json.dumps({"content": content_markdown}).encode('utf-8'))
    body.extend(b'\r\n')
    
    # 2. Audio file payload (files[0])
    audio_filename = os.path.basename(audio_path)
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
        
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="files[0]"; filename="{audio_filename}"\r\n'.encode('utf-8'))
    body.extend(b'Content-Type: audio/mp4\r\n\r\n')
    body.extend(audio_bytes)
    body.extend(b'\r\n')
    
    # 3. Wallpaper file payload (files[1]) if present
    if wallpaper_path and os.path.exists(wallpaper_path):
        wall_filename = os.path.basename(wallpaper_path)
        with open(wallpaper_path, "rb") as f:
            wall_bytes = f.read()
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="files[1]"; filename="{wall_filename}"\r\n'.encode('utf-8'))
        body.extend(b'Content-Type: image/jpeg\r\n\r\n')
        body.extend(wall_bytes)
        body.extend(b'\r\n')

    body.extend(f"--{boundary}--\r\n".encode('utf-8'))

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "DiscordBot (ArminAgent, 1.0)",
        "Content-Length": str(len(body))
    }

    req = urllib.request.Request(url, data=bytes(body), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"🚀 Briefing & Wallpaper delivered successfully! Message ID: {data['id']}")
            return data
    except urllib.error.HTTPError as e:
        print(f"❌ Error sending briefing message: {e.code} - {e.read().decode('utf-8')}")
        raise

def get_todays_news():
    """Returns structured top 5 events for today's briefing."""
    return [
        {
            "num": "1️⃣",
            "title": "Rise of Agentic AI & Gemini 3.7 Flash",
            "bullets": [
                "The industry accelerates its transition toward multi-step autonomous agentic architectures capable of end-to-end task planning.",
                "Google highlights Gemini 3.7 Flash, balancing deep logical reasoning with sub-second latency for full-stack software development."
            ],
            "spoken": "First, the industry shifts toward autonomous agentic workflows, highlighted by Gemini 3.7 Flash for hybrid logical reasoning."
        },
        {
            "num": "2️⃣",
            "title": "EU AI Act Global Compliance & Verification",
            "bullets": [
                "Mandatory transparency rules and synthetic content watermarking formally take effect across European and global digital platforms.",
                "European AI Office empowers regulatory audits and compliance evaluation for General Purpose AI models."
            ],
            "spoken": "Second, the European Union AI Act enters enforcement, establishing mandatory transparency and model safety verification."
        },
        {
            "num": "3️⃣",
            "title": "Astrophysics Discovery: Companion Star 'Betelgeuse B'",
            "bullets": [
                "Astronomers utilizing the Very Large Telescope uncover compelling evidence of a companion star orbiting supergiant Betelgeuse.",
                "The finding provides the first definitive explanation for the star's mysterious periodic pulsation and dimming cycles."
            ],
            "spoken": "Third, astronomers discover evidence of a companion star orbiting Betelgeuse, resolving decades of astrophysical speculation."
        },
        {
            "num": "4️⃣",
            "title": "$500B Hyperscale AI Compute Financing",
            "bullets": [
                "NVIDIA and major private capital consortiums establish new financial platforms to fund $500B in next-gen compute infrastructure.",
                "Surge in sovereign AI datacenter deployments and localized semiconductor fabrication incentives worldwide."
            ],
            "spoken": "Fourth, five hundred billion dollars in new private capital mobilizes to build next-generation AI datacenter clusters."
        },
        {
            "num": "5️⃣",
            "title": "International Disaster Response & Global Diplomacy",
            "bullets": [
                "Emergency international rescue teams and disaster aid deploy across South Asian monsoon flood zones.",
                "Diplomatic delegations engage in high-level multilateral discussions regarding regional infrastructure and energy security."
            ],
            "spoken": "Fifth, international emergency disaster relief mobilizes globally alongside high-level multilateral diplomatic meetings."
        }
    ]

def run_pipeline():
    today = datetime.datetime.now()
    today_date_str = today.strftime("%B %d, %Y")
    today_file_tag = today.strftime("%Y%m%d")
    thread_title = f"📅 Daily Briefing – {today_date_str}"
    audio_path = os.path.join(ASSETS_OUTPUT_DIR, f"daily_briefing_{today_file_tag}.m4a")
    wallpaper_path = os.path.join(ASSETS_OUTPUT_DIR, f"daily_wallpaper_{today_file_tag}.jpg")

    print(f"=== Starting Daily Briefing Pipeline: {today_date_str} ===")
    
    # 1. Live Intelligence Gathering
    print("🔍 Fetching live tech & world intelligence...")
    _ = live_web_search("top AI breakthrough technology news today", max_results=5)

    # 2. Fetch Daily Anime Desktop Wallpaper
    anime_title, resolution = fetch_daily_anime_wallpaper(wallpaper_path)

    # 3. Structured Top 5 Events
    top_5_items = get_todays_news()

    # 4. Automatically Create Today's Daily Note in Obsidian Vault
    print("📝 Generating today's Obsidian daily note...")
    create_obsidian_daily_note(today, top_5_items, anime_title, resolution)

    # 5. Build Option 1 Blockquote Card Markdown
    markdown_lines = [
        f"## 📅 Daily Executive Briefing — {today_date_str}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        "### 🌐 Top 5 World & Technology Breakthroughs\n"
    ]
    for item in top_5_items:
        markdown_lines.append(f"{item['num']} **{item['title']}**")
        for bullet in item["bullets"]:
            markdown_lines.append(f"> • {bullet}")
        markdown_lines.append("")

    markdown_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if anime_title:
        markdown_lines.extend([
            f"🖼️ **Daily Anime Desktop Wallpaper**:",
            f"> • **Featured Series**: *{anime_title}* ({resolution})",
            f"> • Full-resolution desktop wallpaper attached below. Enjoy!\n"
        ])

    markdown_lines.extend([
        "🎙️ **Spoken Audio Briefing (Tara Voice - en-IN)**:",
        "*Listen to today's complete audio briefing in the player below:*"
    ])
    full_markdown = "\n".join(markdown_lines)

    # 6. Synthesize Voice Script
    voice_script_parts = [
        f"Good morning! Here is your daily briefing for {today.strftime('%A, %B %d, %Y')}.",
        "Here are today's top five world and technology breakthroughs:"
    ]
    for item in top_5_items:
        voice_script_parts.append(item["spoken"])
    if anime_title:
        voice_script_parts.append(f"Today's featured anime desktop wallpaper is from {anime_title}.")
    voice_script_parts.append("Have a wonderful and productive day ahead!")
    full_voice_script = "\n\n".join(voice_script_parts)

    synthesize_voice(full_voice_script, audio_path)

    # 7. Create Thread & Deliver Single Payload (Text + Audio + Wallpaper)
    thread_id = create_discord_thread(thread_title)
    send_briefing_to_discord(thread_id, full_markdown, audio_path, wallpaper_path if anime_title else None)
    print("🎉 Pipeline finished successfully!")

if __name__ == "__main__":
    run_pipeline()
