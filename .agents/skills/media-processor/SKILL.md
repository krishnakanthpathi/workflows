---
name: media-processor
description: >-
  Universal media, file, and data processing skill. Inspects, converts, queries, and transforms structured data (CSV, JSON, SQL), images (sips/Pillow), audio/video (ffmpeg), and performs OCR via local Ollama (glm-ocr on localhost) with built-in auto-installation of missing prerequisites, thermal protection, and infinite-loop circuit breakers.
version: 1.0.0
author: Krishna Kanth
platforms: [macos, linux]
metadata:
  tags: [media, ocr, glm-ocr, ollama, ffmpeg, sips, csv, json, sql, processing]
---

# Media Processor Skill

A zero-friction, modular engine to inspect, convert, query, and transform any media file (CSV, JSON, audio, video, images, PDFs) with automatic prerequisite installation and local Ollama integration.

---

## 1. Golden Architecture & Principles

1. **Self-Healing Prerequisites**: Missing Python libraries (`pillow`, `pypdf`) or system binaries (`ffmpeg`) are automatically detected and installed on the fly.
2. **Localhost First**: Ollama is accessed directly on the local machine (`http://localhost:11434`). No remote or LAN IP configurations required.
3. **Thermal & Loop Protection**: Unclear/degraded media can trigger degenerative repetition loops in small VLMs. The OCR runner enforces:
   - `num_thread: 4` (caps CPU load at 50% to prevent hardware overheating)
   - `num_predict: 1500` (caps max tokens to prevent runaway generation)
   - `repeat_penalty: 1.25` (breaks phrase loops)
   - `timeout: 45s` + streaming watchdog (kills hung or repeating requests)
   - `keep_alive: 0` (unloads model to free RAM and cool the CPU)
4. **Cross-Platform**: Uses macOS native `sips` when available, seamlessly falling back to `Pillow` on Linux.

---

## 2. Directory Layout & Key Files

```text
.agents/skills/media-processor/
├── SKILL.md                          # This manual
├── scripts/
│   ├── ensure_prereqs.py             # Auto-installer for missing packages & binaries
│   ├── inspect_media.py              # Universal probe (schema, dimensions, streams)
│   ├── process_media.py              # Unified CLI dispatcher (data, image, audio, video, ocr)
│   └── ocr_ollama.py                 # Ollama OCR client with thermal circuit breakers
├── references/
│   ├── recipes.md                    # Quick one-liner cheatsheet
│   └── formats.md                    # Supported format matrix & capabilities
└── tests/
    └── test_media_processor.py       # Automated test suite
```

---

## 3. How to Use

### A. Auto-Install & Verify Prerequisites
The scripts auto-install missing packages on invocation. You can also run the repair manually:
```bash
python3 .agents/skills/media-processor/scripts/ensure_prereqs.py
```

### B. Inspect Any File
Run before processing to determine file type, size, dimensions, or schema:
```bash
python3 .agents/skills/media-processor/scripts/inspect_media.py /path/to/any_file
```

### C. OCR & Document Extraction (via Localhost Ollama)
Extract clean Markdown, LaTeX formulas, and tables from images/scans:
```bash
# Standard run (dispatches to localhost:11434)
python3 .agents/skills/media-processor/scripts/process_media.py ocr /path/to/document.jpg -o output.md

# Custom options (e.g. limit to 800 tokens, unload immediately)
python3 .agents/skills/media-processor/scripts/process_media.py ocr /path/to/scan.png --max-tokens 800 --unload
```

### D. Tabular Data (CSV, JSON, SQL)
```bash
# Convert formats
python3 .agents/skills/media-processor/scripts/process_media.py data convert input.csv output.json
python3 .agents/skills/media-processor/scripts/process_media.py data convert input.json output.csv

# Query data with SQL in-memory
python3 .agents/skills/media-processor/scripts/process_media.py data sql data.csv "SELECT department, AVG(salary) FROM data GROUP BY department"
python3 .agents/skills/media-processor/scripts/process_media.py data sql data.json "SELECT * FROM data WHERE active = 'true'" --json
```

### E. Image Processing (macOS `sips` or Linux `Pillow`)
```bash
# Resize max dimension to 1080px
python3 .agents/skills/media-processor/scripts/process_media.py image input.png --resize 1080 -o output.png

# Convert format (jpeg, png, tiff, heic)
python3 .agents/skills/media-processor/scripts/process_media.py image input.png --format jpeg -o output.jpg
```

### F. Audio & Video (FFmpeg)
```bash
# Extract audio track from video
python3 .agents/skills/media-processor/scripts/process_media.py audio extract video.mp4 audio.mp3

# Trim audio or video
python3 .agents/skills/media-processor/scripts/process_media.py audio trim input.mp3 output.mp3 --start 00:00:10 --end 00:00:45
python3 .agents/skills/media-processor/scripts/process_media.py video clip input.mp4 clip.mp4 --start 00:01:00 --end 00:01:30

# Extract video frame thumbnail
python3 .agents/skills/media-processor/scripts/process_media.py video thumbnail input.mp4 thumb.jpg --time 00:00:05
```

---

## 4. Troubleshooting & Maintenance

* **CPU Running Hot**:
  If a rogue job is running, send an instant unload request to localhost:
  ```bash
  curl -s http://localhost:11434/api/generate -d '{"model": "glm-ocr", "keep_alive": 0}'
  ```
* **Custom Ollama Port**:
  If running on a custom port, set the environment variable:
  ```bash
  export OLLAMA_ENDPOINT="http://localhost:11434"
  ```
