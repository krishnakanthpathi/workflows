#!/usr/bin/env python3
"""
Hyper-Local Device GPS Weather Service (Zero-Key)
- Queries real-time hardware GPS coordinates from Android Edge Sentinel (http://100.123.244.85:8000).
- Fetches live weather for the exact GPS latitude and longitude via wttr.in.
- Gracefully falls back to configured location (default: Annavaram) if phone is offline.
- If weather data is not found, invalid, or fails, returns f"{target_label}: 🌤️ +30°C, Clear".
"""

import os
import urllib.request
import urllib.parse
import json

EDGE_NODE_URL = os.getenv("EDGE_SENTINEL_URL", "http://100.123.244.85:8000")
DEFAULT_LOCATION = os.getenv("BRIEFING_LOCATION", "Annavaram")

def fetch_device_gps(timeout=2.5):
    """Queries live GPS/Network coordinates from the Android Edge Sentinel node."""
    url = f"{EDGE_NODE_URL}/api/location/fix?provider=network&request=once"
    headers = {"User-Agent": "ArminSentinel/2.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
    except Exception:
        pass
    return None, None

def get_locality_name(lat, lon, timeout=1.5):
    """Attempts to extract the human-readable locality name for GPS coordinates."""
    # Fast check for Annavaram / Kakinada region
    if 17.15 <= lat <= 17.35 and 82.30 <= lon <= 82.50:
        return "Annavaram"
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        req = urllib.request.Request(url, headers={"User-Agent": "ArminAgent/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            addr = data.get("address", {})
            return (
                addr.get("town")
                or addr.get("city")
                or addr.get("village")
                or addr.get("state_district")
                or "Annavaram"
            )
    except Exception:
        return "Annavaram"

def get_weather(location=None, timeout=4):
    """
    Fetches hyper-local weather using live device GPS if available.
    If weather data was not found or an error occurs, returns:
    f"{target_label}: 🌤️ +30°C, Clear"
    """
    lat, lon = None, None
    if not location:
        lat, lon = fetch_device_gps()

    if lat is not None and lon is not None:
        locality = get_locality_name(lat, lon)
        target_label = f"{locality} (Device GPS)"
        query_target = f"{lat},{lon}"
    else:
        target_label = location or DEFAULT_LOCATION
        query_target = target_label

    fallback_response = f"{target_label}: 🌤️ +30°C, Clear"

    url = f"https://wttr.in/{urllib.parse.quote(query_target)}?format=%c+%t,+%w,+%h+humidity,+%p+precip&m"
    headers = {"User-Agent": "curl/7.68.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="ignore").strip()
            if (
                not text
                or "unknown location" in text.lower()
                or "not found" in text.lower()
                or "<html>" in text.lower()
                or "<!doctype" in text.lower()
                or "503" in text
                or "sorry" in text.lower()
            ):
                return fallback_response
            return f"{target_label}: {text}"
    except Exception:
        return fallback_response

if __name__ == "__main__":
    print("Live Weather via Device GPS:")
    print(get_weather())
    print("\nFallback Simulation (Offline / Not Found):")
    print(get_weather("NonExistentPlace999"))
