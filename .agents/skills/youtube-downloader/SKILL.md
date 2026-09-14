---
name: youtube-downloader
description: "Download YouTube videos and audio using yt-dlp. Supports best video+audio merging, target resolutions (1080p, 720p, 480p, 4k), audio extraction (MP3, M4A, WAV), subtitle downloads, and metadata inspection."
version: 1.0.0
author: Krishna Kanth
license: MIT
platforms: [linux, macos, windows]
metadata:
  icon: "📹"
hermes:
  tags: [YouTube, Video, Audio, Downloader, yt-dlp, Media]
  related_skills: [media, youtube-content]
---

# 📹 YouTube Video Downloader

Download YouTube videos, extract audio tracks, fetch subtitles, and inspect video metadata using `yt-dlp` and `ffmpeg`.

## When to Use

Use this skill whenever:
- The user provides a YouTube link (standard video, Short, or playlist) and asks to download or save it.
- The user asks for a specific resolution (e.g. "download this in 1080p", "save 720p version", "get best quality").
- The user wants the audio only (e.g. "extract mp3 from this youtube video", "download the song from this link").
- The user asks to download subtitles or captions for a YouTube video.
- The user wants to check details, available formats, or duration of a YouTube video without downloading.

---

## Prerequisites

- **`yt-dlp`**: Video and audio extractor (`pip install yt-dlp` or `uv pip install yt-dlp`).
- **`ffmpeg`**: Required to merge separate video and audio streams (e.g. 1080p/4K DASH streams) into MP4/MKV and extract MP3s.

```bash
# Verify installation
yt-dlp --version
ffmpeg -version
```

---

## Default Download Location

> [!NOTE]
> All downloads default to the skill's own directory: `<SKILL_DIR>/downloads/`.
> This encapsulates all media files inside the skill folder so they can be easily reviewed, moved, or purged.

---

## Recommended: Helper Script

A bundled helper script is available at `scripts/download_youtube.py`. By default, files are saved directly into `<SKILL_DIR>/downloads/`:

```bash
# 1. Best quality video (H.264/AAC MP4, saved to <SKILL_DIR>/downloads)
python3 <SKILL_DIR>/scripts/download_youtube.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. Specific resolution (1080p, 720p, 480p, 4k)
python3 <SKILL_DIR>/scripts/download_youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" -q 1080p

# 3. Audio extraction (MP3)
python3 <SKILL_DIR>/scripts/download_youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" -a --audio-format mp3

# 4. Metadata inspection without downloading
python3 <SKILL_DIR>/scripts/download_youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" -i --json

# 5. With subtitles
python3 <SKILL_DIR>/scripts/download_youtube.py "https://www.youtube.com/watch?v=VIDEO_ID" -s --sub-lang en

# 6. Custom output directory (if requested by user)
python3 <SKILL_DIR>/scripts/download_youtube.py "URL" -o ~/Downloads
```

---

## Cleanup & Storage Management

To delete all downloaded media and reclaim disk space:

```bash
# Clean via helper script:
python3 <SKILL_DIR>/scripts/download_youtube.py --clean

# Or directly in terminal:
rm -rf <SKILL_DIR>/downloads/*
```

---

## Direct `yt-dlp` CLI Commands

> [!IMPORTANT]
> **Universal Player Compatibility (QuickTime, WhatsApp, Mobile)**:
> YouTube defaults to AV1 or VP9 codecs which fail to open in QuickTime, WhatsApp, and standard media players. Always prioritize H.264 (`avc1`) video and AAC (`mp4a`) audio, combined with `--recode-video mp4` so that any stream will play everywhere.

### 1. Best Quality (Playable Everywhere)
```bash
yt-dlp -f "bv*[vcodec^=avc]+ba[acodec^=mp4a]/bv*+ba/b" --merge-output-format mp4 --recode-video mp4 -o "<SKILL_DIR>/downloads/%(title)s [%(id)s].%(ext)s" "URL"
```

### 2. Specific Resolution (e.g. 1080p or 720p)
```bash
# Max 1080p video + AAC audio merged to playable MP4
yt-dlp -f "bv*[height<=1080][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=1080]+ba/b[height<=1080]/best" --merge-output-format mp4 --recode-video mp4 -o "<SKILL_DIR>/downloads/%(title)s [%(id)s].%(ext)s" "URL"

# Max 720p
yt-dlp -f "bv*[height<=720][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=720]+ba/b[height<=720]/best" --merge-output-format mp4 --recode-video mp4 -o "<SKILL_DIR>/downloads/%(title)s [%(id)s].%(ext)s" "URL"
```

### 3. Audio Only (MP3 / M4A)
```bash
# Extract high quality MP3 (192kbps)
yt-dlp -x --audio-format mp3 --audio-quality 192K -o "<SKILL_DIR>/downloads/%(title)s [%(id)s].%(ext)s" "URL"

# Extract M4A / AAC
yt-dlp -x --audio-format m4a -o "<SKILL_DIR>/downloads/%(title)s [%(id)s].%(ext)s" "URL"
```

### 4. Subtitles Only or Subtitles Embedded
```bash
# Download automatic / manual English subtitles
yt-dlp --write-auto-sub --sub-lang en --skip-download -o "<SKILL_DIR>/downloads/%(title)s [%(id)s]" "URL"

# Embed subtitles into video
yt-dlp -f "bv*[vcodec^=avc]+ba[acodec^=mp4a]/bv*+ba/b" --merge-output-format mp4 --recode-video mp4 --write-auto-sub --embed-subs -o "<SKILL_DIR>/downloads/%(title)s [%(id)s].%(ext)s" "URL"
```

### 5. Inspect Formats
```bash
yt-dlp -F "URL"
```

---

## Workflow Protocol for Agents

1. **Parse Request**: Identify the target URL, whether video or audio is desired, and preferred resolution.
2. **Default Destination**: Store downloads in `<SKILL_DIR>/downloads/` unless the user explicitly asks for a different folder.
3. **Execute**: Run the helper script or `yt-dlp` with `--no-playlist` (to prevent accidental downloads of 100+ videos if URL has `&list=...` unless explicitly requested).
4. **Report Result**: Provide the path to the downloaded file (`<SKILL_DIR>/downloads/...`), file size, and duration/resolution.
5. **Clean on Demand**: When the user requests cleanup, run `python3 <SKILL_DIR>/scripts/download_youtube.py --clean`.

---

## Troubleshooting & Tips

- **Single Video in Playlist URL**: `yt-dlp` automatically defaults to downloading single videos when `--no-playlist` is passed.
- **Bot Detection / Age Gate**: If YouTube challenges the request, use `--cookies-from-browser chrome` (or firefox/safari) or update `yt-dlp` with `pip install -U yt-dlp`.
- **403 Forbidden / Throttling**: Run `yt-dlp -U` to ensure the latest extraction patterns are present.
