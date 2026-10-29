import os
import sys
import subprocess
from typing import List

SERVICE_DIR = os.path.expanduser("~/.config/systemd/user")
SERVICE_FILE = os.path.join(SERVICE_DIR, "live-wallpaper.service")

SERVICE_TEMPLATE = """[Unit]
Description=Live Wallpaper and Screensaver Daemon
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart={exec_cmd}
Restart=always
RestartSec=3
Environment=DISPLAY={display}
Environment=WAYLAND_DISPLAY={wayland_display}

[Install]
WantedBy=graphical-session.target default.target
"""

def install_service(raw_args: List[str]):
    """Installs and enables systemd user service."""
    os.makedirs(SERVICE_DIR, exist_ok=True)
    bin_path = os.path.expanduser("~/.local/bin/live-wallpaper")

    # Filter out service subcommands and -d flags for foreground execution in systemd
    filtered_args = []
    skip_next = False
    for i, a in enumerate(raw_args):
        if skip_next:
            skip_next = False
            continue
        if a in ("service", "install", "-d", "--daemon"):
            continue
        filtered_args.append(a)

    exec_cmd = f"{bin_path} " + " ".join(filtered_args)
    content = SERVICE_TEMPLATE.format(
        exec_cmd=exec_cmd,
        display=os.environ.get("DISPLAY", ":0"),
        wayland_display=os.environ.get("WAYLAND_DISPLAY", "wayland-0")
    )

    with open(SERVICE_FILE, "w") as f:
        f.write(content)

    print(f"==> Wrote systemd service to {SERVICE_FILE}")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "--now", "live-wallpaper.service"], check=False)
    print("==> live-wallpaper service installed and started.")
    print("Check status with: live-wallpaper service status")

def uninstall_service():
    """Stops and removes systemd user service."""
    print("==> Disabling and stopping live-wallpaper systemd service...")
    subprocess.run(["systemctl", "--user", "disable", "--now", "live-wallpaper.service"], check=False)
    if os.path.exists(SERVICE_FILE):
        try:
            os.remove(SERVICE_FILE)
            print("==> Removed service file.")
        except OSError as e:
            print(f"Error removing file: {e}")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    print("==> Successfully uninstalled live-wallpaper service.")

def status_service():
    """Prints systemctl status."""
    subprocess.run(["systemctl", "--user", "status", "live-wallpaper.service"])
