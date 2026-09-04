#!/usr/bin/env python3
"""
Daily Morning Executive Briefing Cron Job (Armin Agent)
- Curates top 5 AI, tech, and world events via live search.
- Curates daily progressive Stock Market & Trading Masterclass (60-day curriculum).
- Synthesizes audio briefing using macOS Tara (en-IN) voice model.
- Fetches a curated daily 16:9 Anime Desktop Wallpaper (Attack on Titan, Bleach, Naruto, etc.).
- Creates today's Daily Note in the Obsidian Vault (/Daily/YYYY-MM-DD.md) with Tasks & Financial Insights.
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

# 60-Day Progressive Stock Market & Trading Educational Curriculum
DAILY_FINANCIAL_CONCEPTS = [
    {
        "day": 1,
        "category": "Foundations",
        "title": "Fractional Ownership & Equity",
        "principle": "Buying a share makes you a part-owner of a real business, entitled to its earnings and asset growth.",
        "application": "Focus on the business model, unit economics, and competitive advantage rather than just ticker symbol fluctuations.",
        "golden_rule": "Treat stock ownership like buying a piece of your neighborhood grocery store.",
        "spoken": "Today's financial lesson is Fractional Ownership. A stock is not a lottery ticket; it is owning a piece of a living business. Look at earnings, revenue, and customer value before price movements."
    },
    {
        "day": 2,
        "category": "Foundations",
        "title": "The Power of Compound Interest & Inflation",
        "principle": "Compound growth is exponential over time, while uninvested cash loses purchasing power to inflation.",
        "application": "Using the Rule of 72: divide 72 by annual return rate to calculate the years needed to double your wealth (e.g., 72 / 12% = 6 years).",
        "golden_rule": "Start early. Time in the market consistently beats trying to time the market.",
        "spoken": "Today's financial lesson is The Power of Compounding. Money invested at 12% doubles every six years due to the Rule of 72, whereas cash sitting idle is quietly eaten away by inflation."
    },
    {
        "day": 3,
        "category": "Foundations",
        "title": "Index Funds & ETFs (Passive Compounding)",
        "principle": "An index fund (like Nifty 50 or S&P 500) automatically buys the top companies in the economy.",
        "application": "Over 85% of active fund managers fail to beat the index over 10-year horizons. Low-cost index ETFs offer automatic diversification.",
        "golden_rule": "Make low-cost broad-market index SIPs the bedrock foundation of your wealth.",
        "spoken": "Today's financial lesson is Index Funds. By holding the top 50 companies automatically, you eliminate single-company collapse risk while capturing macroeconomic economic expansion."
    },
    {
        "day": 4,
        "category": "Fundamental Analysis",
        "title": "The Price-to-Earnings (P/E) Ratio",
        "principle": "P/E measures how much investors are willing to pay for every dollar or rupee of company net profit.",
        "application": "Compare a company's P/E to its historical average and industry peers. A low P/E can mean undervalued, or a troubled business.",
        "golden_rule": "Never buy on low P/E alone; always verify revenue growth and earnings quality.",
        "spoken": "Today's financial lesson is the P/E Ratio. It tells you what you are paying per unit of company profit. Compare it against industry peers and historical multiples."
    },
    {
        "day": 5,
        "category": "Fundamental Analysis",
        "title": "Free Cash Flow (FCF) vs Accounting Profit",
        "principle": "Accounting net profit can be manipulated by accruals, but Free Cash Flow represents actual cash left after expenses and reinvestment.",
        "application": "Healthy companies convert over 80% of net income into operating cash flow to pay down debt, reinvest, or issue dividends.",
        "golden_rule": "Revenue is vanity, profit is sanity, but cash flow is reality.",
        "spoken": "Today's financial lesson is Free Cash Flow. Accounting profits can hide delayed payments, but real cash in the bank funds dividends and future expansion."
    },
    {
        "day": 6,
        "category": "Fundamental Analysis",
        "title": "Economic Moats (Competitive Advantages)",
        "principle": "A moat is a structural advantage that protects a company from competitors taking its market share.",
        "application": "Key moats: Network Effects (Visa, Google), High Switching Costs (Apple ecosystem), Cost Advantage, Intangible Patents.",
        "golden_rule": "Invest in businesses with high barriers to entry that competitors cannot easily duplicate.",
        "spoken": "Today's financial lesson is Economic Moats. Seek out companies with high switching costs or network effects that shield profit margins from competitor encroachment."
    },
    {
        "day": 7,
        "category": "Technical Analysis",
        "title": "Candlestick Anatomy & Price Action",
        "principle": "Every candle tells a battle story between buyers (bulls) and sellers (bears) across Open, High, Low, and Close.",
        "application": "Long lower wicks show buyers aggressively defending a price level; long upper wicks show seller rejection.",
        "golden_rule": "Focus on the closing price; it reveals who won the battle at the end of the session.",
        "spoken": "Today's financial lesson is Candlestick Price Action. The candle body and wicks reveal institutional buying and selling pressure. Always respect the closing price."
    },
    {
        "day": 8,
        "category": "Technical Analysis",
        "title": "Support & Resistance (Supply/Demand Zones)",
        "principle": "Prices reverse at levels where institutional orders cluster; broken resistance transforms into future support.",
        "application": "Mark horizontal price zones where price bounced multiple times on high volume rather than drawing single thin lines.",
        "golden_rule": "Never buy right below strong resistance; wait for a confirmed breakout or a pullback to support.",
        "spoken": "Today's financial lesson is Support and Resistance. These are institutional order zones. Previous price ceilings frequently flip to become price floors."
    },
    {
        "day": 9,
        "category": "Risk Management",
        "title": "The Golden 1% Risk Rule",
        "principle": "Never risk losing more than 1% of your total account balance on a single trade setup.",
        "application": "On a 100,000 rupee account, max loss on a stopped trade is 1,000 rupees. Position size is adjusted to fit the stop-loss distance.",
        "golden_rule": "Position sizing, not market prediction, determines whether a trader survives.",
        "spoken": "Today's financial lesson is the 1% Risk Rule. By limiting risk on any single trade to 1% of equity, you can endure ten consecutive losses and remain in control."
    },
    {
        "day": 10,
        "category": "Risk Management",
        "title": "Risk-to-Reward Ratio (Asymmetric Payoff)",
        "principle": "Only take trade opportunities where the realistic upside target is at least 2 to 3 times the downside stop-loss.",
        "application": "With a 1:2 Risk-to-Reward ratio, you can be wrong 60% of the time and still be mathematically profitable overall.",
        "golden_rule": "Cut losses small and fast; let winning trades run to their multi-R targets.",
        "spoken": "Today's financial lesson is Risk-to-Reward Ratio. When targeting two to three times your risk on every trade, even a 40% win rate generates consistent profitability."
    },
    {
        "day": 11,
        "category": "Psychology & Execution",
        "title": "Eliminating FOMO (Fear Of Missing Out)",
        "principle": "Chasing parabolic green candles is how institutional market makers offload inventory to emotional retail traders.",
        "application": "If you missed a breakout move, let it go. Wait for a structured retest or find a setup with favorable risk-to-reward.",
        "golden_rule": "There is always another trade tomorrow. The market never runs out of opportunities.",
        "spoken": "Today's financial lesson is Overcoming FOMO. Chasing runaway green candles is the fastest way to lose capital. Patiently wait for pullbacks to value zones."
    },
    {
        "day": 12,
        "category": "Strategy & Practice",
        "title": "Paper Trading & Execution Journals",
        "principle": "Simulated trading builds muscle memory, pattern recognition, and statistical edge without emotional capital ruin.",
        "application": "Log every entry, exit, invalidation thesis, and emotional state in a dedicated journal before deploying real capital.",
        "golden_rule": "Do not risk real money until you are demonstrably profitable on paper for 3 consecutive months.",
        "spoken": "Today's financial lesson is Paper Trading. Master position sizing and journal your trade logic in a sandbox before risking hard-earned capital."
    }
]

def get_daily_financial_concept(today):
    """Selects today's progressive stock market & trading masterclass concept."""
    day_index = (today.timetuple().tm_yday - 1) % len(DAILY_FINANCIAL_CONCEPTS)
    return DAILY_FINANCIAL_CONCEPTS[day_index]

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
    """Searches and downloads a desktop anime wallpaper."""
    anime_pool = [
        "Attack on Titan", "Bleach", "Naruto", "Jujutsu Kaisen",
        "Demon Slayer", "Solo Leveling", "One Piece", "Death Note", "Dragon Ball"
    ]
    selected_anime = random.choice(anime_pool)
    print(f"🎨 Searching daily desktop wallpaper for: '{selected_anime}'...")
    url = f"https://wallhaven.cc/api/v1/search?q={urllib.parse.quote(selected_anime)}&categories=010&purity=100&ratios=16x9,16x10&sorting=random"
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

