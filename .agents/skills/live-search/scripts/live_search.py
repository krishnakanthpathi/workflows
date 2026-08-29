#!/usr/bin/env python3
"""
Live Web Search & Research Toolkit (Zero-Cost, Zero-Tokens, Zero-API-Keys)
Provides fast, resilient real-time general knowledge search, encyclopedic overviews,
clean destination URL extraction, and deep HTML-to-Markdown page reading.

Features:
    1. Resilient Web Search: DuckDuckGo HTML with automatic DuckDuckGo Lite fallback.
    2. Encyclopedic Overviews: Wikipedia REST & OpenSearch integration.
    3. Deep Page Reader (--read <URL>): Converts any article/webpage to clean Markdown.
    4. Deep Search Mode (--deep <N>): Searches and automatically deep-reads the top N pages.
    5. Agent-Ready JSON (--json): Machine-readable structured outputs for AI pipelines.

Usage:
    # 1. Standard search
    python3 live_search.py "nuclear fusion energy"

    # 2. Direct page reader
    python3 live_search.py --read "https://en.wikipedia.org/wiki/Quantum_entanglement"

    # 3. Search + Deep read top 2 results
    python3 live_search.py --deep 2 "nuclear fusion energy"

    # 4. JSON mode for autonomous agents
    python3 live_search.py --deep 2 --json "CRISPR prime editing"

    # 5. Fast sources & URLs only
    python3 live_search.py --sources-only "James Webb Space Telescope"
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.parse
import html as html_lib
import ssl
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor

# Permissive SSL context for environment compatibility
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


# =====================================================================
# HTML & URL UTILITIES
# =====================================================================

def clean_html_text(raw_html: str) -> str:
    """Strips HTML tags, decodes HTML entities, and normalizes whitespace."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^<]+?>", "", raw_html)
    text = html_lib.unescape(text)
    return " ".join(text.split()).strip()


def unwrap_redirect_url(raw_url: str) -> str:
    """Extracts actual destination URL from redirect trackers like uddg=."""
    if not raw_url:
        return ""
    if "uddg=" in raw_url:
        try:
            target = raw_url.split("uddg=")[1].split("&")[0]
            return urllib.parse.unquote(target)
        except Exception:
            return raw_url.strip()
    return raw_url.strip()


# =====================================================================
# DEEP HTML-TO-MARKDOWN PARSER
# =====================================================================

VOID_TAGS = {
    "meta", "link", "img", "br", "hr", "input", "area",
    "base", "col", "embed", "param", "source", "track", "wbr"
}

CONTAINER_IGNORE_TAGS = {
    "script", "style", "nav", "footer", "header", "aside",
    "noscript", "svg", "iframe", "button", "form", "head",
    "dialog", "menu"
}


