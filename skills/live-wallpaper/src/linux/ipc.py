import os
import sys
import json
import socket
import signal
import time
from typing import Optional, Dict, Any, Callable

CACHE_DIR = os.path.expanduser("~/.cache/live-wallpaper")
SOCKET_PATH = os.path.join(CACHE_DIR, "ipc.sock")
PID_FILE = os.path.join(CACHE_DIR, "live-wallpaper.pid")
MPV_SOCKET = os.path.join(CACHE_DIR, "mpv.sock")

def ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)

def write_pid(pid: int):
    ensure_cache_dir()
    with open(PID_FILE, "w") as f:
        f.write(str(pid))

def read_pid() -> Optional[int]:
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, "r") as f:
            return int(f.read().strip())
    except (ValueError, IOError):
        return None

def is_running() -> bool:
    pid = read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        # Process dead, cleanup stale pid
        cleanup_ipc()
        return False

def cleanup_ipc():
    if os.path.exists(SOCKET_PATH):
        try:
            os.remove(SOCKET_PATH)
        except OSError:
            pass
    if os.path.exists(MPV_SOCKET):
        try:
            os.remove(MPV_SOCKET)
        except OSError:
            pass
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

def send_command(cmd: Dict[str, Any], timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    """Sends JSON command to running daemon unix socket."""
    if not os.path.exists(SOCKET_PATH):
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(SOCKET_PATH)
        s.sendall(json.dumps(cmd).encode("utf-8") + b"\n")
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in chunk:
                break
        s.close()
        if data:
            return json.loads(data.decode("utf-8"))
    except Exception:
        pass
    return None

def stop_running() -> bool:
    """Stops the running daemon cleanly."""
    if not is_running():
        print("No active live-wallpaper daemon running.")
        return False

    res = send_command({"action": "stop"})
    if res and res.get("status") == "ok":
        print("Stopping live-wallpaper daemon...")
        for _ in range(30):
            if not is_running():
                cleanup_ipc()
                print("Stopped successfully.")
                return True
            time.sleep(0.1)

    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.3)
            if is_running():
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    cleanup_ipc()
    print("Stopped.")
    return True
