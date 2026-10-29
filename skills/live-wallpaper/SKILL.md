---
name: live-wallpaper
description: "Cross-platform macOS and Linux live wallpaper and screensaver engine. Uses modular Swift and AppKit/AVFoundation on macOS, and Python, GTK, and mpv with GPU acceleration on Linux. Supports local video wallpapers, images, playlist queues, per-desktop space/monitor mapping, hardware idle-triggered screensavers, wake-on-input dismissals, directory scanning, background daemonizing (-d), audio control, streaming URLs (HTTP/HTTPS/HLS), and LaunchAgent (macOS) / systemd (Linux) auto-start."
version: 2.4.0
author: Krishna Kanth
license: MIT
platforms: [macos, linux]
metadata:
  icon: "🖼️"
hermes:
  tags: [macos, linux, swift, python, mpv, wallpaper, live-wallpaper, screensaver, desktop, media, queue, images, wayland, x11, low-power]
  related_skills: [media-processor, macos-python-ui]
---

# 🖼️ Cross-Platform Live Wallpaper & Screensaver Engine (macOS & Linux)

High-performance, dual-platform desktop wallpaper and screensaver runner. Renders dynamic videos (MP4, MOV, WebM, MKV, HLS) and high-res images (PNG, JPG, HEIC, WebP) directly onto the desktop layer behind desktop icons, and elevates to a full-screen screensaver overlay above all windows when the system is idle with GPU hardware acceleration.

---

## ⚡ Architecture by Platform

### 🍎 macOS Engine (`src/macos/`)
* **Layering**: Native AppKit desktop window layering (`kCGDesktopWindowLevel - 1`) behind Finder icons.
* **Hardware Space Pinning (0ms Latency)**: Pins windows directly to Mission Control space IDs via SkyLight `CGSAddWindowsToSpaces`.
* **Low-Power Auto-Pause**: Pauses video decoding on inactive spaces.
* **Screensaver**: Elevated to `NSWindow.Level.screenSaver` with frosted glass HUD clock and wake-on-input dismissals.
* **Service**: Managed via macOS LaunchAgent (`~/Library/LaunchAgents`).

### 🐧 Linux Engine (`src/linux/`)
* **Layering**: GTK desktop-level window (`Gdk.WindowTypeHint.DESKTOP`, `set_keep_below(True)`) covering the display geometry behind application windows.
* **Rendering Engine**: Hardware-accelerated `mpv` (`--hwdec=auto`, `--vo=gpu-next`) embedded directly into the desktop window XID.
* **Idle Screensaver**: GNOME Mutter DBus (`org.gnome.Mutter.IdleMonitor`) and X11 idle tracking with instant wake-on-input dismissals.
* **IPC Control**: Unix domain socket (`~/.cache/live-wallpaper/ipc.sock`) supporting zero-downtime queue inspection and manipulation.
* **Service**: Managed via Linux `systemd --user` (`~/.config/systemd/user/live-wallpaper.service`).

---

## 📦 Source Layout

```
skills/live-wallpaper/
├── SKILL.md
├── bin/
│   └── live-wallpaper         # Unified cross-platform CLI dispatcher
├── scripts/
│   ├── build.sh               # Platform builder & installer
│   └── setup-linux.sh         # Linux mpv dependency installer
└── src/
    ├── macos/                 # Swift macOS native engine
    │   ├── IPC.swift
    │   ├── MediaResolver.swift
    │   ├── Models.swift
    │   ├── Renderers.swift
    │   ├── Screensaver.swift
    │   ├── Service.swift
    │   ├── SkyLight.swift
    │   ├── WallpaperApp.swift
    │   └── main.swift
    └── linux/                 # Python Linux engine
        ├── __init__.py
        ├── models.py          # Media discovery & queue models
        ├── ipc.py             # Unix socket IPC client/server & PID manager
        ├── engine.py          # GTK desktop window & mpv runner
        ├── screensaver.py     # Mutter DBus idle detection & screensaver overlay
        ├── service.py         # systemd user service installer & manager
        └── main.py            # Linux CLI entrypoint
```

---

## 🚀 Quick Command Reference

The compiled/linked binary resides in `~/.local/bin/live-wallpaper`.

### 1. Starting the Wallpaper Daemon

```bash
# Run wallpaper daemon in background with a folder of wallpapers
live-wallpaper -d ~/Pictures/Wallpapers

# Run with custom rotation interval (e.g. 30 seconds)
live-wallpaper -d -i 30 ~/Pictures/Wallpapers

# Shuffle playlist queue order
live-wallpaper -d -s -i 60 ~/Pictures/Wallpapers

# Run with multi-monitor / virtual desktop distribution
live-wallpaper -d -p ~/Pictures/Wallpapers
```

### 2. Screensaver Mode

```bash
# Trigger screensaver immediately (press any key or move mouse to dismiss)
live-wallpaper screensaver

# Run wallpaper daemon with auto-screensaver after 3 minutes (180s) of inactivity
live-wallpaper -d -p --screensaver 180 ~/Pictures/Wallpapers

# Use a dedicated screensaver folder/video separate from desktop wallpaper
live-wallpaper -d -p --screensaver 300 --screensaver-source ~/Pictures/Screensavers ~/Pictures/Wallpapers
```

### 3. Live Queue Control (Zero Downtime)

```bash
# View active queue with currently playing item and status
live-wallpaper queue

# Skip to next wallpaper
live-wallpaper next

# Go back to previous wallpaper
live-wallpaper prev

# Jump directly to item #4 in the queue
live-wallpaper goto 4

# Dynamically add a new wallpaper/image to the running queue
live-wallpaper add ~/Pictures/Wallpapers/new-art.png
```

### 4. Audio Control

```bash
# Unmute and play at 100% volume
live-wallpaper -d -a /path/to/video.mp4

# Set custom volume (e.g. 35%)
live-wallpaper -d -a -v 35 /path/to/video.mp4

# Mute audio (default)
live-wallpaper -d -m /path/to/video.mp4
```

### 5. Streaming URLs

```bash
# Stream online video or HLS directly as wallpaper
live-wallpaper -d "https://example.com/stream.mp4"
live-wallpaper -d "https://example.com/live/playlist.m3u8"
```

### 6. Process & Service Management

```bash
# Check current active wallpaper, PID, and queue status
live-wallpaper status

# Stop active wallpaper
live-wallpaper stop

# Install as auto-start background service (LaunchAgent on macOS, systemd on Linux)
live-wallpaper service install -p --screensaver 180 ~/Pictures/Wallpapers

# Check service status
live-wallpaper service status

# Uninstall auto-start service
live-wallpaper service uninstall
```

---

## 🛠️ Build & Installation

To rebuild and install the modular engine from source:

```bash
cd ~/workflows/skills/live-wallpaper
./scripts/build.sh
```
