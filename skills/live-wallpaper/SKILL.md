---
name: live-wallpaper
description: "Native macOS live wallpaper and screensaver engine using Swift, AVFoundation, and AppKit desktop window layering. Supports local video wallpapers, images, playlist queues, per-desktop space mapping with 0ms delay and extreme low-power auto-pause, hardware idle-triggered screensavers, wake-on-input dismissals, directory scanning, background daemonizing (-d), unmuted audio playback, streaming URLs (HTTP/HTTPS/HLS), and LaunchAgent system service auto-start."
version: 2.3.0
author: Krishna Kanth
license: MIT
platforms: [macos]
metadata:
  icon: "🖼️"
hermes:
  tags: [macos, swift, wallpaper, live-wallpaper, screensaver, avfoundation, desktop, media, queue, images, spaces, low-power]
  related_skills: [media-processor, macos-python-ui]
---

# 🖼️ macOS Live Wallpaper & Screensaver Engine

High-performance, native macOS desktop wallpaper and screensaver runner built in modular Swift. Renders dynamic videos (MP4, MOV, WebM, HLS) and high-res images (PNG, JPG, HEIC, WebP) directly onto the macOS desktop layer behind Finder icons, and elevates to a full-screen screensaver overlay above all windows when the system is idle using Apple Silicon hardware acceleration (`~0.4%` CPU).

---

## ⚡ Core Architecture & Layering

```
Layer 1000:        [SCREENSAVER OVERLAY] (NSWindow.Level.screenSaver)   ◄── On Idle / Wake-on-input
Layer    0:        Regular Application Windows (Chrome, Terminal, IDE)
Layer -2147483603: Finder Desktop Layer (Desktop icons, shortcuts)     ◄── Desktop Top
Layer -2147483604: [LIVE WALLPAPER ENGINE] (AVPlayerLayer/CALayer)     ◄── Behind Icons
Layer -2147483624: macOS System Wallpaper (WindowManager)             ◄── Desktop Bottom
```

* **Native Hardware Space Pinning (0ms Latency)**: Pins dedicated windows directly to Mission Control space IDs via SkyLight `CGSAddWindowsToSpaces`. Wallpapers physically slide with trackpad gestures at 120Hz ProMotion without post-swipe switching lag.
* **Full-Screen Screensaver Overlay**: Elevated to `NSWindow.Level.screenSaver` (Layer 1000) covering all windows, menu bar, and dock. Includes a minimal HUD clock and instant wake-on-input dismissals via Quartz and IOKit.
* **Extreme Low-Power Auto-Pause**: Automatically pauses video decoding on inactive spaces. Keeps `VTDecoderXPCService` memory tiny (`~48 MB` instead of `1 GB+`) and CPU usage at `<2-5%` of one core.
* **Modular Swift Architecture**: Decoupled single-responsibility modules under `src/` for clean maintainability and rapid extension.
* **POSIX IPC Control**: Real-time signal and command dispatch (`next`, `prev`, `goto`, `add`, `screensaver`) without stopping the background daemon.

---

## 📦 Modular Source Layout (`src/`)

| Module | Responsibility |
| :--- | :--- |
| **`Models.swift`** | `QueueItem`, `MediaType`, `EngineState`, state and media file path constants |
| **`SkyLight.swift`** | SkyLight CGS private framework bindings, space enumeration, and window pinning |
| **`MediaResolver.swift`** | Directory traversal, format detection, URL handling, and source expansion |
| **`Renderers.swift`** | `SpaceWallpaperWindow` (per-space hardware sliding) & `ScreenRenderer` (regular desktop) |
| **`Screensaver.swift`** | `ScreensaverWindow`, IOHIDSystem idle detection, and wake-on-input global monitors |
| **`WallpaperApp.swift`** | `NSApplicationDelegate` orchestrator, space synchronization, and playback loop |
| **`IPC.swift`** | POSIX signal (`SIGUSR1`) command dispatch, PID tracking, queue/status inspection |
| **`Service.swift`** | macOS LaunchAgent (`~/Library/LaunchAgents`) plist installer and manager |
| **`main.swift`** | CLI entry point, argument parser, and command router |

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

### 2. Screensaver Mode

```bash
# Trigger screensaver immediately (or test standalone overlay)
live-wallpaper screensaver

# Run wallpaper daemon with auto-screensaver after 3 minutes (180s) of inactivity
live-wallpaper -d -p --screensaver 180 ~/Pictures/Wallpapers

# Use a dedicated screensaver folder/video separate from desktop wallpaper
live-wallpaper -d -p --screensaver 300 --screensaver-source ~/Pictures/Screensavers ~/Pictures/Wallpapers
```

### 3. Timed Playlist Queues & Directories

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

### 4. Live Queue Control (Zero Downtime)

```bash
# View active queue with currently playing item, screensaver status, and space bindings
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

### 5. Audio Control

```bash
# Unmute and play at 100% volume
live-wallpaper -d -a /path/to/video.mp4

# Set custom volume (e.g. 35%)
live-wallpaper -d -a -v 35 /path/to/video.mp4

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

# Install as macOS LaunchAgent service with screensaver support
live-wallpaper service install -p --screensaver 180 ~/Pictures/Wallpapers

# Check service status
live-wallpaper service status

# Uninstall macOS LaunchAgent service
live-wallpaper service uninstall
```

---

## 🛠️ Build & Installation

To rebuild and install the modular engine from source:

```bash
cd /Users/krishnakanth/Projects/workflow/skills/live-wallpaper
./scripts/build.sh
```
