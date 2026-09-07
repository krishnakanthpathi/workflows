#!/usr/bin/env python3
"""
Dynamic Learning Roadmap Manager, Sub-Note Generator & Task Verification Engine
- Inspects Obsidian Vault 'Learning/Stock Market & Trading Mastery Roadmap.md'
- Identifies the next active curriculum milestone (- [ ])
- Checks whether previous day's to-dos were completed before advancing
- If incomplete, provides catch-up guidance and retains current milestone
- Generates comprehensive, zero-jargon Obsidian sub-notes in /Learning/
- Strictly adheres to Obsidian Vault rules.md
"""

import os
import re
import datetime
from pathlib import Path

VAULT_DIR = Path("/Users/krishnakanth/Documents/Obsidian Vault")
ROADMAP_FILE = VAULT_DIR / "Learning" / "Stock Market & Trading Mastery Roadmap.md"
LEARNING_DIR = VAULT_DIR / "Learning"
TODOS_FILE = VAULT_DIR / "Todos" / "Todos.md"

CURRICULUM_DETAILS = {
    "Foundations": {
        "day": 1,
        "filename": "Day 01 - Stock Market Foundations",
        "title": "Day 01: Stock Market Foundations & Fractional Ownership",
        "category": "Phase 1: Market Fundamentals & Mechanics",
        "principle": "Buying a stock is purchasing fractional ownership in a living, cash-generating business, not just a flickering lottery ticket.",
        "application": "Switch from a consumer mindset to an owner mindset by observing public companies behind everyday products and holding for long-term growth.",
        "golden_rule": "Never invest in something you cannot explain to a 10-year-old.",
        "spoken": "Today marks Day 1 of your Stock Market journey with Market Foundations. Learn how buying shares grants fractional business ownership and cash dividends.",
        "analogy": "The Coffee Shop Deal: If you contribute 30% to a cafe's setup, you own 30% of its cash profits (dividends) and benefit as its valuation grows from 1 lakh to 10 lakhs.",
        "jargon": [
            ("Stock / Share", "A unit of legal equity ownership in a corporation.", "One slice of an 8-slice pizza."),
            ("Dividend", "Direct cash profit distributed from company earnings to shareholders.", "Your share of the coffee shop profits handed to you at year end."),
            ("Capital Appreciation", "The rise in the market value of your shares as the business expands.", "The shop valuation multiplying over time."),
            ("Demat Account", "A secure digital vault storing your shares electronically with CDSL/NSDL.", "A digital bank locker for share certificates.")
        ],
        "todos": [
            ("Read Day 01 Study Guide", "Read through [[Learning/Day 01 - Stock Market Foundations]] to build core intuition."),
            ("The Room Audit", "Identify 3 everyday brands you use and look up who owns them to switch to an owner mindset."),
            ("5Y Chart Observation", "Search Tata Motors or Apple on Google/TradingView and observe multi-year value growth vs daily noise."),
            ("The Coffee Shop Teach-Back", "Explain the concept of shares, dividends, and growth in 2 minutes to a friend or in your journal.")
        ]
    },
    "Market Participants": {
        "day": 2,
        "filename": "Day 02 - Market Participants",
        "title": "Day 02: Market Participants — Retail, DIIs, FIIs & Market Makers",
        "category": "Phase 1: Market Fundamentals & Mechanics",
        "principle": "Financial markets are driven by institutional capital flows (FIIs & DIIs) that command 80%+ of liquidity and establish macro trends.",
        "application": "Track institutional accumulation via daily FII/DII net flow reports and high-volume breakout zones rather than predicting reversals.",
        "golden_rule": "Never swim against institutional whales; align your entries with smart money accumulation.",
        "spoken": "Today's financial lesson covers Market Participants. Learn why retail traders must track institutional smart money rather than fighting it.",
        "analogy": "The Ocean Ecosystem: In the stock market ocean, Retail traders are small fish, DIIs and FIIs are giant blue whales, and Market Makers are the currents.",
        "jargon": [
            ("Retail Trader", "Individual investors like you and me trading our personal money from mobile apps.", "A regular customer shopping at the local farmers market."),
            ("DII (Domestic Institutional Investor)", "Big Indian financial institutions: Mutual Funds (HDFC, SBI), Insurance giants (LIC), Pension Funds.", "Giant local commercial buying clubs with thousands of members pooling cash."),
            ("FII / FPI (Foreign Institutional Investor)", "Massive foreign hedge funds, sovereign wealth funds, and global asset managers investing into India.", "International investment consortiums bringing billions of dollars across borders."),
            ("Market Maker / Prop Desk", "High-frequency firms and liquidity providers quoting both buy and sell prices continuously.", "The currency exchange kiosk at the airport guaranteeing you can always swap currencies instantly.")
        ],
        "todos": [
            ("Read Day 02 Study Guide", "Review [[Learning/Day 02 - Market Participants]] on institutional capital vs retail."),
            ("Check FII / DII Flow", "Check today's institutional net cash flow on NSE India or Moneycontrol."),
            ("Smart Money Observation", "Identify how institutional block deals impact volume spikes on charts.")
        ]
    },
    "Order Types": {
        "day": 3,
        "filename": "Day 03 - Order Types Demystified",
        "title": "Day 03: Order Types Demystified — Market, Limit, SL, SL-M & GTT",
        "category": "Phase 1: Market Fundamentals & Mechanics",
        "principle": "Order execution speed versus price precision: Market orders guarantee immediate execution, while Limit and GTT orders guarantee price control.",
        "application": "Always use Limit Orders for buying illiquid stocks and GTT (Good Till Triggered) for automated long-term stop-loss and profit targets.",
        "golden_rule": "Never enter volatile markets with market orders; dictate your entry price with limit orders.",
        "spoken": "Today's lesson explores Order Types. Master the difference between immediate market fills and disciplined limit and stop-loss execution.",
        "analogy": "Ordering at a Restaurant vs Auction: Market orders are saying 'Give me whatever food is ready now at any price'. Limit orders are saying 'I will only pay ₹200 for this dish, not a rupee more.'",
        "jargon": [
            ("Market Order", "Executes immediately at the best available current price.", "Buying the item at whatever price the cashier rings up right now."),
            ("Limit Order", "Executes ONLY at your specified price or better.", "Setting a strict price cap on an auction bidding paddle."),
            ("Stop-Loss (SL)", "An automatic conditional trigger order that exits a trade to prevent catastrophic loss.", "An emergency parachute cord that pulls open automatically if you fall below 1,000 feet."),
            ("GTT (Good Till Triggered)", "A persistent order that stays active for up to 1 year until your target price is hit.", "A standing bank instruction that executes whenever conditions are met.")
        ],
        "todos": [
            ("Read Day 03 Study Guide", "Review [[Learning/Day 03 - Order Types Demystified]] on Limit vs Market orders."),
            ("Explore Order Tickets", "Open your broker app (or TradingView demo) and locate Market, Limit, SL, and GTT screens."),
            ("Draft a GTT Strategy", "Define entry and stop-loss levels on a watchlist stock using GTT.")
        ]
    },
    "Market Indices & ETFs": {
        "day": 4,
        "filename": "Day 04 - Market Indices and ETFs",
        "title": "Day 04: Market Indices & ETFs — Nifty 50, Sensex, S&P 500 & Index Investing",
        "category": "Phase 1: Market Fundamentals & Mechanics",
        "principle": "An index represents a weighted basket of the nation's top corporations, reflecting overall economic expansion while eliminating single-company bankruptcy risk.",
        "application": "Automate monthly SIP investments into low-cost Nifty 50 and S&P 500 index ETFs to capture market return with near-zero expense ratio.",
        "golden_rule": "Owning the entire market basket beats picking individual stocks for 90% of long-term investors.",
        "spoken": "Today's lesson covers Market Indices and ETFs. Understand why owning the top 50 companies through index investing beats 90% of stock pickers.",
        "analogy": "The National All-Star Sports Team: Instead of betting on one cricket batsman, you bet on the entire World Cup winning squad. If one underperforms, others score runs.",
        "jargon": [
            ("Index", "A mathematical benchmark tracking the performance of top companies (e.g. Nifty 50 = top 50 Indian companies).", "The average class test score of the top 50 students in school."),
            ("ETF (Exchange Traded Fund)", "A basket of stocks tracking an index that trades on exchanges just like a single share.", "A fruit basket containing apple, orange, and mango that you can buy as a single item."),
            ("Sensex", "The benchmark index of Bombay Stock Exchange (BSE) tracking 30 established companies.", "The heritage economic barometer of Indian industry."),
            ("Nifty 50", "The flagship index of the National Stock Exchange (NSE) tracking 50 diverse large-cap leaders.", "The modern engine tracking India's economic growth.")
        ],
        "todos": [
            ("Read Day 04 Study Guide", "Review [[Learning/Day 04 - Market Indices and ETFs]] on index investing."),
            ("Compare Index Returns", "Compare Nifty 50 vs S&P 500 5-year rolling returns."),
            ("Expense Ratio Audit", "Look up expense ratios of 2 popular index funds (e.g., UTI Nifty 50, Navi Nifty 50).")
        ]
    },
    "Power of Compounding": {
        "day": 5,
        "filename": "Day 05 - Power of Compounding and Inflation",
        "title": "Day 05: The Power of Compounding & Inflation — The Rule of 72 & The Silent Tax",
        "category": "Phase 1: Market Fundamentals & Mechanics",
        "principle": "Inflation silently degrades uninvested cash purchasing power, while compound interest produces exponential capital growth over multi-decade horizons.",
        "application": "Use the Rule of 72 to calculate doubling periods: At 12% equity CAGR, your capital doubles every 6 years.",
        "golden_rule": "Compound interest is the 8th wonder of the world; he who understands it, earns it; he who doesn't, pays it.",
        "spoken": "Today's lesson focuses on Compounding and Inflation. Learn how the Rule of 72 turns disciplined investing into generational wealth.",
        "analogy": "The Snowball Rolling Downhill: At first it picks up tiny flakes, but as its surface area expands, every single roll collects exponentially more snow than the last.",
        "jargon": [
            ("CAGR", "Compound Annual Growth Rate — the steady smoothed annual growth rate of an investment.", "The consistent speed a marathon runner maintains over 42 kilometers."),
            ("Inflation", "The steady increase in prices over time that reduces what a rupee can buy.", "A slow invisible leak in your car's tire pressure."),
            ("Rule of 72", "A fast shortcut: Divide 72 by the annual return rate to find how many years it takes money to double.", "At 12% return, 72 ÷ 12 = 6 years to double."),
            ("Real Return", "Nominal return minus inflation rate (e.g. 12% return - 6% inflation = 6% real purchasing power growth).", "Your actual net speed against a headwind.")
        ],
        "todos": [
            ("Read Day 05 Study Guide", "Review [[Learning/Day 05 - Power of Compounding and Inflation]] on Rule of 72."),
            ("Rule of 72 Calculations", "Calculate doubling periods for 7% (bank FD/inflation) vs 12% (equity index)."),
            ("SIP Projection", "Run a 20-year compound interest calculation on a monthly ₹5,000 SIP.")
        ]
    }
}

