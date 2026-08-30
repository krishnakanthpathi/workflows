---
name: android-edge-sentinel
description: Control and monitor Android Termux edge nodes, 24/7 power outage & UPS sentinels, 32-sensor telemetry, high-FPS camera streaming, GNSS geolocation, and hardware actuators over Tailscale mesh.
version: 1.0.0
author: Krishna Kanth
license: MIT
---

# Android Edge Sentinel & Hardware Gateway Skill

Comprehensive skill for managing, controlling, and automating Android devices running Termux as low-power edge nodes in a homelab. Includes 24/7 power outage monitoring, hardware actuator control, 32-sensor telemetry, high-FPS camera streaming, GNSS geolocation, and cross-device clipboard synchronization over Tailscale mesh.

---

## 📱 Hardware & Node Specifications

* **Node Model**: realme XT (Qualcomm Snapdragon 712, 8-Core ARM64 / `aarch64`, 8GB RAM, Android 11)
* **Tailscale Mesh IP**: `100.123.244.85` (Hostname: `srsxb13`)
* **Local Subnet IP**: `192.168.31.139`
* **SSH Remote Access**: Port `8022` (`u0_a742@100.123.244.85`)
* **Web Dashboard & REST Gateway**: Port `8000` (`http://100.123.244.85:8000`)
* **Auto-Start Daemon**: `~/.termux/boot/start-sshd.sh` via `Termux:Boot`

---

## ⚡ Core Capabilities

1. **⚡ 24/7 Power Outage & UPS Sentinel**:
   * Continuous charger state detection (5s polling interval).
   * Automatically triggers Android notification banners, high-priority audible alarms, and spoken voice warnings upon power cuts.
   * Maintains an in-memory chronological event log of all power interruptions.

2. **📍 Real-Time GNSS & Geolocation**:
   * Queries hardware GPS satellite receiver directly (`termux-location -p gps -r once`).
   * Provides latitude, longitude, altitude, horizontal accuracy ($\pm\text{m}$), speed, and bearing.
   * Interactive OpenStreetMap viewport and direct Google Maps link.

3. **📹 High-FPS Asynchronous Camera & Vision Engine**:
   * Background frame-capture worker continuously buffers frames to RAM.
   * Ultra-low latency image delivery (`/api/camera/frame/fast`).
   * Dual sensor support: Rear camera (Sensor 0, up to $3000 \times 4000$ 4K) & Front camera (Sensor 1).
   * Automatic sensor sleep when stream is stopped to conserve battery.

4. **🎛️ Physical Hardware Actuators**:
   * **Torch**: Toggle camera LED flashlight ON/OFF.
   * **Haptics**: Trigger vibration pulses (300ms, 500ms, 1000ms).
   * **Text-to-Speech (TTS)**: Synthesize speech directly through the device speaker.
   * **Toast & Notifications**: Push native Android popups and notification cards.

5. **💻 Remote Terminal & System Telemetry**:
   * Interactive web terminal console with preset quick pills (`top`, `htop`, `ifconfig`, `df -h`, `free -h`, `ps aux`).
   * Real-time 8-core CPU load averages, RAM allocation, and node uptime.
   * Cross-device clipboard read and write sync.

---

## 🚀 Quick Reference Commands

### 1. REST API Endpoints

```bash
# Check Node Status & Uptime
curl -s http://100.123.244.85:8000/api/status

# Get Full Telemetry & Battery
curl -s http://100.123.244.85:8000/api/dashboard/all

# Query Live GPS Fix
curl -s "http://100.123.244.85:8000/api/location/fix?provider=gps&request=once"

# Toggle Flashlight Torch
curl -X POST http://100.123.244.85:8000/api/torch -H "Content-Type: application/json" -d '{"state": "on"}'
curl -X POST http://100.123.244.85:8000/api/torch -H "Content-Type: application/json" -d '{"state": "off"}'

# Trigger Haptic Vibration
curl -X POST http://100.123.244.85:8000/api/vibrate -H "Content-Type: application/json" -d '{"duration_ms": 500}'

# Voice Speech Synthesis (TTS)
curl -X POST http://100.123.244.85:8000/api/tts -H "Content-Type: application/json" -d '{"text": "Alert: Sentinel online"}'

# Download 4K Camera Snapshot
curl -s "http://100.123.244.85:8000/api/camera/snap?camera=0" --output snap.jpg

# Execute Remote Terminal Command
curl -X POST http://100.123.244.85:8000/api/terminal -H "Content-Type: application/json" -d '{"command": "uptime"}'
```

### 2. Python Client SDK

Use the included CLI client helper script:
```bash
python3 /Users/krishnakanth/.gemini/config/skills/android-edge-sentinel/scripts/client.py --status
python3 /Users/krishnakanth/.gemini/config/skills/android-edge-sentinel/scripts/client.py --speak "Homelab Sentinel is running"
python3 /Users/krishnakanth/.gemini/config/skills/android-edge-sentinel/scripts/client.py --torch on
python3 /Users/krishnakanth/.gemini/config/skills/android-edge-sentinel/scripts/client.py --gps
python3 /Users/krishnakanth/.gemini/config/skills/android-edge-sentinel/scripts/client.py --snap output.jpg
```

---

## 🛠️ Service Management & Troubleshooting

### Restart Gateway Service on Phone
```bash
ssh u0_a742@100.123.244.85 -p 8022 "tmux kill-session -t sentinel 2>/dev/null; tmux new -d -s sentinel 'python3 ~/edge_sentinel.py'"
```

### Inspect Live Sentinel Logs
```bash
ssh u0_a742@100.123.244.85 -p 8022 "tmux capture-pane -pt sentinel -S -50"
```

### Interactive Process Viewer (`htop`)
```bash
ssh u0_a742@100.123.244.85 -p 8022 -t "htop"
```

---

## 🔒 Important Operating Constraints

1. **POSIX Path Storage Constraint**:
   * Android Scoped Storage truncates zero-byte files if camera/audio streams write directly into `/sdcard/Download/`. Always write output to internal POSIX path (`~/snap.jpg`) first before moving or serving over HTTP.
2. **IPC Socket Non-Blocking Concurrency**:
   * `termux-api` commands communicate over a single Android IPC broadcast receiver. Use in-memory caching and background worker threads to prevent socket locking.
