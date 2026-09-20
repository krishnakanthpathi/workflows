#!/usr/bin/env python3
"""
Post Inspector Tool
Inspects any post URL to extract releases, quality tiers, file sizes, and episode links.
"""

import sys
import re
import json
import urllib.request
import urllib.parse
from html import unescape

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def inspect_post(post_url):
    html = fetch_html(post_url)
    
    title_m = re.search(r"<h1[^>]*class=[\"'][^\"']*entry-title[^\"']*[\"'][^>]*>(.*?)</h1>", html, re.DOTALL)
    page_title = unescape(re.sub(r"<[^>]+>", "", title_m.group(1)).strip()) if title_m else "Unknown Title"

    m_body = re.search(r"entry-content\">(.*?)<div\s+class=\"(?:gridlove|comments|sharedaddy)", html, re.DOTALL)
    content = m_body.group(1) if m_body else html

    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, re.DOTALL)
    tiers = []

    for i, p in enumerate(paragraphs):
        if "sid=" in p and ("episode" in p.lower() or "download" in p.lower() or "zip" in p.lower() or "pack" in p.lower()):
            episodes_raw = re.findall(r"<a[^>]*href=[\"']([^\"']*sid=[^\"']+)[\"'][^>]*>(.*?)</a>", p, re.DOTALL)
            
            episode_list = []
            for href, label in episodes_raw:
                clean_lbl = re.sub(r"<[^>]+>", "", label).strip()
                if clean_lbl.lower() not in ["uhdmovies", "1080p uhd"]:
                    episode_list.append({
                        "label": clean_lbl,
                        "url": href
                    })

            if not episode_list:
                continue

            prev_p = paragraphs[max(0, i-4):i]
            header_text = " ".join([re.sub(r"<[^>]+>", " ", pp).strip() for pp in prev_p])
            header_text = unescape(re.sub(r"\s+", " ", header_text))

            size_matches = re.findall(r"\[\s*([0-9\.]+\s*(?:MB|GB)(?:/[^\]]+)?)\s*\]", header_text, re.I)
            size_str = size_matches[-1].strip() if size_matches else "N/A"

            clean_hdr = re.sub(r"\[.*?\]", "", header_text)
            clean_hdr = re.sub(r"(?:Episode\s*\d+|Zip\s*/\s*Pack|\b\d+\b)", "", clean_hdr)
            clean_hdr = re.sub(r"\s+", " ", clean_hdr).strip()
            tokens = clean_hdr.split(" ")
            short_desc = " ".join(tokens[-12:]) if len(tokens) > 12 else clean_hdr

            is_zip = any("zip" in ep["label"].lower() or "pack" in ep["label"].lower() for ep in episode_list)

            tiers.append({
                "header": short_desc or "Direct Download",
                "size": size_str,
                "is_zip": is_zip,
                "total_episodes": len(episode_list),
                "episodes": episode_list
            })

    return {
        "title": page_title,
        "url": post_url,
        "tiers": tiers
    }

def print_detailed_inspection(post_url, show_all_links=False):
    print("================================================================================")
    print(" 📑 IN-DEPTH POST INSPECTOR")
    print("================================================================================")
    print(f"URL: {post_url}\n")
    
    data = inspect_post(post_url)
    print(f"🎬 Title: {data['title']}")
    print(f"📊 Total Quality Tiers Detected: {len(data['tiers'])}\n")

    for idx, t in enumerate(data["tiers"], 1):
        pack_type = "📦 Zip Pack" if t["is_zip"] else f"🎬 {t['total_episodes']} Episodes"
        print("--------------------------------------------------------------------------------")
        print(f"[{idx}] {t['header']}")
        print(f"    ├─ File Size       : {t['size']}")
        print(f"    ├─ Structure       : {pack_type}")
        print(f"    └─ Available Items : {t['total_episodes']} links")

        if show_all_links or t['total_episodes'] <= 10:
            print("\n    🔗 Links:")
            for ep in t["episodes"]:
                print(f"       • {ep['label']:<12} : {ep['url']}")
        else:
            print("\n    🔗 Sample Links (showing first 5 of {0}, pass --all to show all):".format(t['total_episodes']))
            for ep in t["episodes"][:5]:
                print(f"       • {ep['label']:<12} : {ep['url'][:65]}...")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_post.py <POST_URL> [--all] [--json]")
        sys.exit(1)

    url = sys.argv[1]
    show_all = "--all" in sys.argv
    as_json = "--json" in sys.argv

    if as_json:
        data = inspect_post(url)
        print(json.dumps(data, indent=2))
    else:
        print_detailed_inspection(url, show_all_links=show_all)

if __name__ == "__main__":
    main()
