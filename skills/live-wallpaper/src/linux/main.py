import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import time
import argparse
import subprocess
from typing import List

from models import resolve_media_sources
from ipc import (
    is_running,
    stop_running,
    send_command,
    read_pid,
    PID_FILE
)
from engine import LinuxWallpaperEngine
from screensaver import run_standalone_screensaver
from service import install_service, uninstall_service, status_service

HELP_TEXT = """macOS & Linux Live Wallpaper and Screensaver Engine (Linux Backend)

USAGE:
  live-wallpaper [OPTIONS] [SOURCES...]
  live-wallpaper <COMMAND>

COMMANDS:
  screensaver [SOURCES...]            Launch fullscreen screensaver overlay immediately
  status                             Print running instance status and playback mode
  queue, list                        Display current queue
  next                               Advance to next wallpaper
  prev                               Return to previous wallpaper
  goto <index>                       Jump directly to 1-based queue index
  add <file|dir|url>                 Append new media to running queue
  stop                               Terminate running background engine
  service <install|uninstall|status> Manage systemd user service auto-start

OPTIONS:
  -d, --daemon                       Run wallpaper engine in the background
  -p, --per-space, --per-monitor     Enable multi-monitor wallpaper distribution
  -a, --audio, --unmute              Enable audio playback (default: muted)
  -m, --mute                         Mute audio playback
  -v, --volume <0-100>               Set audio volume percentage (e.g. 35)
  -i, --interval <seconds>           Queue rotation interval in seconds (default: 60)
  -s, --shuffle                      Randomize wallpaper playback order
  --screensaver [seconds]            Enable auto-screensaver on idle (default: 180s)
  --screensaver-source <src>         Dedicated media path or directory for screensaver
  -h, --help                         Display this help menu
"""

def print_status():
    if not is_running():
        print("Status: No live-wallpaper daemon currently running.")
        return

    res = send_command({"action": "status"})
    if not res or res.get("status") != "ok":
        pid = read_pid()
        print(f"Status: Daemon running (PID: {pid}), but IPC is unresponsive.")
        return

    print("=== Live Wallpaper Status ===")
    print(f"PID:            {res.get('pid')}")
    print(f"Mode:           {res.get('mode')}")
    print(f"Current Item:   {res.get('current_path') or 'None'}")
    print(f"Queue Position: [{res.get('current_index')}/{res.get('total_items')}]")
    print(f"Paused:         {res.get('is_paused')}")
    audio_str = "Muted" if res.get("is_muted") else f"{res.get('volume')}%"
    print(f"Audio:          {audio_str}")

def print_queue():
    if not is_running():
        print("No live-wallpaper daemon currently running.")
        return

    res = send_command({"action": "queue"})
    if not res or res.get("status") != "ok":
        print("Failed to retrieve queue from daemon.")
        return

    items = res.get("queue", [])
    if not items:
        print("Queue is empty.")
        return

    print(f"=== Active Wallpaper Queue ({len(items)} items) ===")
    for idx, item in enumerate(items, 1):
        is_cur = item.get("current", False)
        prefix = "▶" if is_cur else " "
        mark = " (Active)" if is_cur else ""
        print(f"{prefix} [{idx}] {item.get('path')}{mark}")

