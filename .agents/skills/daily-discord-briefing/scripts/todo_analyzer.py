#!/usr/bin/env python3
"""
Todos & Project Backlog Analyzer
- Scans /Users/krishnakanth/Documents/Obsidian Vault/Todos/*.md
- Extracts active pending tasks (- [ ])
- Generates high-impact daily recommendations and milestone suggestions
"""

import os
import re
from pathlib import Path

TODOS_DIR = Path("/Users/krishnakanth/Documents/Obsidian Vault/Todos")

def analyze_todos():
    """Parses active tasks from the Todos directory."""
    if not TODOS_DIR.exists():
        return []

    project_tasks = {}
    for md_file in TODOS_DIR.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_section = "General Backlog"
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("### "):
                current_section = line_str.replace("### ", "").split("(")[0].strip()
                # Clean emoji
                current_section = re.sub(r"^[^\w\s]+", "", current_section).strip()
            elif line_str.startswith("## "):
                current_section = line_str.replace("## ", "").split("(")[0].strip()
                current_section = re.sub(r"^[^\w\s]+", "", current_section).strip()
            elif line_str.startswith("- [ ]"):
                task_text = re.sub(r"- \[ \]\s*", "", line_str)
                task_text = re.sub(r"📅.*", "", task_text).strip()
                if current_section not in project_tasks:
                    project_tasks[current_section] = []
                project_tasks[current_section].append(task_text)

    return project_tasks

def generate_strategic_recommendations(project_tasks):
    """Synthesizes high-signal daily recommendations based on active pending tasks."""
    recommendations = []

    # Check for VidyaSetu / Vidyanshu
    vidya_tasks = []
    for sec, tasks in project_tasks.items():
        if any(k in sec.lower() for k in ["vidya", "vidyanshu"]):
            vidya_tasks.extend(tasks)
    if vidya_tasks:
        recommendations.append({
            "area": "🏛️ VidyaSetu AI Engine (P1)",
            "action": vidya_tasks[0],
            "impact": "Unlocks Devanagari text processing and textbook exam generation pipeline."
        })

    # Check for Obsidian Semantizer
    semantizer_tasks = []
    for sec, tasks in project_tasks.items():
        if "semantizer" in sec.lower() or "graph" in sec.lower():
            semantizer_tasks.extend(tasks)
    if semantizer_tasks:
        recommendations.append({
            "area": "🧠 Obsidian Semantizer & Graph Engine (P1)",
            "action": semantizer_tasks[0],
            "impact": "Builds foundation for hybrid search (Vector + BM25 + Graph) across the vault."
        })

    # Check for Android Edge Sentinel
    edge_tasks = []
    for sec, tasks in project_tasks.items():
        if "android" in sec.lower() or "sentinel" in sec.lower() or "edge" in sec.lower():
            edge_tasks.extend(tasks)
    if edge_tasks:
        recommendations.append({
            "area": "📱 Android Edge Sentinel",
            "action": edge_tasks[0],
            "impact": "Expands on-device hardware telemetry and power alert mesh."
        })

    # Check for System Design / Career
    career_tasks = []
    for sec, tasks in project_tasks.items():
        if any(k in sec.lower() for k in ["system design", "learning", "career", "dsa", "milestones"]):
            career_tasks.extend(tasks)
    if career_tasks:
        recommendations.append({
            "area": "📚 System Design & Technical Mastery",
            "action": career_tasks[0],
            "impact": "Maintains daily compounding toward senior engineering and architecture mastery."
        })

    return recommendations

def format_recommendations_obsidian(recommendations):
    """Formats recommendations for Obsidian Daily Note."""
    if not recommendations:
        return "> *No pending backlog recommendations found.*"

    lines = [
        "> [!tip] 🎯 High-Impact Focus & Backlog Recommendations",
        "> Derived dynamically from [[Todos/Todos|Master To-Do Hub]] and active project roadmaps:",
        "> "
    ]
    for r in recommendations:
        lines.append(f"> - **{r['area']}**: {r['action']}")
        lines.append(f">   *Impact:* {r['impact']}")
        lines.append("> ")
    return "\n".join(lines[:-1])

def format_recommendations_discord(recommendations):
    """Formats 1-2 key recommendations for Discord."""
    if not recommendations:
        return ""
    lines = ["🎯 **Today's Strategic Focus**:"]
    for r in recommendations[:2]:
        lines.append(f"> • **{r['area'].split('(')[0].strip()}**: {r['action']}")
    return "\n".join(lines)

if __name__ == "__main__":
    tasks = analyze_todos()
    recs = generate_strategic_recommendations(tasks)
    print("Analyzed Recommendations:")
    print(format_recommendations_obsidian(recs))
    print("\nDiscord Format:")
    print(format_recommendations_discord(recs))
