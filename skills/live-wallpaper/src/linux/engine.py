import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import time
import json
import shutil
import socket
import select
import threading
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

from models import resolve_media_sources, MediaItem
from ipc import (
    SOCKET_PATH,
    PID_FILE,
    MPV_SOCKET,
    CACHE_DIR,
    write_pid,
    cleanup_ipc,
    ensure_cache_dir
)

def find_mpv_binary() -> tuple[str, dict]:
    """Locates mpv binary and builds required environment."""
    env = os.environ.copy()
    share_dir = os.path.expanduser("~/.local/share/live-wallpaper")
    local_mpv = os.path.join(share_dir, "bin", "mpv")
    local_lib = os.path.join(share_dir, "lib")

    if shutil.which("mpv"):
        return shutil.which("mpv"), env

    if os.path.isfile(local_mpv) and os.access(local_mpv, os.X_OK):
        env["LD_LIBRARY_PATH"] = f"{local_lib}:" + env.get("LD_LIBRARY_PATH", "")
        return local_mpv, env

    # Run setup script if missing
    setup_script = os.path.expanduser("~/workflows/skills/live-wallpaper/scripts/setup-linux.sh")
    if os.path.exists(setup_script):
        subprocess.run(["bash", setup_script], check=False)
        if os.path.isfile(local_mpv):
            env["LD_LIBRARY_PATH"] = f"{local_lib}:" + env.get("LD_LIBRARY_PATH", "")
            return local_mpv, env

    raise RuntimeError("mpv binary not found. Please install mpv: sudo apt install mpv")