def main():
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args or "help" in args:
        print(HELP_TEXT)
        sys.exit(0)

    # 1. Dispatch simple subcommands
    first = args[0]
    if first in ("status", "--status"):
        print_status()
        sys.exit(0)
    elif first in ("queue", "list", "--queue", "--list"):
        print_queue()
        sys.exit(0)
    elif first in ("next", "--next"):
        if send_command({"action": "next"}):
            time.sleep(0.1)
            print_status()
        else:
            print("Daemon not running or failed to skip to next.")
        sys.exit(0)
    elif first in ("prev", "--prev"):
        if send_command({"action": "prev"}):
            time.sleep(0.1)
            print_status()
        else:
            print("Daemon not running or failed to return to previous.")
        sys.exit(0)
    elif first in ("goto", "--goto"):
        if len(args) > 1 and args[1].isdigit():
            idx = int(args[1])
            if send_command({"action": "goto", "index": idx}):
                time.sleep(0.1)
                print_status()
            else:
                print("Failed to jump to index.")
        else:
            print("Usage: live-wallpaper goto <1-based index>")
        sys.exit(0)
    elif first in ("add", "--add"):
        if len(args) > 1:
            res = send_command({"action": "add", "source": args[1]})
            if res and res.get("status") == "ok":
                print(f"Added {res.get('added', 1)} item(s) to running queue.")
            else:
                print("Failed to add media to running queue.")
        else:
            print("Usage: live-wallpaper add <path|dir|url>")
        sys.exit(0)
    elif first in ("stop", "--stop"):
        stop_running()
        sys.exit(0)
    elif first == "service":
        action = args[1] if len(args) > 1 else ""
        if action == "install":
            install_service(args[2:])
        elif action == "uninstall":
            uninstall_service()
        elif action == "status":
            status_service()
        else:
            print("Usage: live-wallpaper service <install|uninstall|status>")
        sys.exit(0)
    elif first in ("screensaver", "--screensaver-test"):
        sources = args[1:]
        if not sources:
            # Check default wallpaper folder or fallbacks
            sources = [os.path.expanduser("~/Pictures/Wallpapers")]
        run_standalone_screensaver(sources)
        sys.exit(0)

    # 2. Parse general options and sources for wallpaper runner
    is_daemon = False
    is_muted = True
    volume = 1.0
    interval = 60.0
    per_space = False
    shuffle = False
    screensaver_idle = None
    screensaver_sources = []
    raw_sources = []

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-d", "--daemon"):
            is_daemon = True
        elif a in ("-a", "--audio", "--unmute"):
            is_muted = False
        elif a in ("-m", "--mute"):
            is_muted = True
        elif a in ("-v", "--volume"):
            if i + 1 < len(args):
                try:
                    v = float(args[i + 1])
                    volume = max(0.0, min(1.0, v / 100.0 if v > 1.0 else v))
                    is_muted = False
                except ValueError:
                    pass
                i += 1
        elif a in ("-i", "--interval"):
            if i + 1 < len(args):
                try:
                    interval = float(args[i + 1])
                except ValueError:
                    pass
                i += 1
        elif a in ("-p", "--per-space", "--per-monitor"):
            per_space = True
        elif a in ("-s", "--shuffle"):
            shuffle = True
        elif a in ("--screensaver", "--screensaver-idle"):
            if i + 1 < len(args) and args[i + 1].replace(".", "", 1).isdigit():
                screensaver_idle = float(args[i + 1])
                i += 1
            else:
                screensaver_idle = 180.0
        elif a == "--screensaver-source":
            if i + 1 < len(args):
                screensaver_sources.append(args[i + 1])
                i += 1
        else:
            raw_sources.append(a)
        i += 1

    if not raw_sources:
        # Default fallback folder
        default_dir = os.path.expanduser("~/Pictures/Wallpapers")
        if os.path.isdir(default_dir):
            raw_sources.append(default_dir)
        else:
            print("Error: No media sources or directories specified.")
            print("Usage: live-wallpaper [-d] [-p] /path/to/media/or/folder")
            sys.exit(1)

    resolved = resolve_media_sources(raw_sources)
    if not resolved:
        print("Error: No valid video or image files found in specified sources.")
        sys.exit(1)

    if is_running():
        print("A live-wallpaper daemon is already running. Stopping it first...")
        stop_running()

    if is_daemon:
        # Launch detached background process
        cmd = [sys.executable, "-m", "skills.live-wallpaper.src.linux.main"]
        # Use full path directly
        script_path = os.path.abspath(__file__)
        daemon_cmd = [sys.executable, script_path]
        for a in args:
            if a not in ("-d", "--daemon"):
                daemon_cmd.append(a)

        proc = subprocess.Popen(
            daemon_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"==> Started live-wallpaper daemon (PID: {proc.pid})")
        print(f"Loaded {len(resolved)} wallpaper(s).")
        print("Run 'live-wallpaper status' or 'live-wallpaper queue' to inspect.")
        sys.exit(0)

    # Foreground execution
    print(f"==> Starting live-wallpaper engine ({len(resolved)} item(s))...")
    engine = LinuxWallpaperEngine(
        sources=resolved,
        is_muted=is_muted,
        volume=volume,
        interval=interval,
        shuffle=shuffle,
        screensaver_idle=screensaver_idle,
        screensaver_sources=screensaver_sources,
        per_monitor=per_space
    )
    engine.run()

if __name__ == "__main__":
    main()
