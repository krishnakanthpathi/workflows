import os
import sys
import time
import subprocess
from typing import List, Optional

def get_idle_time_ms() -> Optional[float]:
    """Gets user idle time in milliseconds across GNOME Mutter / X11."""
    # 1. GNOME Mutter DBus IdleMonitor
    try:
        from gi.repository import Gio
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor",
            None
        )
        idle_val = proxy.GetIdletime()
        if idle_val is not None:
            return float(idle_val)
    except Exception:
        pass

    # 2. xprintidle command fallback
    try:
        out = subprocess.check_output(["xprintidle"], stderr=subprocess.DEVNULL)
        return float(out.decode().strip())
    except Exception:
        pass

    return None

import shutil

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

    raise RuntimeError("mpv binary not found. Please install mpv: sudo apt install mpv")

def run_screensaver_overlay(
    sources: List[str],
    is_muted: bool = True,
    volume: float = 1.0,
    mpv_bin: Optional[str] = None,
    env: Optional[dict] = None
) -> subprocess.Popen:
    """Launches fullscreen screensaver overlay with instant wake-on-input."""
    if not mpv_bin or not env:
        mpv_bin, env = find_mpv_binary()

    cmd = [
        mpv_bin,
        "--fs",
        "--ontop",
        "--no-border",
        "--no-osc",
        "--no-osd-bar",
        "--loop-playlist=inf",
        "--hwdec=auto",
        "--input-default-bindings=yes",
        f"--mute={'yes' if is_muted else 'no'}",
        f"--volume={int(volume * 100)}",
        "--osd-level=1",
        "--osd-font-size=24",
        "--osd-align-x=right",
        "--osd-align-y=top",
        "--osd-margin-x=40",
        "--osd-margin-y=40"
    ]

    for s in sources:
        cmd.append(s)

    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return proc

def run_standalone_screensaver(sources: List[str]):
    """Launches screensaver immediately and blocks until user dismissal."""
    from models import resolve_media_sources

    resolved = resolve_media_sources(sources)
    if not resolved:
        print("Error: No valid screensaver media sources found.")
        sys.exit(1)

    mpv_bin, env = find_mpv_binary()
    print("Launching screensaver overlay (move mouse or press any key to exit)...")
    proc = run_screensaver_overlay(resolved, is_muted=True, volume=1.0, mpv_bin=mpv_bin, env=env)

    # Monitor idle time for instant wake-on-input
    start_time = time.time()
    try:
        while proc.poll() is None:
            time.sleep(0.2)
            # Give 1 second grace period before detecting mouse movement
            if time.time() - start_time > 1.0:
                idle_ms = get_idle_time_ms()
                if idle_ms is not None and idle_ms < 500:
                    proc.terminate()
                    break
    except KeyboardInterrupt:
        proc.terminate()
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
        print("Screensaver dismissed.")
