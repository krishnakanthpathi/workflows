import os
import sys
import time
import json
import shutil
import socket
import hashlib
import threading
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

from models import resolve_media_sources, MediaItem, MediaType
from ipc import (
    SOCKET_PATH,
    PID_FILE,
    MPV_SOCKET,
    CACHE_DIR,
    write_pid,
    cleanup_ipc,
    ensure_cache_dir
)

def is_gnome_session() -> bool:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    session = os.environ.get("DESKTOP_SESSION", "").upper()
    return "GNOME" in desktop or "UBUNTU" in desktop or "GNOME" in session

def set_gnome_wallpaper(file_path: str):
    """Sets wallpaper natively in GNOME Shell without window overlay conflicts."""
    uri = f"file://{os.path.abspath(file_path)}"
    try:
        from gi.repository import Gio
        settings = Gio.Settings.new("org.gnome.desktop.background")
        settings.set_string("picture-options", "zoom")
        settings.set_string("picture-uri", uri)
        settings.set_string("picture-uri-dark", uri)
        settings.apply()
    except Exception:
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"], check=False)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri], check=False)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri], check=False)

def get_snapshot_for_video(video_path: str) -> str:
    """Extracts a high quality frame from a video for native desktop background display."""
    ensure_cache_dir()
    snap_dir = os.path.join(CACHE_DIR, "snapshots")
    os.makedirs(snap_dir, exist_ok=True)
    file_hash = hashlib.md5(video_path.encode("utf-8")).hexdigest()
    snap_path = os.path.join(snap_dir, f"{file_hash}.jpg")

    if not os.path.exists(snap_path) or os.path.getsize(snap_path) == 0:
        subprocess.run([
            "ffmpeg", "-y", "-ss", "00:00:01", "-i", video_path,
            "-frames:v", "1", "-q:v", "2", snap_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        # Fallback to 00:00:00 if 1s fails
        if not os.path.exists(snap_path) or os.path.getsize(snap_path) == 0:
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path,
                "-frames:v", "1", "-q:v", "2", snap_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    return snap_path if os.path.exists(snap_path) else video_path

class LinuxWallpaperEngine:
    def __init__(
        self,
        sources: List[str],
        is_muted: bool = True,
        volume: float = 1.0,
        interval: float = 60.0,
        shuffle: bool = False,
        screensaver_idle: Optional[float] = None,
        screensaver_sources: Optional[List[str]] = None,
        per_monitor: bool = False
    ):
        self.sources = resolve_media_sources(sources)
        self.is_muted = is_muted
        self.volume = volume
        self.interval = interval if interval > 0 else 60.0
        self.shuffle = shuffle
        self.screensaver_idle = screensaver_idle
        self.screensaver_sources = resolve_media_sources(screensaver_sources) if screensaver_sources else self.sources
        self.per_monitor = per_monitor

        self.current_index = 0
        self.is_paused = False
        self.is_screensaver_active = False
        self.screensaver_proc = None
        self.running = False

        self.ipc_server_sock = None
        self.ipc_thread = None
        self.rotation_thread = None
        self.idle_thread = None

        if self.shuffle and len(self.sources) > 1:
            import random
            random.shuffle(self.sources)

    def apply_current_wallpaper(self):
        """Applies current wallpaper natively without creating intrusive overlay windows."""
        if not self.sources:
            return

        current_path = self.sources[self.current_index]
        media_item = MediaItem(current_path)

        if is_gnome_session():
            if media_item.type == MediaType.VIDEO:
                target_image = get_snapshot_for_video(current_path)
            else:
                target_image = current_path
            set_gnome_wallpaper(target_image)

    def start_ipc_server(self):
        """Runs IPC unix domain socket server for CLI controls."""
        ensure_cache_dir()
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except OSError:
                pass

        self.ipc_server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.ipc_server_sock.bind(SOCKET_PATH)
        self.ipc_server_sock.listen(5)
        self.ipc_server_sock.settimeout(0.5)

        def listen_loop():
            while self.running:
                try:
                    conn, _ = self.ipc_server_sock.accept()
                    data = b""
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                        if b"\n" in chunk:
                            break
                    if data:
                        req = json.loads(data.decode("utf-8"))
                        resp = self.handle_ipc_request(req)
                        conn.sendall(json.dumps(resp).encode("utf-8") + b"\n")
                    conn.close()
                except socket.timeout:
                    continue
                except Exception:
                    continue

        self.ipc_thread = threading.Thread(target=listen_loop, daemon=True)
        self.ipc_thread.start()

    def handle_ipc_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        action = req.get("action")

        if action == "status":
            current_path = self.sources[self.current_index] if self.sources else None
            return {
                "status": "ok",
                "pid": os.getpid(),
                "mode": "Screensaver" if self.is_screensaver_active else "Wallpaper",
                "current_path": current_path,
                "current_index": self.current_index + 1,
                "total_items": len(self.sources),
                "is_paused": self.is_paused,
                "volume": int(self.volume * 100),
                "is_muted": self.is_muted
            }

        elif action == "queue":
            items = []
            for idx, s in enumerate(self.sources):
                items.append({
                    "path": s,
                    "current": (idx == self.current_index),
                    "id": idx + 1
                })
            return {"status": "ok", "queue": items}

        elif action == "next":
            if self.sources:
                self.current_index = (self.current_index + 1) % len(self.sources)
                self.apply_current_wallpaper()
            return {"status": "ok"}

        elif action == "prev":
            if self.sources:
                self.current_index = (self.current_index - 1) % len(self.sources)
                self.apply_current_wallpaper()
            return {"status": "ok"}

        elif action == "goto":
            idx = int(req.get("index", 1)) - 1
            if 0 <= idx < len(self.sources):
                self.current_index = idx
                self.apply_current_wallpaper()
                return {"status": "ok"}
            return {"status": "error", "message": "Index out of range"}

        elif action == "add":
            src = req.get("source")
            if src:
                resolved = resolve_media_sources([src])
                self.sources.extend(resolved)
                return {"status": "ok", "added": len(resolved)}
            return {"status": "error", "message": "No source provided"}

        elif action == "stop":
            self.stop()
            return {"status": "ok"}

        return {"status": "error", "message": f"Unknown action {action}"}

    def start_rotation_timer(self):
        """Cycles wallpapers automatically at specified interval."""
        def rotation_loop():
            while self.running:
                # Sleep interval in small steps so stop/pause responds quickly
                elapsed = 0.0
                while self.running and elapsed < self.interval:
                    time.sleep(0.5)
                    elapsed += 0.5

                if self.running and not self.is_paused and not self.is_screensaver_active and len(self.sources) > 1:
                    self.current_index = (self.current_index + 1) % len(self.sources)
                    self.apply_current_wallpaper()

        self.rotation_thread = threading.Thread(target=rotation_loop, daemon=True)
        self.rotation_thread.start()

    def start_screensaver_monitor(self):
        """Watches user idle time and triggers fullscreen screensaver without stealing input."""
        if not self.screensaver_idle or self.screensaver_idle <= 0:
            return

        def monitor_loop():
            from screensaver import get_idle_time_ms, run_screensaver_overlay
            threshold_ms = self.screensaver_idle * 1000.0

            while self.running:
                time.sleep(1.0)
                idle_ms = get_idle_time_ms()
                if idle_ms is None:
                    continue

                if not self.is_screensaver_active and idle_ms >= threshold_ms:
                    # User is idle, launch screensaver overlay
                    self.is_screensaver_active = True
                    self.screensaver_proc = run_screensaver_overlay(
                        self.screensaver_sources,
                        is_muted=self.is_muted,
                        volume=self.volume
                    )

                    # Monitor for user activity
                    while self.running and self.is_screensaver_active:
                        time.sleep(0.3)
                        current_idle = get_idle_time_ms()
                        # Dismiss when user touches mouse or keyboard
                        if (current_idle is not None and current_idle < 1000) or (self.screensaver_proc and self.screensaver_proc.poll() is not None):
                            if self.screensaver_proc and self.screensaver_proc.poll() is None:
                                self.screensaver_proc.terminate()
                                self.screensaver_proc.wait()
                            self.screensaver_proc = None
                            self.is_screensaver_active = False
                            break

        self.idle_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.idle_thread.start()

    def run(self):
        """Main runner loop."""
        self.running = True
        write_pid(os.getpid())

        # Apply initial wallpaper
        self.apply_current_wallpaper()

        # Start servers and timers
        self.start_ipc_server()
        self.start_rotation_timer()
        self.start_screensaver_monitor()

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.screensaver_proc and self.screensaver_proc.poll() is None:
            self.screensaver_proc.terminate()
        if self.ipc_server_sock:
            try:
                self.ipc_server_sock.close()
            except OSError:
                pass
        cleanup_ipc()
