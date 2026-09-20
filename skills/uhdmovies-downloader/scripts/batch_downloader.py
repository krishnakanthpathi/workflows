#!/usr/bin/env python3
"""
Batch Downloader Engine
Orchestrates link gate resolution, Instant Download probe, and Telegram bot fallback.
"""

import sys
import os
import time
import urllib.request
import argparse

# Allow local imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from inspect_post import inspect_post
from get_links import resolve_single_link, parse_episode_filter
from telegram import dispatch_telegram

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def verify_instant_download(instant_url):
    """Checks if instant download URL serves an active stream without 404/500."""
    if not instant_url:
        return None, False
    try:
        req = urllib.request.Request(instant_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status in [200, 302]:
                return instant_url, True
        return None, False
    except Exception:
        return None, False

def process_batch(post_url, tier=1, episodes_filter=None, delay=2):
    print("================================================================================")
    print(" 🚀 BATCH DOWNLOAD & DISPATCH ENGINE")
    print("================================================================================")

    post_data = inspect_post(post_url)
    if not post_data["tiers"]:
        print("[-] No download tiers found on post.")
        return

    tier_idx = tier - 1
    if tier_idx < 0 or tier_idx >= len(post_data["tiers"]):
        print(f"[-] Invalid tier {tier}. Max: {len(post_data['tiers'])}")
        return

    selected_tier = post_data["tiers"][tier_idx]
    ep_list = selected_tier["episodes"]
    total = len(ep_list)

    filter_set = None
    if episodes_filter and episodes_filter.lower() != "all":
        filter_set = parse_episode_filter(episodes_filter, total)

    print(f"🎬 Title   : {post_data['title']}")
    print(f"📦 Release : {selected_tier['header']} ({selected_tier['size']})")
    print(f"🎯 Target  : {len(filter_set) if filter_set else total} of {total} episodes\n")

    for idx, ep in enumerate(ep_list, 1):
        if filter_set is not None and idx not in filter_set:
            continue

        label = ep["label"]
        gate_url = ep["url"]

        print(f"--------------------------------------------------------------------------------")
        print(f"[*] [{idx}/{total}] Processing: {label}")
        print(f"    Resolving gate: {gate_url[:60]}...")
        info = resolve_single_link(gate_url, label=label)

        if "error" in info:
            print(f"    [!] Gate resolution failed: {info['error']}")
            continue

        print(f"    [+] Link Page: {info['file_page']}")

        # Test Instant Download
        direct_url, alive = verify_instant_download(info["instant_download"])
        if alive:
            print(f"    [+] Instant Download available: {direct_url}")
        else:
            print("    [-] Instant Download unavailable/404. Falling back to Telegram...")
            if info.get("telegram_link"):
                dispatch_telegram(info["telegram_link"], label=label)
            else:
                print("    [!] Telegram fallback link not present.")

        time.sleep(delay)

def main():
    parser = argparse.ArgumentParser(description="Batch download and Telegram file dispatcher.")
    parser.add_argument("post_url", help="UHDMovies post URL")
    parser.add_argument("--tier", type=int, default=1, help="Tier index (default: 1)")
    parser.add_argument("--episodes", help="Episode range (e.g. '7', '1-5', '6,7,8' or 'all')")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests in seconds")

    args = parser.parse_args()
    process_batch(args.post_url, tier=args.tier, episodes_filter=args.episodes, delay=args.delay)

if __name__ == "__main__":
    main()
