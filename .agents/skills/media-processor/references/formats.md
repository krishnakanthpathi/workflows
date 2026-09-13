# Supported Formats & Architecture Capability Matrix

| Category | File Extensions | Primary Handler | Strategy / Capabilities |
| :--- | :--- | :--- | :--- |
| **Structured Data** | `.csv`, `.tsv` | Python `csv` + SQLite stdlib | In-memory SQL querying, filtering, conversion to JSON/JSONL. Zero external deps. |
| **Document Data** | `.json`, `.jsonl` | Python `json` + SQLite stdlib | Nested object inspection, JSONL line streaming, SQL aggregations. |
| **Raster Images** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.heic` | `sips` (macOS) / `Pillow` (Linux) | Auto-orientation, resize, format transcode, contrast enhancement. |
| **Vector Images** | `.svg` | System Browser / Pillow | XML inspection, rasterization. |
| **Video Streams** | `.mp4`, `.mov`, `.mkv`, `.webm` | `ffmpeg` / `ffprobe` | Lossless stream-copy trimming, thumbnail extraction, CRF compression. |
| **Audio Streams** | `.mp3`, `.wav`, `.aac`, `.flac`, `.m4a` | `ffmpeg` | Audio track extraction from video, format transcoding, trimming. |
| **Documents / Scans** | `.pdf`, `.png`, `.jpg` | Ollama `glm-ocr` on `localhost` | Optical normalization, Markdown table extraction, LaTeX math reconstruction. |

---

## Thermal & Loop Circuit Breakers (Localhost Ollama)

When processing unclear media via Ollama on local CPU hardware:
1. **Thread Capping (`num_thread: 4`)**: Allocates at most 4 hyperthreads, keeping remaining cores cool and responsive.
2. **Token Ceiling (`num_predict: 1500`)**: Prevents runaway generation loops that can otherwise generate unbounded tokens.
3. **Repetition Penalty (`repeat_penalty: 1.25`)**: Penalizes token loops (e.g. repeated punctuation or repetitive hallucinated sentences).
4. **Hard Timeout (`timeout: 45s`)**: Enforces socket termination if inference stalls.
5. **Auto-Unload (`keep_alive: 0`)**: Instructs Ollama to drop model weights from memory immediately when finished.
