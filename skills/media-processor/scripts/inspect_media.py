#!/usr/bin/env python3
"""
Universal Media Inspector.
Probes and extracts normalized metadata across structured data, images, video, audio, and documents.
"""

import sys
import os
import json
import csv
import subprocess
from pathlib import Path

def inspect_data(path: str) -> dict:
    """Inspect tabular/structured data (CSV, TSV, JSON, JSONL)."""
    p = Path(path)
    suffix = p.suffix.lower()
    
    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, [])
            rows = 0
            sample_rows = []
            for row in reader:
                rows += 1
                if rows <= 3:
                    sample_rows.append(row)
            return {
                "media_type": "data",
                "subtype": "csv" if suffix == ".csv" else "tsv",
                "columns": header,
                "column_count": len(header),
                "row_count": rows,
                "samples": sample_rows
            }

    elif suffix in (".json", ".jsonl"):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if suffix == ".jsonl":
                lines = 0
                sample = None
                for line in f:
                    if line.strip():
                        lines += 1
                        if sample is None:
                            try:
                                sample = json.loads(line)
                            except Exception:
                                pass
                return {
                    "media_type": "data",
                    "subtype": "jsonl",
                    "line_count": lines,
                    "sample_keys": list(sample.keys()) if isinstance(sample, dict) else []
                }
            else:
                data = json.load(f)
                if isinstance(data, list):
                    sample_keys = list(data[0].keys()) if data and isinstance(data[0], dict) else []
                    return {
                        "media_type": "data",
                        "subtype": "json_array",
                        "item_count": len(data),
                        "sample_keys": sample_keys
                    }
                elif isinstance(data, dict):
                    return {
                        "media_type": "data",
                        "subtype": "json_object",
                        "root_keys": list(data.keys())
                    }
    return {"media_type": "data", "subtype": "unknown"}


def inspect_image(path: str) -> dict:
    """Inspect image using Pillow or macOS sips."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return {
                "media_type": "image",
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "is_animated": getattr(img, "is_animated", False)
            }
    except Exception:
        # Fallback to macOS sips
        try:
            res = subprocess.run(["sips", "-g", "all", path], capture_output=True, text=True)
            info = {}
            for line in res.stdout.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip()
            return {
                "media_type": "image",
                "format": info.get("format"),
                "width": int(info.get("pixelWidth", 0)),
                "height": int(info.get("pixelHeight", 0)),
                "mode": info.get("space")
            }
        except Exception as e:
            return {"media_type": "image", "error": str(e)}


def inspect_av(path: str) -> dict:
    """Inspect audio/video using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            format_info = data.get("format", {})
            streams = data.get("streams", [])
            
            video_streams = [s for s in streams if s.get("codec_type") == "video"]
            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
            
            media_type = "video" if video_streams else ("audio" if audio_streams else "media")
            
            details = {
                "media_type": media_type,
                "duration_seconds": float(format_info.get("duration", 0)),
                "bitrate_kbps": int(format_info.get("bit_rate", 0)) // 1000 if format_info.get("bit_rate") else None,
                "format_name": format_info.get("format_name")
            }
            if video_streams:
                v = video_streams[0]
                details["video"] = {
                    "codec": v.get("codec_name"),
                    "width": v.get("width"),
                    "height": v.get("height"),
                    "fps": eval(v.get("r_frame_rate", "0/1")) if "/" in v.get("r_frame_rate", "") else None
                }
            if audio_streams:
                a = audio_streams[0]
                details["audio"] = {
                    "codec": a.get("codec_name"),
                    "sample_rate_hz": a.get("sample_rate"),
                    "channels": a.get("channels")
                }
            return details
    except Exception as e:
        return {"media_type": "av", "error": str(e)}
    return {"media_type": "av", "error": "ffprobe not available"}


def inspect_document(path: str) -> dict:
    """Inspect PDF documents."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        return {
            "media_type": "document",
            "subtype": "pdf",
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": {k: str(v) for k, v in (reader.metadata or {}).items()}
        }
    except Exception as e:
        return {"media_type": "document", "subtype": "pdf", "error": str(e)}


def inspect_file(path: str) -> dict:
    if not os.path.exists(path):
        return {"error": f"File does not exist: {path}"}

    stat = os.stat(path)
    base_info = {
        "path": os.path.abspath(path),
        "filename": os.path.basename(path),
        "size_bytes": stat.st_size,
        "size_human": f"{stat.st_size / (1024 * 1024):.2f} MB" if stat.st_size >= 1024*1024 else f"{stat.st_size / 1024:.2f} KB"
    }

    ext = Path(path).suffix.lower()
    if ext in (".csv", ".tsv", ".json", ".jsonl"):
        probe = inspect_data(path)
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff", ".bmp", ".heic"):
        probe = inspect_image(path)
    elif ext in (".mp4", ".mov", ".mkv", ".webm", ".avi", ".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"):
        probe = inspect_av(path)
    elif ext in (".pdf",):
        probe = inspect_document(path)
    else:
        probe = {"media_type": "generic", "extension": ext}

    return {**base_info, **probe}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_media.py <file_path>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = inspect_file(file_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