def send_mpv_command(cmd: List[Any], timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """Sends JSON-RPC command to mpv's unix socket."""
    if not os.path.exists(MPV_SOCKET):
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(MPV_SOCKET)
        payload = json.dumps({"command": cmd}) + "\n"
        s.sendall(payload.encode("utf-8"))
        
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in chunk:
                break
        s.close()
        for line in data.decode("utf-8").strip().split("\n"):
            if line:
                parsed = json.loads(line)
                if "error" in parsed:
                    return parsed
    except Exception:
        pass
    return None

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

        self.mpv_proc: Optional[subprocess.Popen] = None
        self.screensaver_proc: Optional[subprocess.Popen] = None
        self.is_screensaver_active = False
        self.running = False
        self.gtk_window = None
        self.ipc_server_sock = None
        self.ipc_thread = None
        self.idle_thread = None

    def create_desktop_window(self) -> int:
        """Creates desktop-level X11/Xwayland GTK window and returns its XID."""
        os.environ["GDK_BACKEND"] = "x11"
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("GdkX11", "3.0")
        from gi.repository import Gtk, Gdk, GdkX11

        win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        win.set_title("LiveWallpaper-Desktop")
        win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        win.set_keep_below(True)
        win.set_skip_taskbar_hint(True)
        win.set_skip_pager_hint(True)
        win.set_accept_focus(False)
        win.set_focus_on_map(False)
        win.set_decorated(False)
        win.fullscreen()
        win.show_all()

        xid = win.get_window().get_xid()
        self.gtk_window = win
        return xid

    def start_mpv(self, xid: int):
        """Launches mpv embedded into desktop window."""
        mpv_bin, env = find_mpv_binary()
        ensure_cache_dir()
        if os.path.exists(MPV_SOCKET):
            try:
                os.remove(MPV_SOCKET)
            except OSError:
                pass

        cmd = [
            mpv_bin,
            f"--wid={xid}",
            f"--input-ipc-server={MPV_SOCKET}",
            "--idle=yes",
            "--loop-playlist=inf",
            "--hwdec=auto",
            "--no-osc",
            "--no-osd-bar",
            "--no-input-default-bindings",
            "--keep-open=yes",
            f"--image-display-duration={self.interval}",
            f"--mute={'yes' if self.is_muted else 'no'}",
            f"--volume={int(self.volume * 100)}"
        ]

        if self.shuffle:
            cmd.append("--shuffle=yes")

        # Create temporary playlist file for robust loading
        playlist_file = os.path.join(CACHE_DIR, "playlist.txt")
        with open(playlist_file, "w") as f:
            for s in self.sources:
                f.write(s + "\n")

        cmd.append(f"--playlist={playlist_file}")

        self.mpv_proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait briefly for mpv socket
        for _ in range(30):
            if os.path.exists(MPV_SOCKET):
                break
            time.sleep(0.1)

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
            path_res = send_mpv_command(["get_property", "path"])
            pos_res = send_mpv_command(["get_property", "playlist-pos"])
            count_res = send_mpv_command(["get_property", "playlist-count"])
            pause_res = send_mpv_command(["get_property", "pause"])
            vol_res = send_mpv_command(["get_property", "volume"])
            mute_res = send_mpv_command(["get_property", "mute"])

            return {
                "status": "ok",
                "pid": os.getpid(),
                "mode": "Screensaver" if self.is_screensaver_active else "Wallpaper",
                "current_path": path_res.get("data") if path_res else None,
                "current_index": (pos_res.get("data", 0) + 1) if pos_res else 1,
                "total_items": count_res.get("data", len(self.sources)) if count_res else len(self.sources),
                "is_paused": pause_res.get("data", False) if pause_res else False,
                "volume": vol_res.get("data", int(self.volume * 100)) if vol_res else int(self.volume * 100),
                "is_muted": mute_res.get("data", self.is_muted) if mute_res else self.is_muted
            }

        elif action == "queue":
            res = send_mpv_command(["get_property", "playlist"])
            playlist_items = []
            if res and "data" in res:
                for item in res["data"]:
                    playlist_items.append({
                        "path": item.get("filename"),
                        "current": item.get("current", False),
                        "id": item.get("id")
                    })
            return {"status": "ok", "queue": playlist_items}

        elif action == "next":
            send_mpv_command(["playlist-next"])
            return {"status": "ok"}

        elif action == "prev":
            send_mpv_command(["playlist-prev"])
            return {"status": "ok"}

        elif action == "goto":
            idx = int(req.get("index", 1)) - 1
            send_mpv_command(["playlist-play-index", max(0, idx)])
            return {"status": "ok"}

        elif action == "add":
            src = req.get("source")
            if src:
                resolved = resolve_media_sources([src])
                for item in resolved:
                    send_mpv_command(["loadfile", item, "append"])
                    self.sources.append(item)
                return {"status": "ok", "added": len(resolved)}
            return {"status": "error", "message": "No source provided"}

        elif action == "stop":
            self.stop()
            return {"status": "ok"}

        return {"status": "error", "message": f"Unknown action {action}"}

    def start_screensaver_monitor(self):
        """Watches user idle time and triggers fullscreen screensaver."""
        if not self.screensaver_idle or self.screensaver_idle <= 0:
            return

        def monitor_loop():
            from .screensaver import get_idle_time_ms, run_screensaver_overlay
            threshold_ms = self.screensaver_idle * 1000.0

            while self.running:
                time.sleep(1.0)
                idle_ms = get_idle_time_ms()
                if idle_ms is None:
                    continue

                if not self.is_screensaver_active and idle_ms >= threshold_ms:
                    # User is idle, trigger screensaver
                    self.is_screensaver_active = True
                    send_mpv_command(["set_property", "pause", True])

                    # Launch screensaver overlay
                    mpv_bin, env = find_mpv_binary()
                    self.screensaver_proc = run_screensaver_overlay(
                        self.screensaver_sources,
                        is_muted=self.is_muted,
                        volume=self.volume,
                        mpv_bin=mpv_bin,
                        env=env
                    )

                    # Wait for activity to dismiss
                    while self.running and self.is_screensaver_active:
                        time.sleep(0.3)
                        current_idle = get_idle_time_ms()
                        # Dismiss when user touches mouse/keyboard or screensaver quits
                        if (current_idle is not None and current_idle < 1000) or (self.screensaver_proc and self.screensaver_proc.poll() is not None):
                            if self.screensaver_proc and self.screensaver_proc.poll() is None:
                                self.screensaver_proc.terminate()
                                self.screensaver_proc.wait()
                            self.screensaver_proc = None
                            self.is_screensaver_active = False
                            send_mpv_command(["set_property", "pause", False])
                            break

        self.idle_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.idle_thread.start()

    def run(self):
        """Main runner loop."""
        self.running = True
        write_pid(os.getpid())

        # Create background desktop layer
        xid = self.create_desktop_window()
        self.start_mpv(xid)
        self.start_ipc_server()
        self.start_screensaver_monitor()

        # Run GTK event loop
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, GLib

        def check_proc():
            if not self.running or (self.mpv_proc and self.mpv_proc.poll() is not None):
                Gtk.main_quit()
                return False
            return True

        GLib.timeout_add(1000, check_proc)
        try:
            Gtk.main()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.screensaver_proc and self.screensaver_proc.poll() is None:
            self.screensaver_proc.terminate()
        if self.mpv_proc and self.mpv_proc.poll() is None:
            send_mpv_command(["quit"])
            try:
                self.mpv_proc.terminate()
            except OSError:
                pass
        if self.ipc_server_sock:
            try:
                self.ipc_server_sock.close()
            except OSError:
                pass
        cleanup_ipc()
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        if Gtk.main_level() > 0:
            Gtk.main_quit()
