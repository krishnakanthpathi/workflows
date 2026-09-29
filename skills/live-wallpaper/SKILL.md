---
name: live-wallpaper
description: "Native macOS live wallpaper engine using Swift, AVFoundation, and AppKit desktop window layering. Supports local video wallpapers, images, playlist queues, per-desktop space mapping with 0ms delay and extreme low-power auto-pause, directory scanning, background daemonizing (-d), unmuted audio playback, streaming URLs (HTTP/HTTPS/HLS), and LaunchAgent system service auto-start."
version: 2.2.0
author: Krishna Kanth
license: MIT
platforms: [macos]
metadata:
  icon: "🖼️"
hermes:
  tags: [macos, swift, wallpaper, live-wallpaper, avfoundation, desktop, media, queue, images, spaces, low-power]
  related_skills: [media-processor, macos-python-ui]
---

# 🖼️ macOS Live Wallpaper Engine

High-performance, native macOS desktop wallpaper runner built in Swift. Renders dynamic videos (MP4, MOV, WebM, HLS) and high-res images (PNG, JPG, HEIC, WebP) directly onto the macOS desktop layer behind Finder icons and above the system static wallpaper using Apple Silicon hardware acceleration (`~0.4%` CPU).

---

## ⚡ Core Architecture

```
Layer   0: Regular Application Windows (Chrome, Terminal, IDE)
Layer -2147483603: Finder Desktop Layer (Desktop icons, shortcuts)  ◄── Top
Layer -2147483604: [LIVE WALLPAPER ENGINE] (AVPlayerLayer/CALayer)  ◄── Window Level
Layer -2147483624: macOS System Wallpaper (WindowManager)          ◄── Bottom
```

* **Native Hardware Space Pinning (0ms Latency)**: Pins dedicated windows directly to Mission Control space IDs via SkyLight `CGSAddWindowsToSpaces`. Wallpapers physically slide with trackpad gestures at 120Hz ProMotion without post-swipe switching lag.
* **Extreme Low-Power Auto-Pause**: Automatically pauses video decoding on inactive spaces. Keeps `VTDecoderXPCService` memory tiny (`~48 MB` instead of `1 GB+`) and CPU usage at `<2-5%` of one core.
* **Multi-Monitor Display Offsetting**: Connected physical monitors render distinct wallpapers from the queue simultaneously.
* **Multi-Format Support**: Hardware-accelerated video decoding (`AVPlayerLayer` / `AVPlayerLooper`) and retina image rendering (`CALayer` with `.resizeAspectFill`).
* **Click-Through Transparency**: `window.ignoresMouseEvents = true` passes all mouse clicks and drags directly to Finder desktop items.
* **Space Awareness**: `collectionBehavior = [.stationary, .ignoresCycle]` ensures windows stay strictly pinned to designated spaces.
* **POSIX IPC Control**: Real-time signal and command dispatch (`next`, `prev`, `goto`, `add`) without stopping the daemon.

---

## 🚀 Quick Command Reference

The compiled binary resides in `~/.local/bin/live-wallpaper`.

### 1. Per-Desktop Space Mapping (Swipe Between Desktops)

```bash
# Bind each Mission Control virtual desktop to a distinct wallpaper (0ms delay & low power)
live-wallpaper -d -p ~/Pictures/Wallpapers

# Check active desktop space and mapped wallpapers
live-wallpaper queue
```

### 2. Timed Playlist Queues & Directories

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

### 3. Live Queue Control (Zero Downtime)

```bash
# View active queue with currently playing item and space bindings
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

### 4. Single Video / Image Playback

```bash
# Play single video (loops infinitely)
live-wallpaper -d /path/to/video.mp4

# Display static high-res image behind desktop icons
live-wallpaper -d /path/to/wallpaper.png
```

### 5. Audio Control

```bash
# Unmute and play at 100% volume
live-wallpaper -d -a /path/to/video.mp4

# Set custom volume (e.g. 35%)
live-wallpaper -d -a --volume 35 /path/to/video.mp4

# Mute audio (default)
live-wallpaper -d -m /path/to/video.mp4
```

### 6. Streaming URLs

```bash
# Stream online video or HLS directly as wallpaper
live-wallpaper -d "https://example.com/stream.mp4"
live-wallpaper -d "https://example.com/live/playlist.m3u8"
```

### 7. Process & Service Management

```bash
# Check current active wallpaper, PID, and queue status
live-wallpaper status

# Stop active wallpaper
live-wallpaper stop

# Install as macOS LaunchAgent service (starts automatically on login)
live-wallpaper service install -p ~/Pictures/Wallpapers

# Check service status
live-wallpaper service status

# Uninstall macOS LaunchAgent service
live-wallpaper service uninstall
```

---

## 🛠️ Build & Installation

To rebuild and reinstall the engine from source:

```bash
cd /Users/krishnakanth/Projects/workflow/skills/live-wallpaper
./scripts/build.sh
```