class HTMLToMarkdownParser(HTMLParser):
    """
    Zero-dependency HTML to structured Markdown converter.
    Strips navigation, footers, sidebars, scripts, and ads.
    Converts headings, paragraphs, lists, code, quotes, and tables to Markdown.
    """
    def __init__(self):
        super().__init__()
        self.result = []
        self.ignore_stack = 0
        self.in_pre = False
        self.in_code = False
        self.heading_level = 0
        self.in_li = False
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()

        # Handle void/self-closing tags safely without altering ignore_stack
        if tag_lower in VOID_TAGS:
            if tag_lower == "hr" and self.ignore_stack == 0:
                self.result.append("\n\n---\n\n")
            elif tag_lower == "br" and self.ignore_stack == 0:
                self.result.append("\n")
            return

        if tag_lower == "title":
            self.in_title = True
            return

        if tag_lower in CONTAINER_IGNORE_TAGS:
            self.ignore_stack += 1
            return

        if self.ignore_stack > 0:
            return

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_level = int(tag_lower[1])
            self.result.append("\n\n" + "#" * self.heading_level + " ")
        elif tag_lower == "p":
            self.result.append("\n\n")
        elif tag_lower == "li":
            self.in_li = True
            self.result.append("\n- ")
        elif tag_lower == "pre":
            self.in_pre = True
            self.result.append("\n\n```\n")
        elif tag_lower == "code" and not self.in_pre:
            self.in_code = True
            self.result.append(" `")
        elif tag_lower == "blockquote":
            self.result.append("\n\n> ")
        elif tag_lower in ("th", "td"):
            self.result.append(" | ")

    def handle_endtag(self, tag):
        tag_lower = tag.lower()

        if tag_lower in VOID_TAGS:
            return

        if tag_lower == "title":
            self.in_title = False
            return

        if tag_lower in CONTAINER_IGNORE_TAGS:
            self.ignore_stack = max(0, self.ignore_stack - 1)
            return

        if self.ignore_stack > 0:
            return

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_level = 0
            self.result.append("\n")
        elif tag_lower == "pre":
            self.in_pre = False
            self.result.append("\n```\n")
        elif tag_lower == "code" and self.in_code:
            self.in_code = False
            self.result.append("` ")
        elif tag_lower == "li":
            self.in_li = False
        elif tag_lower == "tr":
            self.result.append(" |\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
            return

        if self.ignore_stack == 0:
            if self.in_pre:
                self.result.append(data)
            else:
                cleaned = " ".join(data.split())
                if cleaned:
                    if self.result and not self.result[-1].endswith((" ", "\n", "#", "> ", "- ", "`", "(", "|")):
                        self.result.append(" ")
                    self.result.append(html_lib.unescape(cleaned))

    def get_markdown(self) -> str:
        text = "".join(self.result)
        # Normalize excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def fetch_url_markdown(url: str, max_chars: int = 0) -> dict:
    """
    Fetches raw HTML from a target URL and extracts clean structured Markdown.
    max_chars=0 (default) extracts the full, untruncated page content.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12, context=SSL_CTX) as response:
            content_bytes = response.read()
            # Try UTF-8 first, fallback to latin-1
            try:
                html_text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                html_text = content_bytes.decode("latin-1", errors="ignore")

        parser = HTMLToMarkdownParser()
        parser.feed(html_text)
        markdown = parser.get_markdown()
        page_title = parser.title.strip() if parser.title else url

        truncated = False
        if max_chars and max_chars > 0 and len(markdown) > max_chars:
            markdown = markdown[:max_chars] + f"\n\n... *(Content truncated at {max_chars} chars. Pass --max-chars 0 for full)*"
            truncated = True

        return {
            "url": url,
            "title": page_title,
            "markdown": markdown,
            "total_chars": len(markdown),
            "truncated": truncated,
            "status": "success",
        }
    except Exception as e:
        return {
            "url": url,
            "title": "",
            "markdown": f"⚠️ Failed to fetch page content: {e}",
            "total_chars": 0,
            "truncated": False,
            "status": "error",
            "error": str(e),
        }


# =====================================================================
# GENERAL WEB SEARCH ENGINES
# =====================================================================

def search_duckduckgo_html(query: str, max_results: int = 5) -> list:
    """
    Queries DuckDuckGo HTML endpoint and parses result titles, direct URLs, and snippets.
    """
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as response:
            resp = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    h2_matches = re.findall(
        r'<h2[^>]*>\s*<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>',
        resp,
        re.DOTALL,
    )
    snippets = re.findall(
        r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', resp, re.DOTALL
    )

    results = []
    total = min(len(h2_matches), len(snippets))
    for i in range(min(total, max_results)):
        raw_url, raw_title = h2_matches[i]
        snippet_raw = snippets[i]

        clean_url = unwrap_redirect_url(raw_url)
        clean_title = clean_html_text(raw_title)
        clean_snippet = clean_html_text(snippet_raw)

        if clean_url and clean_title:
            results.append({
                "index": i + 1,
                "title": clean_title,
                "url": clean_url,
                "snippet": clean_snippet,
                "engine": "ddg_html",
            })
    return results


def search_duckduckgo_lite(query: str, max_results: int = 5) -> list:
    """
    Queries DuckDuckGo Lite endpoint (fallback engine when HTML is throttled).
    """
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    req = urllib.request.Request(
        "https://lite.duckduckgo.com/lite/",
        data=data,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as response:
            resp = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    link_matches = re.findall(
        r'<a[^>]*rel=[\"\']nofollow[\"\'][^>]*href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>',
        resp,
        re.DOTALL,
    )
    snippet_matches = re.findall(
        r'<td[^>]*class=[\"\']result-snippet[\"\'][^>]*>(.*?)</td>',
        resp,
        re.DOTALL,
    )

    results = []
    total = min(len(link_matches), len(snippet_matches))
    for i in range(min(total, max_results)):
        raw_url, raw_title = link_matches[i]
        raw_snip = snippet_matches[i]

        clean_url = unwrap_redirect_url(raw_url)
        clean_title = clean_html_text(raw_title)
        clean_snippet = clean_html_text(raw_snip)

        if clean_url and clean_title:
            results.append({
                "index": i + 1,
                "title": clean_title,
                "url": clean_url,
                "snippet": clean_snippet,
                "engine": "ddg_lite",
            })
    return results


def fetch_wikipedia_overview(query: str) -> dict | None:
    """
    Fetches structured encyclopedic summary, definition, and article link from Wikipedia.
    Uses OpenSearch API to find the most relevant canonical topic, then queries the REST Summary API.
    """
    search_url = (
        f"https://en.wikipedia.org/w/api.php?action=opensearch&search="
        f"{urllib.parse.quote(query)}&limit=3&namespace=0&format=json"
    )
    req = urllib.request.Request(
        search_url,
        headers={"User-Agent": "LiveSearchToolkit/2.0 (General Knowledge Research)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as response:
            data = json.loads(response.read().decode("utf-8", errors="ignore"))
            if not data or len(data) < 2 or not data[1]:
                return None

            best_title = data[1][0]
            best_url = data[3][0] if len(data) > 3 and data[3] else ""

            sum_url = (
                f"https://en.wikipedia.org/api/rest_v1/page/summary/"
                f"{urllib.parse.quote(best_title.replace(' ', '_'))}"
            )
            req_sum = urllib.request.Request(
                sum_url,
                headers={"User-Agent": "LiveSearchToolkit/2.0 (General Knowledge Research)"},
            )
            try:
                with urllib.request.urlopen(req_sum, timeout=6, context=SSL_CTX) as sum_resp:
                    sum_data = json.loads(sum_resp.read().decode("utf-8", errors="ignore"))
                    return {
                        "title": sum_data.get("title", best_title),
                        "description": sum_data.get("description", ""),
                        "extract": sum_data.get("extract", ""),
                        "url": sum_data.get("content_urls", {}).get("desktop", {}).get("page", best_url),
                    }
            except Exception:
                desc = data[2][0] if len(data) > 2 and data[2] else ""
                return {
                    "title": best_title,
                    "description": desc,
                    "extract": desc,
                    "url": best_url,
                }
    except Exception:
        return None


def search_general_knowledge(
    query: str,
    max_results: int = 5,
    include_wiki: bool = True,
    wiki_only: bool = False,
    deep_count: int = 0,
    max_chars_per_page: int = 0,
) -> dict:
    """
    Executes general knowledge search with optional Wikipedia overview and deep reading of top N results.
    max_chars_per_page=0 (default) extracts full untruncated content.
    """
    wiki_overview = None
    web_results = []
    engine_used = "none"

    if wiki_only:
        wiki_overview = fetch_wikipedia_overview(query)
        return {
            "query": query,
            "encyclopedic_overview": wiki_overview,
            "results": [],
            "engine_used": "wikipedia",
        }

    # Parallel execution of web search and Wikipedia overview
    with ThreadPoolExecutor(max_workers=2) as executor:
        wiki_future = executor.submit(fetch_wikipedia_overview, query) if include_wiki else None

        web_results = search_duckduckgo_html(query, max_results=max_results)
        engine_used = "ddg_html"

        if not web_results:
            web_results = search_duckduckgo_lite(query, max_results=max_results)
            engine_used = "ddg_lite"

        if wiki_future:
            try:
                wiki_overview = wiki_future.result()
            except Exception:
                wiki_overview = None

    # Deep Read Top N Results if requested
    if deep_count > 0 and web_results:
        target_count = min(deep_count, len(web_results))
        urls_to_fetch = [web_results[i]["url"] for i in range(target_count)]

        with ThreadPoolExecutor(max_workers=min(target_count, 5)) as executor:
            deep_futures = [
                executor.submit(fetch_url_markdown, url, max_chars_per_page)
                for url in urls_to_fetch
            ]
            for i, future in enumerate(deep_futures):
                try:
                    read_result = future.result()
                    web_results[i]["deep_content"] = read_result.get("markdown", "")
                    web_results[i]["page_title"] = read_result.get("title", "")
                except Exception as e:
                    web_results[i]["deep_content"] = f"⚠️ Error reading page: {e}"

    return {
        "query": query,
        "encyclopedic_overview": wiki_overview,
        "results": web_results,
        "engine_used": engine_used,
        "deep_count": deep_count,
    }


# =====================================================================
# HUMAN TERMINAL OUTPUT FORMATTER
# =====================================================================

def format_human_output(data: dict, sources_only: bool = False) -> None:
    """Renders formatted search and research output in the terminal."""
    query = data.get("query", "")
    overview = data.get("encyclopedic_overview")
    results = data.get("results", [])
    engine = data.get("engine_used", "web")
    deep_count = data.get("deep_count", 0)

    if sources_only:
        if overview and overview.get("url"):
            print(f"[Wiki] {overview['title']}")
            print(f"       {overview['url']}")
        for r in results:
            print(f"[{r['index']}] {r['title']}")
            print(f"    {r['url']}")
        return

    # Print Header
    print("=" * 72)
    print(f"🔍 SEARCH & RESEARCH: '{query}'")
    print(f"📡 Provider: {engine.upper()} | Zero Tokens / $0.00 Cost" + (f" | Deep Read: Top {deep_count}" if deep_count else ""))
    print("=" * 72)

    # Print Encyclopedic Overview Card if available
    if overview and overview.get("title") and overview.get("extract"):
        print("\n📖 ENCYCLOPEDIC OVERVIEW (Wikipedia):")
        print(f"   📌 Topic: {overview['title']}" + (f" ({overview['description']})" if overview.get('description') else ""))
        print(f"   🔗 Source: {overview['url']}")
        print(f"   📝 {overview['extract']}\n")
        print("-" * 72)

    # Print Web Results
    if results:
        print(f"\n🌐 WEB SEARCH RESULTS ({len(results)} Found via {engine}):\n")
        for r in results:
            print(f"[{r['index']}] {r['title']}")
            print(f"    🔗 URL: {r['url']}")
            print(f"    📝 {r['snippet']}")

            # Print Deep Content if available
            if "deep_content" in r and r["deep_content"]:
                print(f"\n    📄 DEEP PAGE CONTENT ({r.get('page_title', r['title'])}):")
                print("    " + "-" * 64)
                for line in r["deep_content"].split("\n"):
                    print(f"    {line}")
                print("    " + "-" * 64)
            print()
    elif not overview:
        print("❌ No search results found. Please check your connection or refine the query.")


def main():
    parser = argparse.ArgumentParser(
        description="Live Web Search & Research Toolkit (Zero-Token, Zero-Cost General Knowledge)"
    )
    parser.add_argument("query", nargs="*", help="The search query or research topic")
    parser.add_argument("-q", "--query-str", type=str, help="Search query string via flag")
    parser.add_argument("-n", "--max-results", type=int, default=5, help="Number of search results to fetch (default: 5)")
    parser.add_argument("--read", type=str, help="Read and convert a specific URL directly to structured Markdown")
    parser.add_argument("--deep", type=int, nargs="?", const=2, default=0, help="Search and deep-read top N results (default: 2)")
    parser.add_argument("--max-chars", type=int, default=0, help="Optional max characters limit per page (default: 0 for full untruncated content)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON for autonomous agents")
    parser.add_argument("--sources-only", action="store_true", help="Output only source titles and verified URLs")
    parser.add_argument("--no-wiki", action="store_true", help="Disable encyclopedic Wikipedia overview lookup")
    parser.add_argument("--wiki-only", action="store_true", help="Fetch only encyclopedic definition and summary")
    args = parser.parse_args()

    max_chars = args.max_chars

    # 1. Direct Page Reader Mode (--read <URL>)
    if args.read:
        url = args.read.strip()
        if not args.json:
            print(f"📖 Reading and extracting content from: {url}\n")
        read_result = fetch_url_markdown(url, max_chars=max_chars)
        if args.json:
            print(json.dumps(read_result, indent=2))
        else:
            if read_result["status"] == "success":
                print("=" * 72)
                print(f"📄 ARTICLE: {read_result['title']}")
                print(f"🔗 URL: {read_result['url']}")
                print("=" * 72 + "\n")
                print(read_result["markdown"])
                if read_result.get("truncated"):
                    print(f"\n💡 Note: Truncated at {read_result['total_chars']} chars. Use --full for untruncated text.")
            else:
                print(f"❌ Error: {read_result.get('error', 'Failed to fetch')}")
        return

    # 2. Search & Research Mode (with optional --deep)
    query = args.query_str or (" ".join(args.query) if args.query else "")
    if not query:
        query = "nuclear fusion and fission differences"

    search_data = search_general_knowledge(
        query=query,
        max_results=args.max_results,
        include_wiki=not args.no_wiki,
        wiki_only=args.wiki_only,
        deep_count=args.deep,
        max_chars_per_page=max_chars,
    )

    if args.json:
        print(json.dumps(search_data, indent=2))
        return

    format_human_output(search_data, sources_only=args.sources_only)


if __name__ == "__main__":
    main()
