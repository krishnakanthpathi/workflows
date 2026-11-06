---
name: live-wallpaper
description: "Cross-platform macOS and Linux live wallpaper and screensaver engine. Uses modular Swift and AppKit/AVFoundation on macOS (with native Lock Screen dynamic video playback), and Python, GTK, and mpv with GPU acceleration on Linux. Supports local video wallpapers, images, playlist queues, per-desktop space/monitor mapping, hardware idle-triggered screensavers, wake-on-input dismissals, directory scanning, background daemonizing (-d), audio control, streaming URLs (HTTP/HTTPS/HLS), and LaunchAgent (macOS) / systemd (Linux) auto-start."
version: 2.4.1
author: Krishna Kanth
license: MIT
platforms: [macos, linux]
metadata:
  icon: "🖼️"
hermes:
  tags: [macos, linux, swift, python, mpv, wallpaper, live-wallpaper, screensaver, lock-screen, avfoundation, desktop, media, queue, images, wayland, x11, spaces, low-power]
  related_skills: [media-processor, macos-python-ui]
---

# 🖼️ Cross-Platform Live Wallpaper, Screensaver & Dynamic Lock Screen Engine

High-performance, dual-platform desktop wallpaper and screensaver runner. Renders dynamic videos (MP4, MOV, WebM, MKV, HLS) and high-res images (PNG, JPG, HEIC, WebP) directly onto the desktop layer behind desktop icons, elevates to a full-screen screensaver overlay above all windows when the system is idle with GPU hardware acceleration, and on macOS continuously injects custom videos into the native Aerial engine so your video **actually plays live on the Lock Screen**!

---

## ⚡ Architecture by Platform

### macOS Architecture (`src/macos/*.swift`)
```
Layer 1000:        [SCREENSAVER OVERLAY] (NSWindow.Level.screenSaver)   ◄── On Idle / Wake-on-input / Lock
Layer    0:        Regular Application Windows (Chrome, Terminal, IDE)
Layer -2147483603: Finder Desktop Layer (Desktop icons, shortcuts)     ◄── Desktop Top
Layer -2147483604: [LIVE WALLPAPER ENGINE] (AVPlayerLayer/CALayer)     ◄── Behind Icons
Layer -2147483624: macOS System Wallpaper (WindowManager)             ◄── Desktop Bottom & Native Lock Screen
```
* **Live Video on Lock Screen**: Injects the active video directly into the native macOS Aerial Lock Screen engine (`~/Library/Application Support/com.apple.wallpaper/aerials/videos/`) via zero-loss AVFoundation passthrough remuxing. When the Mac locks, `WallpaperAgent` plays your video natively at 60/120Hz on the Lock Screen!
* **Safe Automatic Backups & Reversion**: Every original macOS Aerial asset is backed up using zero-cost APFS clones before modification. Revert anytime with `live-wallpaper restore-lockscreen`.
* **Zero-Power Lock Mode (`com.apple.screenIsLocked`)**: Observes system-wide distributed lock events. The desktop AppKit overlay automatically pauses video decoding while locked to eliminate duplicate decoding and save 100% battery, while the native lock screen handles hardware playback.
* **Instant Lock Trigger (`live-wallpaper lock`)**: Synchronizes the current wallpaper to both desktop and lock screen engines and immediately invokes native macOS lock via `SACLockScreenImmediate`.
* **Lock on Screensaver Wake (`--lock`)**: Arms secure wake mode so any wake event from the screensaver overlay immediately prompts the macOS login lock screen.
* **Native Hardware Space Pinning (0ms Latency)**: Pins dedicated windows directly to Mission Control space IDs via SkyLight `CGSAddWindowsToSpaces`. Wallpapers physically slide with trackpad gestures at 120Hz ProMotion without crossfade hacks.

### Linux Architecture (`src/linux/*.py`)
* **Dual Display Server Support**: Works automatically on **Wayland** (GNOME, Sway, Hyprland) and **X11** (KDE, XFCE, i3/bspwm).
* **Native GNOME Background API on Wayland**: Avoids black screens and input hijacking by writing dynamic rendering pipes to standard desktop schemas (`org.gnome.desktop.background`).
* **mpv GPU Hardware Acceleration**: Embedded `libmpv` renders 4K/60fps video at `<1%` CPU utilizing VA-API/NVDEC.
* **systemd User Service Integration**: Installs clean auto-starting systemd user units (`live-wallpaper.service`).

---

## 📁 Source File Organization