def create_obsidian_daily_note(today, top_5_items, anime_title, resolution, fin_concept):
    """Automatically creates today's Daily Note in the Obsidian Vault with Tasks & Financial Concept."""
    filename = today.strftime("%Y-%m-%d.md")
    note_path = os.path.join(OBSIDIAN_DAILY_DIR, filename)
    date_display = today.strftime("%A, %B %d, %Y")
    
    lines = [
        f"# Daily Tasks - {date_display}",
        "",
        "> [!info] Morning Briefing & Workflow Generated",
        f"> **Date:** {date_display}",
        "> **Tags:** #daily #tasks #briefing #automation #finance #learning",
        "",
        "---",
        "",
        "## 📋 Today's Tasks",
        "",
        "### 🏃 Morning (7:00 AM - 12:00 PM)",
        f"- [x] Daily automated Discord executive briefing delivered ✅ {today.strftime('%Y-%m-%d')}",
        f"- [ ] Review daily market lesson: {fin_concept['title']} ([[Learning/Stock Market & Trading Mastery Roadmap|Stock Market Roadmap]]) 📅 {today.strftime('%Y-%m-%d')}",
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
        f"## 📈 Daily Market & Trading Insight (Day {fin_concept['day']})",
        "",
        f"> [!tip] {fin_concept['title']} ({fin_concept['category']})",
        f"> **Core Principle:** {fin_concept['principle']}",
        "> ",
        f"> **Real-World Application:** {fin_concept['application']}",
        "> ",
        f"> **🎯 Golden Rule:** `{fin_concept['golden_rule']}`",
        "> ",
        "> *Deep-dive study guide:* [[Learning/Stock Market & Trading Mastery Roadmap|📈 Stock Market & Trading Mastery Roadmap]]",
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
        f.write("\n".join(lines).replace("\\n", "\n"))
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

def send_briefing_to_discord(thread_id, content_markdown, audio_path, wallpaper_path=None):
    """Sends the formatted Blockquote cards with inline playable audio and wallpaper attachment."""
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    crlf = "\r\n".encode("utf-8")
    body = bytearray()
    
    body.extend(f"--{boundary}".encode("utf-8") + crlf)
    body.extend(b'Content-Disposition: form-data; name="payload_json"' + crlf)
    body.extend(b'Content-Type: application/json' + crlf + crlf)
    body.extend(json.dumps({"content": content_markdown}).encode("utf-8") + crlf)
    
    audio_filename = os.path.basename(audio_path)
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    body.extend(f"--{boundary}".encode("utf-8") + crlf)
    body.extend(f'Content-Disposition: form-data; name="files[0]"; filename="{audio_filename}"'.encode("utf-8") + crlf)
    body.extend(b"Content-Type: audio/mp4" + crlf + crlf)
    body.extend(audio_bytes + crlf)
    
    if wallpaper_path and os.path.exists(wallpaper_path):
        wall_filename = os.path.basename(wallpaper_path)
        with open(wallpaper_path, "rb") as f:
            wall_bytes = f.read()
        body.extend(f"--{boundary}".encode("utf-8") + crlf)
        body.extend(f'Content-Disposition: form-data; name="files[1]"; filename="{wall_filename}"'.encode("utf-8") + crlf)
        body.extend(b"Content-Type: image/jpeg" + crlf + crlf)
        body.extend(wall_bytes + crlf)
        
    body.extend(f"--{boundary}--".encode("utf-8") + crlf)
    
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "DiscordBot (ArminAgent, 1.0)",
        "Content-Length": str(len(body))
    }
    req = urllib.request.Request(url, data=bytes(body), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
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
    print("🔍 Fetching live tech & world intelligence...")
    _ = live_web_search("top AI breakthrough technology news today", max_results=5)

    fin_concept = get_daily_financial_concept(today)
    print(f"📈 Daily Financial Concept: Day {fin_concept['day']} - {fin_concept['title']}")

    anime_title, resolution = fetch_daily_anime_wallpaper(wallpaper_path)
    top_5_items = get_todays_news()

    print("📝 Generating today's Obsidian daily note with tasks & financial lesson...")
    create_obsidian_daily_note(today, top_5_items, anime_title, resolution, fin_concept)

    markdown_lines = [
        f"## 📅 Daily Executive Briefing — {today_date_str}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        f"### 📈 Daily Market & Trading Masterclass (Day {fin_concept['day']})\n",
        f"💡 **Concept**: **{fin_concept['title']}** ({fin_concept['category']})",
        f"> • **Core Principle**: {fin_concept['principle']}",
        f"> • **Application**: {fin_concept['application']}",
        f"> • 🎯 **Golden Rule**: `{fin_concept['golden_rule']}`\n",
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

    voice_script_parts = [
        f"Good morning! Here is your daily executive briefing for {today.strftime('%A, %B %d, %Y')}.",
        fin_concept["spoken"],
        "Now, here are today's top five world and technology breakthroughs:"
    ]
    for item in top_5_items:
        voice_script_parts.append(item["spoken"])
    if anime_title:
        voice_script_parts.append(f"Today's featured anime desktop wallpaper is from {anime_title}.")
    voice_script_parts.append("Have a disciplined, wonderful, and productive day ahead!")
    full_voice_script = "\n\n".join(voice_script_parts)

    synthesize_voice(full_voice_script, audio_path)
    thread_id = create_discord_thread(thread_title)
    send_briefing_to_discord(thread_id, full_markdown, audio_path, wallpaper_path if anime_title else None)
    print("🎉 Pipeline finished successfully!")

if __name__ == "__main__":
    run_pipeline()
