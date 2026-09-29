---
name: live-wallpaper
description: "Native macOS live wallpaper engine using Swift, AVFoundation, and AppKit desktop window layering. Supports local video wallpapers, background daemonizing (-d), unmuted audio playback, streaming URLs (HTTP/HTTPS/HLS), and LaunchAgent system service auto-start."
version: 1.0.0
author: Krishna Kanth
license: MIT
platforms: [macos]
metadata:
  icon: "🖼️"
hermes:
  tags: [macos, swift, wallpaper, live-wallpaper, avfoundation, desktop, media]
  related_skills: [media-processor, macos-python-ui]
---

# 🖼️ macOS Live Wallpaper Engine

High-performance, native macOS live video wallpaper runner built in Swift. Renders directly onto the macOS desktop layer behind Finder icons and above the system static wallpaper using Apple Silicon hardware acceleration via AVFoundation (~1-4% CPU).

---

## ⚡ Core Architecture

```
Layer   0: Regular Application Windows (Chrome, Terminal, IDE)
Layer -2147483603: Finder Desktop Layer (Desktop icons, shortcuts)  ◄── Top
Layer -2147483604: [LIVE WALLPAPER ENGINE] (AVPlayerLayer)         ◄── Window Level
Layer -2147483624: macOS System Wallpaper (WindowManager)          ◄── Bottom
```

* **Click-Through Transparency**: `window.ignoresMouseEvents = true` passes all mouse clicks and drags directly to Finder desktop items.
* **Space Awareness**: `collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]` ensures the wallpaper stays locked across all Mission Control virtual desktops without sliding.
* **Dynamic Resolution Adapting**: Observes `NSApplication.didChangeScreenParametersNotification` to dynamically adjust or span newly connected/disconnected displays.
* **Hardware Looping**: Uses `AVPlayerLooper` with zero frame-drop hardware decoding.

---

## 🚀 Quick Command Reference

The compiled binary resides in `~/.local/bin/live-wallpaper`.

### 1. Basic Playback & Presets

```bash
# Run in background with built-in presets
live-wallpaper -d naruto
live-wallpaper -d aot

# Play any local MP4/MOV file
live-wallpaper -d /path/to/video.mp4
```

### 2. Audio Control

```bash
# Unmute and play at 100% volume
live-wallpaper -d -a naruto

# Set custom volume (e.g. 35%)
live-wallpaper -d -a --volume 35 naruto

# Mute audio (default)
live-wallpaper -d -m naruto
```

### 3. Streaming URLs

```bash
# Stream online video or HLS directly as wallpaper
live-wallpaper -d "https://example.com/stream.mp4"
live-wallpaper -d "https://example.com/live/playlist.m3u8"
```

### 4. Process & Service Management

```bash
# Check current active wallpaper and PID
live-wallpaper status

# Stop active wallpaper
live-wallpaper stop

# Install as macOS LaunchAgent service (starts automatically on login)
live-wallpaper service install naruto

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
