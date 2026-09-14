# Media Processor Quick Recipes

High-velocity cheat sheet of direct one-liners for Antigravity agents.

---

## 1. Local Ollama OCR (with Thermal & Loop Protection)

Default endpoint: `http://localhost:11434`

### Python Runner (Recommended - includes loop watchdog)
```bash
python3 .agents/skills/media-processor/scripts/ocr_ollama.py /path/to/scan.jpg --threads 4 --max-tokens 1500 --timeout 45
```

### Direct cURL One-Liner (Fast inspection)
```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "glm-ocr",
  "prompt": "Extract all text, tables, and formulas from this document as clean markdown.",
  "images": ["'$(base64 -i /path/to/image.png | tr -d '\n')'"],
  "stream": false,
  "options": {
    "num_thread": 4,
    "num_predict": 1500,
    "repeat_penalty": 1.25,
    "temperature": 0.1
  },
  "keep_alive": "30s"
}' | jq -r .response
```

### Emergency Unload (Cool down CPU immediately)
```bash
curl -s http://localhost:11434/api/generate -d '{"model": "glm-ocr", "keep_alive": 0}'
```

---

## 2. Auto-Prerequisite Verification & Repair

Run once to check and auto-install any missing dependencies:
```bash
python3 .agents/skills/media-processor/scripts/ensure_prereqs.py
```

---

## 3. Tabular Data (CSV / JSON / SQL)

### Query CSV/JSON with SQL (in-memory SQLite)
```bash
# Query CSV directly
python3 .agents/skills/media-processor/scripts/process_media.py data sql data.csv "SELECT name, SUM(amount) FROM data GROUP BY name ORDER BY 2 DESC"

# Output as JSON
python3 .agents/skills/media-processor/scripts/process_media.py data sql data.csv "SELECT * FROM data LIMIT 10" --json
```

### Format Conversions
```bash
# CSV -> JSON
python3 .agents/skills/media-processor/scripts/process_media.py data convert input.csv output.json

# JSON -> CSV
python3 .agents/skills/media-processor/scripts/process_media.py data convert input.json output.csv

# JSON -> JSONL
python3 .agents/skills/media-processor/scripts/process_media.py data convert input.json output.jsonl
```

---

## 4. Images (Native macOS `sips` or Pillow Fallback)

```bash
# Resize to max 1200px (preserves aspect ratio)
python3 .agents/skills/media-processor/scripts/process_media.py image input.png --resize 1200 -o image_resized.png

# Convert PNG to JPEG
python3 .agents/skills/media-processor/scripts/process_media.py image input.png --format jpeg -o image.jpg
```

---

## 5. Audio & Video (FFmpeg)

```bash
# Extract audio from video
ffmpeg -y -i input.mp4 -vn -c:a mp3 output.mp3

# Grab video frame thumbnail at 5 seconds
ffmpeg -y -ss 00:00:05 -i input.mp4 -vframes 1 thumbnail.jpg

# Trim video without re-encoding (lossless & instant)
ffmpeg -y -ss 00:01:00 -to 00:02:30 -i input.mp4 -c copy clip.mp4

# Compress video (H.264 CRF 28)
ffmpeg -y -i input.mp4 -vcodec libx264 -crf 28 -preset fast -c:a aac -b:a 128k compressed.mp4
```
