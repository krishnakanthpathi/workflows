#!/usr/bin/env python3
"""
Link Page Resolver (get_links.py)
Resolves intermediate link gates (unblockedgames.world) to final file host pages (driveseed / video-seed).
Accepts either:
  1. A direct gate URL (https://cloud.unblockedgames.world/?sid=...)
  2. A post URL with tier and episode filtering (--post URL --tier 1 --episodes 7,8 or 1-5)
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.parse
import http.cookiejar
from html import unescape

# Allow importing inspect_post when run from anywhere
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from inspect_post import inspect_post

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def resolve_gate(gate_url):
    """
    Solves unblockedgames.world 2-step challenge via POST requests in ~2s.
    Returns (driveseed_url, error_message)
    """
    m_sid = re.search(r"sid=([^&]+)", gate_url)
    if not m_sid:
        return None, "No sid parameter found in URL."
    sid = m_sid.group(1)

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Step 1: POST to cloud.unblockedgames.world/
    data1 = urllib.parse.urlencode({"_wp_http": sid}).encode("utf-8")
    req1 = urllib.request.Request("https://cloud.unblockedgames.world/", data=data1, headers={
        "User-Agent": USER_AGENT,
        "Referer": gate_url
    })
    try:
        with opener.open(req1, timeout=15) as resp1:
            html1 = resp1.read().decode("utf-8", errors="ignore")
            referer1 = resp1.geturl()
    except Exception as e:
        return None, f"Gate step 1 network error: {e}"

    m_action = re.search(r"<form id=\"landing\" method=\"POST\" [^>]*action=\"([^\"]+)\"", html1)
    m_http2 = re.search(r"name=\"_wp_http2\" value=\"([^\"]+)\"", html1)
    m_token = re.search(r"name=\"token\" value=\"([^\"]+)\"", html1)

    if not (m_action and m_http2 and m_token):
        return None, "Failed to parse step 1 verification form."

    # Step 2: POST to article page
    data2 = urllib.parse.urlencode({"_wp_http2": m_http2.group(1), "token": m_token.group(1)}).encode("utf-8")
    req2 = urllib.request.Request(m_action.group(1), data=data2, headers={
        "User-Agent": USER_AGENT,
        "Referer": referer1
    })
    try:
        with opener.open(req2, timeout=15) as resp2:
            html2 = resp2.read().decode("utf-8", errors="ignore")
            referer2 = resp2.geturl()
    except Exception as e:
        return None, f"Gate step 2 network error: {e}"

    # Step 3: Extract cookie call and target URL
    m_s343 = re.search(r"s_343\(\s*[\'\"]([^\'\"]+)[\'\"]\s*,\s*[\'\"]([^\'\"]+)[\'\"]", html2)
    if not m_s343:
        return None, "Verification cookie token not found in step 2."

    c_name, c_val = m_s343.group(1), m_s343.group(2)
    target_go_url = f"https://cloud.unblockedgames.world/?go={c_name}"

    req3 = urllib.request.Request(target_go_url, headers={
        "User-Agent": USER_AGENT,
        "Referer": referer2,
        "Cookie": f"{c_name}={c_val}"
    })
    try:
        with opener.open(req3, timeout=15) as resp3:
            html3 = resp3.read().decode("utf-8", errors="ignore")
            final_url = resp3.geturl()
    except Exception as e:
        return None, f"Gate step 3 network error: {e}"

    m_meta = re.search(r"url=([^\"\'\s>]+)", html3)
    target = m_meta.group(1) if m_meta else final_url
    return target, None

def resolve_host_page(target_r_url):
    """
    Given the driveseed redirect URL (https://driveseed.org/r?...),
    extracts the final file landing page and download options.
    """
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    req = urllib.request.Request(target_r_url, headers={
        "User-Agent": USER_AGENT,
        "Referer": "https://cloud.unblockedgames.world/"
    })
    try:
        with opener.open(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return None, f"DriveSeed network error: {e}"

    m_loc = re.search(r"window\.location\.replace\([\'\"]([^\'\"]+)[\'\"]\)", html)
    if not m_loc:
        return None, "Could not extract final file path from redirect."

    file_path = m_loc.group(1)
    file_page_url = urllib.parse.urljoin("https://driveseed.org", file_path)

    # Fetch file page
    req_file = urllib.request.Request(file_page_url, headers={
        "User-Agent": USER_AGENT,
        "Referer": target_r_url
    })
    try:
        with opener.open(req_file, timeout=15) as resp_file:
            html_file = resp_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return None, f"Error fetching file page: {e}"

    instant_download = None
    telegram_url = None
    telegram_tg_proto = None
    resume_cloud = None

    for a in re.findall(r"<a[^>]+href=[\'\"]([^\'\"]+)[\'\"][^>]*>(.*?)</a>", html_file, re.DOTALL):
        txt = re.sub(r"<[^>]+>", "", a[1]).strip().lower()
        href = unescape(a[0])
        if "instant download" in txt or "instant" in txt:
            instant_download = href
        elif "telegram" in txt and ("seedtg" in href or "start=" in href or "bot=" in href):
            telegram_url = href
            # extract tg://
            parsed = urllib.parse.urlparse(href)
            params = urllib.parse.parse_qs(parsed.query)
            bot = params.get("bot", ["seedcdn_bot"])[0]
            start = params.get("start", [""])[0]
            telegram_tg_proto = f"tg://resolve?domain={bot}&start={start}"
        elif "resume cloud" in txt:
            resume_cloud = urllib.parse.urljoin("https://driveseed.org", href)

    return {
        "file_page": file_page_url,
        "instant_download": instant_download,
        "telegram_link": telegram_url,
        "telegram_tg": telegram_tg_proto,
        "resume_cloud": resume_cloud
    }, None

def resolve_single_link(gate_url, label="Episode"):
    target_r_url, err = resolve_gate(gate_url)
    if err:
        return {"label": label, "gate_url": gate_url, "error": err}

    host_info, err2 = resolve_host_page(target_r_url)
    if err2:
        return {"label": label, "gate_url": gate_url, "redirect_url": target_r_url, "error": err2}

    return {
        "label": label,
        "gate_url": gate_url,
        "file_page": host_info["file_page"],
        "instant_download": host_info["instant_download"],
        "telegram_link": host_info["telegram_link"],
        "telegram_tg": host_info["telegram_tg"],
        "resume_cloud": host_info["resume_cloud"]
    }

def parse_episode_filter(filter_str, max_count):
    selected = set()
    parts = filter_str.split(",")
    for p in parts:
        p = p.strip()
        if "-" in p:
            start, end = p.split("-", 1)
            if start.isdigit() and end.isdigit():
                for num in range(int(start), int(end) + 1):
                    if 1 <= num <= max_count:
                        selected.add(num)
        elif p.isdigit():
            num = int(p)
            if 1 <= num <= max_count:
                selected.add(num)
    return selected

def main():
    parser = argparse.ArgumentParser(description="Resolve link gates to final download and Telegram pages.")
    parser.add_argument("url", nargs="?", help="Direct gate URL (https://cloud.unblockedgames.world/?sid=...)")
    parser.add_argument("--post", help="UHDMovies post URL to inspect and resolve from")
    parser.add_argument("--tier", type=int, default=1, help="Tier number to select (default: 1)")
    parser.add_argument("--episodes", help="Episode numbers to resolve (e.g. '7', '1-5', '6,7,8' or 'all')")
    parser.add_argument("--json", action="store_true", help="Output results as clean JSON")

    args = parser.parse_args()

    results = []

    if args.url:
        if not args.json:
            print(f"\n[*] Resolving Gate: {args.url[:60]}...")
        info = resolve_single_link(args.url)
        results.append(info)
        if not args.json:
            if "file_page" in info:
                print(f"    ├─ File Page : {info['file_page']}")
                print(f"    ├─ Telegram  : {info['telegram_link'] or 'N/A'}")
                if info.get('telegram_tg'):
                    print(f"    ├─ Tg Proto  : {info['telegram_tg']}")
                print(f"    ├─ Instant   : {info['instant_download'] or 'N/A'}")
                print(f"    └─ Cloud     : {info['resume_cloud'] or 'N/A'}\n")
            else:
                print(f"    [!] Error: {info.get('error')}\n")

    elif args.post:
        post_data = inspect_post(args.post)
        if not post_data["tiers"]:
            print("[-] No quality tiers found on this post.", file=sys.stderr)
            sys.exit(1)

        tier_idx = args.tier - 1
        if tier_idx < 0 or tier_idx >= len(post_data["tiers"]):
            print(f"[-] Invalid tier {args.tier}. Available: 1 to {len(post_data['tiers'])}", file=sys.stderr)
            sys.exit(1)

        selected_tier = post_data["tiers"][tier_idx]
        total_ep = len(selected_tier["episodes"])
        if not args.json:
            print(f"\n=======================================================")
            print(f" 🎬 Resolving for: {selected_tier['header']}")
            print(f" 📊 Tier {args.tier} | Total: {total_ep} items")
            print(f"=======================================================")

        filter_set = None
        if args.episodes and args.episodes.lower() != "all":
            filter_set = parse_episode_filter(args.episodes, total_ep)

        for idx, ep in enumerate(selected_tier["episodes"], 1):
            if filter_set is not None and idx not in filter_set:
                continue

            if not args.json:
                print(f"\n[*] [{idx}/{total_ep}] Resolving {ep['label']}...")
            info = resolve_single_link(ep["url"], label=ep["label"])
            results.append(info)
            if not args.json and "file_page" in info:
                print(f"    ├─ File Page : {info['file_page']}")
                print(f"    ├─ Telegram  : {info['telegram_link'] or 'N/A'}")
                if info.get('telegram_tg'):
                    print(f"    ├─ Tg Proto  : {info['telegram_tg']}")
                print(f"    ├─ Instant   : {info['instant_download'] or 'N/A'}")
                print(f"    └─ Cloud     : {info['resume_cloud'] or 'N/A'}")
    else:
        parser.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
