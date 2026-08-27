#!/usr/bin/env python3
"""
Pure Live Web Search (Zero-Cost, Zero-Tokens, No AI / No API Keys)
Fetches real-time web search results directly from the live web.

Usage:
    python3 live_search.py "gas booking in india number for hp in ap"
    python3 live_search.py "Python 3.13 changelog"
    python3 live_search.py --json "Claude SDK"
    python3 live_search.py --sources-only "OpenAI Agents SDK"
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.parse
import html as html_lib

def search_live_web(query: str, max_results: int = 5):
    """
    Fetches real-time search results directly from the live web without any API keys or tokens.
    Extracts exact page titles, clean destination URLs, and full raw text snippets.
    """
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    req = urllib.request.Request(
        'https://html.duckduckgo.com/html/',
        data=data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=12).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ Web search connection error: {e}")
        return []
    
    # Extract exact page titles, destination URLs, and verbatim snippets
    h2_matches = re.findall(r'<h2[^>]*>\s*<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>', resp, re.DOTALL)
    snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', resp, re.DOTALL)
    
    results = []
    total = min(len(h2_matches), len(snippets))
    for i in range(min(total, max_results)):
        raw_url, raw_title = h2_matches[i]
        snippet_raw = snippets[i]
        
        # Clean redirect URL to extract the real target link
        if 'uddg=' in raw_url:
            parsed_url = urllib.parse.unquote(raw_url.split('uddg=')[1].split('&')[0])
        else:
            parsed_url = raw_url.strip()
            
        clean_title = re.sub(r'<[^<]+?>', '', html_lib.unescape(raw_title)).strip()
        clean_snippet = re.sub(r'<[^<]+?>', '', html_lib.unescape(snippet_raw)).strip()
            
        results.append({
            'index': i + 1,
            'title': clean_title,
            'url': parsed_url,
            'snippet': clean_snippet
        })
    return results

def main():
    parser = argparse.ArgumentParser(description="Live Web Search (Zero API Keys, Zero Tokens)")
    parser.add_argument("query", nargs="*", help="The search query or question")
    parser.add_argument("-q", "--query-str", type=str, help="Search query as flag")
    parser.add_argument("--sources-only", action="store_true", help="Print only source titles and URLs")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON for agents")
    parser.add_argument("-n", "--max-results", type=int, default=5, help="Number of search results to fetch (default: 5)")
    args = parser.parse_args()

    query = args.query_str or (" ".join(args.query) if args.query else "")
    if not query:
        query = "gas booking in india number for hp in ap"

    if not args.json and not args.sources_only:
        print(f"🔍 Searching live web for: '{query}'...\n")

    web_results = search_live_web(query, max_results=args.max_results)

    if not web_results:
        if args.json:
            print(json.dumps({"query": query, "error": "No results found", "sources": []}))
        else:
            print("❌ No search results found.")
        return

    # Machine-readable JSON output mode
    if args.json:
        output_data = {
            "query": query,
            "total_results": len(web_results),
            "results": web_results
        }
        print(json.dumps(output_data, indent=2))
        return

    # Sources-only mode
    if args.sources_only:
        for r in web_results:
            print(f"[{r['index']}] {r['title']}")
            print(f"    {r['url']}")
        return

    # Standard Human Terminal Output
    print("=" * 65)
    print(f"🌐 LIVE SEARCH RESULTS ({len(web_results)} Found):")
    print("=" * 65)
    for r in web_results:
        print(f"[{r['index']}] {r['title']}")
        print(f"    🔗 URL: {r['url']}")
        print(f"    📝 {r['snippet']}\n")

if __name__ == "__main__":
    main()
