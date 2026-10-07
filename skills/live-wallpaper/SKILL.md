---
name: live-wallpaper
description: "Native macOS live wallpaper and screensaver engine using Swift, AVFoundation, and AppKit desktop window layering. Supports local video wallpapers, images, playlist queues, native Lock Screen synchronization, zero-power lock detection (0% CPU), per-desktop space mapping with 0ms delay and extreme low-power auto-pause, hardware idle-triggered screensavers, wake-on-input dismissals, directory scanning, background daemonizing (-d), unmuted audio playback, streaming URLs (HTTP/HTTPS/HLS), and LaunchAgent system service auto-start."
version: 2.4.0
author: Krishna Kanth
license: MIT
platforms: [macos]
metadata:
  icon: "🖼️"
hermes:
  tags: [macos, swift, wallpaper, live-wallpaper, screensaver, lock-screen, avfoundation, desktop, media, queue, images, spaces, low-power]
  related_skills: [media-processor, macos-python-ui]
---

# 🖼️ macOS Live Wallpaper, Screensaver & Lock Screen Engine

High-performance, native macOS desktop wallpaper and screensaver runner built in modular Swift. Renders dynamic videos (MP4, MOV, WebM, HLS) and high-res images (PNG, JPG, HEIC, WebP) directly onto the macOS desktop layer behind Finder icons, elevates to a full-screen screensaver overlay above all windows when the system is idle, and continuously synchronizes wallpaper poster frames to the native macOS Lock Screen while automatically pausing decoders on lock (`0% CPU`).

---

## ⚡ Core Architecture & Layering

```
Layer 1000:        [SCREENSAVER OVERLAY] (NSWindow.Level.screenSaver)   ◄── On Idle / Wake-on-input / Lock
Layer    0:        Regular Application Windows (Chrome, Terminal, IDE)
Layer -2147483603: Finder Desktop Layer (Desktop icons, shortcuts)     ◄── Desktop Top
Layer -2147483604: [LIVE WALLPAPER ENGINE] (AVPlayerLayer/CALayer)     ◄── Behind Icons
Layer -2147483624: macOS System Wallpaper (WindowManager)             ◄── Desktop Bottom & Native Lock Screen
```

* **Native Lock Screen Continuity**: Automatically extracts 4K poster frames from video wallpapers (or uses native images) and mirrors them to the macOS system desktop picture via `NSWorkspace`. When macOS locks, the Lock Screen seamlessly displays the current wallpaper!
* **Zero-Power Lock Mode (`com.apple.screenIsLocked`)**: Listens to system-wide distributed lock events. Video decoding (`VTDecoderXPCService`) instantly pauses upon screen lock, saving 100% of GPU/CPU video overhead (`0.0%` CPU) and resumes instantly on unlock.
* **Instant Lock Trigger (`live-wallpaper lock`)**: Synchronizes the current wallpaper and immediately invokes native macOS lock via `SACLockScreenImmediate`.
* **Lock on Screensaver Wake (`--lock`)**: Arms secure wake mode so any wake event from the screensaver overlay immediately prompts the macOS login lock screen.
* **Native Hardware Space Pinning (0ms Latency)**: Pins dedicated windows directly to Mission Control space IDs via SkyLight `CGSAddWindowsToSpaces`. Wallpapers physically slide with trackpad gestures at 120Hz ProMotion without post-swipe switching lag.
* **Modular Swift Architecture**: Decoupled single-responsibility modules under `src/` for clean maintainability and rapid extension.
* **POSIX IPC Control**: Real-time signal and command dispatch (`next`, `prev`, `goto`, `add`, `screensaver`, `lock`) without stopping the background daemon.

---

## 📦 Modular Source Layout (`src/`)

| Module | Responsibility |
| :--- | :--- |
| **`Models.swift`** | `QueueItem`, `MediaType`, `EngineState`, state, cache, and media file path constants |
| **`LockScreen.swift`** | Native `SACLockScreenImmediate` lock trigger, 4K poster frame extraction, cache, and `DistributedNotificationCenter` lock monitors |
| **`SkyLight.swift`** | SkyLight CGS private framework bindings, space enumeration, and window pinning |
| **`MediaResolver.swift`** | Directory traversal, fuzzy name matching, shorthand aliases, format detection, URL handling |
| **`Renderers.swift`** | `SpaceWallpaperWindow` (per-space hardware sliding) & `ScreenRenderer` (regular desktop) |
| **`Screensaver.swift`** | `ScreensaverWindow`, frosted glass HUD clock capsule, IOHIDSystem idle detection, wake-on-input |
| **`WallpaperApp.swift`** | `NSApplicationDelegate` orchestrator, space synchronization, power saving on lock, playback loop |
| **`IPC.swift`** | POSIX signal (`SIGUSR1`) command dispatch, PID tracking, queue/status inspection |
| **`Service.swift`** | macOS LaunchAgent (`~/Library/LaunchAgents`) plist installer and manager |
| **`main.swift`** | CLI entry point, argument parser, and command router |

---

## 🚀 Quick Command Reference

The compiled binary resides in `~/.local/bin/live-wallpaper`.

### 1. Lock Screen Control & Continuity

```bash
# Immediately sync current wallpaper and lock macOS screen
live-wallpaper lock

# Lock with a specific wallpaper or video
live-wallpaper lock naruto

# Run daemon with continuous Lock Screen wallpaper synchronization (default: enabled)
live-wallpaper -d -p ~/Pictures/Wallpapers

# Run with Lock on Screensaver Wake armed
live-wallpaper -d --screensaver 180 --lock ~/Pictures/Wallpapers
```

### 2. Per-Desktop Space Mapping (Swipe Between Desktops)

```bash
# Bind each Mission Control virtual desktop to a distinct wallpaper (0ms delay & low power)
live-wallpaper -d -p ~/Pictures/Wallpapers

# Check active desktop space, lock screen sync status, and mapped wallpapers
live-wallpaper queue
```

### 3. Screensaver Mode

```bash
# Trigger screensaver immediately (or test standalone overlay)
live-wallpaper screensaver

# Run wallpaper daemon with auto-screensaver after 3 minutes (180s) of inactivity
live-wallpaper -d -p --screensaver 180 ~/Pictures/Wallpapers

# Require password unlock when waking from screensaver
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

# Skip to next wallpaper (automatically syncs new poster frame to lock screen)
live-wallpaper next

# Go back to previous wallpaper
live-wallpaper prev

# Jump directly to item #4 in the queue
live-wallpaper goto 4

# Dynamically add a new wallpaper/image to the running queue
live-wallpaper add ~/Pictures/Wallpapers/new-art.png
```

### 6. Audio Control

```bash
# Unmute and play at 100% volume
live-wallpaper -d -a /path/to/video.mp4

# Set custom volume (e.g. 35%)
live-wallpaper -d -a -v 35 /path/to/video.mp4

# Mute audio (default)
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

# Install as macOS LaunchAgent service with screensaver & lock support
live-wallpaper service install -p --screensaver 180 --lock ~/Pictures/Wallpapers

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
