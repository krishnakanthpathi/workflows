#!/usr/bin/env python3
"""
Catalog Search Tool
Searches the video catalog and returns clean numbered results with titles and URLs.
"""

import sys
import re
import urllib.request
import urllib.parse
from html import unescape

BASE_URL = "https://uhdmovies.my"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def search_titles(query):
    search_url = f"{BASE_URL}/?s={urllib.parse.quote_plus(query)}"
    req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[-] Search network error: {e}", file=sys.stderr)
        return []

    results = []
    articles = re.findall(
        r"<article[^>]*>.*?<a[^>]+href=[\"']([^\"']+)[\"'][^>]*title=[\"']([^\"']+)[\"'].*?</article>",
        html,
        re.DOTALL
    )
    for href, title in articles:
        clean_title = unescape(re.sub(r"\s+", " ", title)).strip()
        results.append({
            "title": clean_title,
            "url": href
        })
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search.py \"<title or search query>\"")
        sys.exit(1)

    query = sys.argv[1]
    print(f"\n=======================================================")
    print(f" 🔎 SEARCHING CATALOG: '{query}'")
    print(f"=======================================================")
    results = search_titles(query)
    if not results:
        print("[-] No titles found matching query.")
        return

    for idx, item in enumerate(results, 1):
        print(f"[{idx}] {item['title']}")
        print(f"    {item['url']}\n")

    print("-------------------------------------------------------")
    print("👉 To inspect any result in detail, run:")
    print("   python3 inspect_post.py \"<URL>\"\n")

if __name__ == "__main__":
    main()