```
skills/live-wallpaper/
├── bin/
│   └── live-wallpaper         # Cross-platform entrypoint & OS dispatch launcher
├── scripts/
│   ├── build.sh               # Dual-platform compilation & dependency installer
│   └── setup-linux.sh         # Linux apt/dnf/pacman dependency installer
└── src/
    ├── macos/                 # Native Swift Engine (macOS)
    │   ├── Models.swift       # Structs, Enums, CLI options
    │   ├── SkyLight.swift     # macOS Private CGS APIs (Space IDs)
    │   ├── MediaResolver.swift# Directory scanning & format detection
    │   ├── Renderers.swift    # SpaceWallpaperWindow & ScreenRenderer
    │   ├── Screensaver.swift  # ScreensaverWindow, frosted glass HUD clock
    │   ├── LockScreen.swift   # Dynamic macOS Aerial Lock Screen injection
    │   ├── WallpaperApp.swift # AppKit application orchestrator
    │   ├── IPC.swift          # POSIX signal IPC dispatch & status
    │   ├── Service.swift      # macOS LaunchAgent installer
    │   └── main.swift         # macOS CLI entrypoint
    └── linux/                 # Native Python/mpv Engine (Linux)
        ├── __init__.py
        ├── models.py          # Configuration models & state tracking
        ├── engine.py          # mpv playback & GTK desktop window layering
        ├── screensaver.py     # Screensaver overlay & idle monitoring
        ├── ipc.py             # Unix socket IPC & command dispatch
        ├── service.py         # systemd user service installer & manager
        └── main.py            # Linux CLI entrypoint
```

---

## 🚀 Quick Command Reference

The compiled/linked binary resides in `~/.local/bin/live-wallpaper`.

### 1. Lock Screen Control & Live Video Playback (macOS)

```bash
# Immediately sync current wallpaper (desktop + dynamic lock screen video) and lock macOS screen
live-wallpaper lock

# Lock with a specific wallpaper or video
live-wallpaper lock naruto

# Revert macOS lock screen back to original Apple Aerial videos
live-wallpaper restore-lockscreen

# Run daemon with dynamic Lock Screen video injection (default: enabled)
live-wallpaper -d -p ~/Pictures/Wallpapers

# Run with Lock on Screensaver Wake armed
live-wallpaper -d --screensaver 180 --lock ~/Pictures/Wallpapers
```

### 2. Starting the Wallpaper Daemon

```bash
# Run wallpaper daemon in background with a folder of wallpapers
live-wallpaper -d ~/Pictures/Wallpapers

# Run with custom rotation interval (e.g. 30 seconds)
live-wallpaper -d -i 30 ~/Pictures/Wallpapers

# Shuffle playlist queue order
live-wallpaper -d -s -i 60 ~/Pictures/Wallpapers

# Run with multi-monitor / virtual desktop space distribution
live-wallpaper -d -p ~/Pictures/Wallpapers
```

### 3. Screensaver Mode

```bash
# Trigger screensaver immediately (press any key or move mouse to dismiss)
live-wallpaper screensaver

# Run wallpaper daemon with auto-screensaver after 3 minutes (180s) of inactivity
live-wallpaper -d -p --screensaver 180 ~/Pictures/Wallpapers

# Require password unlock when waking from screensaver (macOS)
live-wallpaper -d -p --screensaver 180 --lock ~/Pictures/Wallpapers

# Use a dedicated screensaver folder/video separate from desktop wallpaper
live-wallpaper -d -p --screensaver 300 --screensaver-source ~/Pictures/Screensavers ~/Pictures/Wallpapers
```

### 4. Timed Playlist Queues & Directories

```bash
# Play all wallpapers and images in a folder (rotates every 60s by default)
live-wallpaper -d ~/Pictures/Wallpapers

# Set custom rotation interval (e.g. 30 seconds)
live-wallpaper -d -i 30 ~/Pictures/Wallpapers

# Shuffle playlist queue order
live-wallpaper -d -s -i 60 ~/Pictures/Wallpapers

# Play specific multiple videos and images in a custom queue
live-wallpaper -d video1.mp4 anime-art.png video2.mov
```

### 5. Live Queue Control (Zero Downtime)

```bash
# View active queue with currently playing item, lock sync status, and space bindings
live-wallpaper queue

# Skip to next wallpaper (automatically updates dynamic lock screen video on macOS)
live-wallpaper next

# Go back to previous wallpaper
live-wallpaper prev

# Jump directly to item by index
live-wallpaper goto 4

# Append a new video/image to the active queue dynamically
live-wallpaper add ~/Pictures/Wallpapers/new-art.png
```

### 6. Audio Control

```bash
# Unmute and play at 100% volume
live-wallpaper -d -a /path/to/video.mp4

# Set volume to 35%
live-wallpaper -d -a -v 35 /path/to/video.mp4

# Keep muted (default)
live-wallpaper -d -m /path/to/video.mp4
```

### 7. Streaming URLs

```bash
# Stream online video or HLS directly as wallpaper
live-wallpaper -d "https://example.com/stream.mp4"
live-wallpaper -d "https://example.com/live/playlist.m3u8"
```

### 8. Process & Service Management

```bash
# Check current active wallpaper, PID, lock screen sync, and queue status
live-wallpaper status

# Stop active wallpaper
live-wallpaper stop

# Install as auto-start background service (LaunchAgent on macOS, systemd on Linux)
live-wallpaper service install -p --screensaver 180 --lock ~/Pictures/Wallpapers

# Check service status
live-wallpaper service status

# Uninstall auto-start service
live-wallpaper service uninstall
```
