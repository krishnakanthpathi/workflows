#!/usr/bin/env python3
"""
Live Market Pulse Service (Zero-Token, Zero-API-Key)
Fetches real-time market quotes and 24h percentage changes for:
- Indian Indices: Nifty 50, Sensex
- US & Global Indices: S&P 500, Nasdaq
- Commodities & Forex: Gold, USD/INR
"""

import json
import urllib.request
import urllib.error

SYMBOLS = [
    {"name": "NIFTY 50", "symbol": "%5ENSEI", "type": "index", "currency": "INR"},
    {"name": "SENSEX", "symbol": "%5EBSESN", "type": "index", "currency": "INR"},
    {"name": "S&P 500", "symbol": "%5EGSPC", "type": "index", "currency": "USD"},
    {"name": "NASDAQ", "symbol": "%5EIXIC", "type": "index", "currency": "USD"},
    {"name": "GOLD", "symbol": "GC%3DF", "type": "commodity", "currency": "USD"},
    {"name": "USD/INR", "symbol": "INR%3DX", "type": "forex", "currency": "INR"},
]

def fetch_symbol_quote(sym_info, timeout=4):
    symbol = sym_info["symbol"]
    name = sym_info["name"]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose", price)
            if price is None:
                return None
            change = price - prev_close if prev_close else 0.0
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
            return {
                "name": name,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "currency": sym_info["currency"]
            }
    except Exception:
        return None

def get_market_pulse(timeout=4):
    """Fetches all tracked market quotes and returns structured data."""
    quotes = []
    for s in SYMBOLS:
        q = fetch_symbol_quote(s, timeout=timeout)
        if q:
            quotes.append(q)
    return quotes

def format_market_pulse_discord(quotes):
    """Formats market pulse for Discord message."""
    if not quotes:
        return "📊 *Market data temporarily unavailable.*"
    
    parts = []
    for q in quotes:
        icon = "🟢" if q["change_pct"] >= 0 else "🔴"
        sign = "+" if q["change_pct"] >= 0 else ""
        if q["currency"] == "INR" and "USD" not in q["name"]:
            price_str = f"₹{q['price']:,.2f}"
        elif q["currency"] == "INR" and "USD" in q["name"]:
            price_str = f"₹{q['price']:.2f}"
        else:
            price_str = f"${q['price']:,.2f}"
        parts.append(f"{icon} **{q['name']}**: `{price_str}` ({sign}{q['change_pct']:.2f}%)")
    return " | ".join(parts)

def format_market_pulse_obsidian(quotes):
    """Formats market pulse as a clean Markdown table for Obsidian."""
    if not quotes:
        return "> *Live market data snapshot not captured.*"
    
    rows = [
        "| Index / Asset | Last Price | 24h Change | Sentiment |",
        "| :--- | :--- | :--- | :--- |"
    ]
    for q in quotes:
        icon = "🟢 Bullish" if q["change_pct"] >= 0 else "🔴 Bearish"
        sign = "+" if q["change_pct"] >= 0 else ""
        if q["currency"] == "INR" and "USD" not in q["name"]:
            price_str = f"₹{q['price']:,.2f}"
        elif q["currency"] == "INR" and "USD" in q["name"]:
            price_str = f"₹{q['price']:.2f}"
        else:
            price_str = f"${q['price']:,.2f}"
        rows.append(f"| **{q['name']}** | `{price_str}` | `{sign}{q['change_pct']:.2f}%` | {icon} |")
    return "\n".join(rows)

if __name__ == "__main__":
    print("Fetching live market pulse...")
    data = get_market_pulse()
    print("\nDiscord Format:")
    print(format_market_pulse_discord(data))
    print("\nObsidian Table:")
    print(format_market_pulse_obsidian(data))