def parse_next_curriculum_item():
    """Reads the roadmap file and returns the first unchecked item."""
    if not ROADMAP_FILE.exists():
        return None, None, None, 1

    with open(ROADMAP_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_phase = "Phase 1: Market Fundamentals & Mechanics"
    completed_count = 0
    next_item = None
    line_idx = -1

    for i, line in enumerate(lines):
        if line.startswith("### "):
            current_phase = line.strip().replace("### ", "").split("(")[0].strip()
        if "- [x]" in line:
            completed_count += 1
        elif "- [ ]" in line and next_item is None:
            next_item = line.strip()
            line_idx = i

    return current_phase, next_item, line_idx, completed_count + 1

def check_day_completion(day_num):
    """
    Checks if the tasks and to-dos for a given day are completed.
    Returns: (is_completed, pending_todos, note_path)
    """
    pattern = f"Day {day_num:02d} - *.md"
    matches = list(LEARNING_DIR.glob(pattern))
    if not matches:
        matches = list(LEARNING_DIR.glob(f"Day {day_num:02d}*.md"))

    if not matches:
        return True, [], None

    note_path = matches[0]
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    pending_todos = []
    for line in content.splitlines():
        line_s = line.strip()
        if line_s.startswith("- [ ]"):
            task_text = re.sub(r"^- \[ \]\s*", "", line_s)
            task_text = re.sub(r"📅.*", "", task_text).strip()
            clean_task = re.sub(r"\*\*([^\*]+)\*\*", r"\1", task_text)
            pending_todos.append(clean_task)

    is_completed = (len(pending_todos) == 0)
    return is_completed, pending_todos, note_path

def generate_study_note(day_num, title, category, principle, application, golden_rule, analogy, jargon, note_filename, todos=None):
    """Generates a dedicated Markdown note in /Learning/ conforming strictly to rules.md."""
    today = datetime.datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    note_path = LEARNING_DIR / f"{note_filename}.md"

    if note_path.exists():
        return note_path

    jargon_rows = []
    for term, meaning, ana in jargon:
        jargon_rows.append(f"| **{term}** | {meaning} | {ana} |")
    jargon_table = "\n".join(jargon_rows)

    todos_section = ""
    if todos:
        todo_rows = []
        for t_title, t_desc in todos:
            todo_rows.append(f"- [ ] **{t_title}:** {t_desc} 📅 {today_str}")
        todos_section = f"""---

## 🎯 4. Practical To-Dos & Action Items

{chr(10).join(todo_rows)}
"""

    rule_num = "5" if todos else "4"
    links_num = "6" if todos else "5"

    content = f"""---
title: "{title}"
date: {today_str}
tags:
  - finance
  - stock-market
  - learning
  - day-{day_num:02d}
  - roadmap
status: in-progress
version: 1.0.0
---

# 📈 {title}

> [!abstract] Executive Summary
> {principle}

---

## 💡 1. Everyday Analogy: {analogy.split(':')[0]}

{analogy}

---

## 🏛️ 2. Core Concepts & Practical Application

### 🎯 Key Principle
> [!tip] First-Principles Takeaway
> **{principle}**

### 🔧 Real-World Application
{application}

---

## 📖 3. Jargon Buster: Plain-English Translations

| Concept | What It Actually Means | Everyday Real-World Analogy |
| :--- | :--- | :--- |
{jargon_table}

{todos_section}---

## 🎯 {rule_num}. The Golden Rule

> [!important] Golden Rule of Day {day_num:02d}
> `{golden_rule}`

---

## 🔗 {links_num}. Related Notes & Next Steps
- [[Learning/Stock Market & Trading Mastery Roadmap|📈 Stock Market & Trading Mastery Roadmap]]
- [[Todos/Todos|📝 Master To-Do Hub]]
- [[Daily/{today_str}|📅 Today's Daily Note ({today_str})]]
"""
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Generated learning sub-note: {note_path}")
    return note_path

def get_next_lesson_and_advance(dry_run=False):
    """
    Identifies the active roadmap item, verifies whether the previous day's
    tasks were completed, and only advances if all to-dos are checked off.
    Otherwise, retains the current lesson with rollover recommendations.
    """
    phase, raw_item, line_idx, day_num = parse_next_curriculum_item()
    if not raw_item:
        print("ℹ️ All roadmap items are currently checked or roadmap file missing.")
        return CURRICULUM_DETAILS["Foundations"]

    # Match topic
    matched_key = None
    for key in CURRICULUM_DETAILS:
        if key.lower() in raw_item.lower():
            matched_key = key
            break

    if matched_key:
        info = dict(CURRICULUM_DETAILS[matched_key])
    else:
        clean_title = re.sub(r"- \[[ x]\]\s*", "", raw_item)
        clean_title = re.sub(r"📅.*", "", clean_title).strip()
        clean_title = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", clean_title)
        info = {
            "day": day_num,
            "filename": f"Day {day_num:02d} - {clean_title[:30].strip()}",
            "title": f"Day {day_num:02d}: {clean_title}",
            "category": phase,
            "principle": f"Core principles governing {clean_title} in financial markets.",
            "application": f"Apply disciplined analysis and risk management when encountering {clean_title}.",
            "golden_rule": f"Always master {clean_title} before risking capital.",
            "spoken": f"Today's financial lesson covers {clean_title}.",
            "analogy": f"Foundations of {clean_title}: Essential building block for disciplined market participation.",
            "jargon": [(clean_title, "Key financial concept in roadmap.", "Essential trading building block.")],
            "todos": [("Study Topic", f"Review and master {clean_title}.")]
        }

    current_day = info["day"]
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    note_filename = info["filename"]
    note_path = LEARNING_DIR / f"{note_filename}.md"
    wikilink = f"[[Learning/{note_filename}|{info['title']}]]"
    info["note_wikilink"] = wikilink
    info["note_path"] = str(note_path)

    # Check previous day completion if current_day > 1
    if current_day > 1:
        prev_day = current_day - 1
        is_completed, pending_todos, prev_note_path = check_day_completion(prev_day)
        if not is_completed:
            print(f"⚠️ Day {prev_day:02d} has {len(pending_todos)} uncompleted to-dos! Rolling over...")
            prev_info = None
            for k, v in CURRICULUM_DETAILS.items():
                if v["day"] == prev_day:
                    prev_info = dict(v)
                    break
            if not prev_info:
                prev_info = info

            prev_info["rollover"] = True
            prev_info["pending_todos"] = pending_todos
            prev_info["note_wikilink"] = f"[[Learning/{prev_info['filename']}|{prev_info['title']}]]"
            prev_info["note_path"] = str(LEARNING_DIR / f"{prev_info['filename']}.md")
            prev_info["recommendation"] = (
                f"You have {len(pending_todos)} pending to-do(s) from Day {prev_day:02d}: "
                f"{'; '.join(pending_todos[:2])}. Focus on mastering these practical exercises today before advancing to Day {current_day:02d}."
            )
            return prev_info

    if not dry_run:
        generate_study_note(
            day_num=info["day"],
            title=info["title"],
            category=info["category"],
            principle=info["principle"],
            application=info["application"],
            golden_rule=info["golden_rule"],
            analogy=info["analogy"],
            jargon=info["jargon"],
            note_filename=note_filename,
            todos=info.get("todos")
        )

        # Tick off previous day in roadmap if verified complete
        if current_day > 1:
            with open(ROADMAP_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            prev_day_str = f"Day {current_day - 1:02d}"
            for idx, l in enumerate(lines):
                if prev_day_str in l and "- [ ]" in l:
                    lines[idx] = re.sub(r"^- \[ \]", "- [x]", l).rstrip() + f" ✅ {today_str}\n"
                    print(f"✅ Verified & ticked completed roadmap milestone: Day {current_day - 1:02d}")
                    with open(ROADMAP_FILE, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    break

    info["rollover"] = False
    return info

if __name__ == "__main__":
    print("Testing Roadmap Manager...")
    info = get_next_lesson_and_advance(dry_run=True)
    print("\nActive Lesson Info (Dry Run):")
    print(info)
