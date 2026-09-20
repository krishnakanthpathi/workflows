#!/usr/bin/env python3
"""
Telegram Dispatcher
Launches Telegram via tg:// protocol on macOS and auto-accepts prompts with AppleScript.
"""

import sys
import time
import subprocess
import urllib.parse

def dispatch_telegram(tg_url_or_proto, label="Video File"):
    """
    Given a seedtg URL or tg:// protocol link:
    - Launches /Applications/Telegram.app with the payload
    - Focuses Telegram and presses Return / clicks START
    """
    if "seedtg.xyz" in tg_url_or_proto or "http" in tg_url_or_proto:
        parsed = urllib.parse.urlparse(tg_url_or_proto)
        params = urllib.parse.parse_qs(parsed.query)
        bot = params.get("bot", ["seedcdn_bot"])[0]
        start = params.get("start", [""])[0]
        tg_proto_url = f"tg://resolve?domain={bot}&start={start}"
    else:
        tg_proto_url = tg_url_or_proto

    import platform
    current_os = platform.system().lower()

    if current_os == "darwin":
        print(f"[*] Launching Telegram for '{label}' on macOS...")
        subprocess.run(["open", tg_proto_url], check=True)
        time.sleep(2)

        applescript = """
        tell application "Telegram" to activate
        delay 1
        tell application "System Events"
            tell process "Telegram"
                key code 36
            end tell
        end tell
        """
        res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        if res.returncode == 0:
            print("[+] Successfully sent START and accepted file prompt in Telegram.")
        else:
            print(f"[-] AppleScript notice: {res.stderr.strip() or 'Prompt focused.'}")
    elif current_os == "linux":
        print(f"[*] Launching Telegram for '{label}' on Linux...")
        try:
            subprocess.run(["xdg-open", tg_proto_url], check=True)
            print("[+] Dispatched tg:// URL via xdg-open on Linux.")
        except Exception as e:
            print(f"[-] Could not open via xdg-open: {e}. Protocol URL: {tg_proto_url}")
    else:
        print(f"[*] Telegram deep link: {tg_proto_url}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 telegram.py \"<TG_PROTO_OR_SEEDTG_URL>\" [LABEL]")
        sys.exit(1)

    url = sys.argv[1]
    lbl = sys.argv[2] if len(sys.argv) > 2 else "Video File"
    dispatch_telegram(url, lbl)
