#!/usr/bin/env python3
"""
Unified Media Processor CLI.
Dispatches processing across data, images, audio, video, and Ollama-based OCR.
Uses default localhost endpoint with cross-platform fallbacks and auto-prerequisites.
"""

import sys
import os
import csv
import json
import sqlite3
import argparse
import shutil
import subprocess
from pathlib import Path

# Auto-heal prerequisites if available
try:
    from ensure_prereqs import check_and_install_all
    check_and_install_all()
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")


def handle_ocr(args):
    """Delegate to ocr_ollama.py with loop protection."""
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "ocr_ollama.py"),
        args.file,
        "--endpoint", args.endpoint,
        "--model", args.model,
        "--max-tokens", str(args.max_tokens),
        "--threads", str(args.threads),
        "--timeout", str(args.timeout)
    ]
    if args.output:
        cmd.extend(["--output", args.output])
    if args.unload:
        cmd.append("--unload-now")
    
    subprocess.run(cmd, check=True)


def handle_data_convert(args):
    """Convert between CSV, JSON, and JSONL using zero external dependencies."""
    inp = Path(args.input)
    out = Path(args.output)
    in_ext = inp.suffix.lower()
    out_ext = out.suffix.lower()

    records = []
    if in_ext in (".csv", ".tsv"):
        delim = "\t" if in_ext == ".tsv" else ","
        with open(inp, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=delim)
            records = list(reader)
    elif in_ext == ".json":
        with open(inp, "r", encoding="utf-8") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else [data]
    elif in_ext == ".jsonl":
        with open(inp, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]

    if out_ext == ".json":
        with open(out, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    elif out_ext == ".jsonl":
        with open(out, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
    elif out_ext in (".csv", ".tsv"):
        if not records:
            print("No records to write.", file=sys.stderr)
            return
        fieldnames = list(records[0].keys())
        delim = "\t" if out_ext == ".tsv" else ","
        with open(out, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delim)
            writer.writeheader()
            writer.writerows(records)

    print(f"[+] Converted {len(records)} records: {inp} -> {out}")


def handle_data_sql(args):
    """Run SQL queries on CSV/JSON using built-in SQLite in-memory."""
    inp = Path(args.input)
    in_ext = inp.suffix.lower()

    records = []
    if in_ext == ".csv":
        with open(inp, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            records = list(reader)
    elif in_ext == ".json":
        with open(inp, "r", encoding="utf-8") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else [data]

    if not records:
        print("Empty dataset.", file=sys.stderr)
        return

    cols = list(records[0].keys())
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    safe_cols = [f'"{c}" TEXT' for c in cols]
    cur.execute(f"CREATE TABLE data ({', '.join(safe_cols)})")

    placeholders = ", ".join(["?"] * len(cols))
    rows = [[r.get(c, "") for c in cols] for r in records]
    cur.executemany(f"INSERT INTO data VALUES ({placeholders})", rows)
    conn.commit()

    query = args.query.replace("{table}", "data")
    cur.execute(query)
    out_cols = [d[0] for d in cur.description]
    out_rows = cur.fetchall()

    if args.json:
        result = [dict(zip(out_cols, r)) for r in out_rows]
        print(json.dumps(result, indent=2))
    else:
        print(" | ".join(out_cols))
        print("-" * (sum(len(c) for c in out_cols) + len(out_cols) * 3))
        for r in out_rows[:args.limit]:
            print(" | ".join(str(v) for v in r))
        if len(out_rows) > args.limit:
            print(f"... ({len(out_rows) - args.limit} more rows truncated)")


def handle_image(args):
    """Process image using macOS sips or Pillow fallback."""
    inp = args.input
    out = args.output or inp

    has_sips = bool(shutil.which("sips"))

    if has_sips:
        if args.resize:
            cmd = ["sips", "-Z", str(args.resize), inp, "--out", out]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[+] Resized image to max {args.resize}px -> {out}")
        if args.format:
            cmd = ["sips", "-s", "format", args.format, inp, "--out", out]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[+] Converted image format to {args.format} -> {out}")
    else:
        # Cross-platform Pillow fallback (Linux/Docker)
        from PIL import Image
        with Image.open(inp) as img:
            if args.resize:
                w, h = img.size
                max_dim = args.resize
                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                print(f"[+] Resized image to max {args.resize}px -> {out}")
            
            save_format = args.format.upper() if args.format else None
            if save_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(out, format=save_format)
            if args.format:
                print(f"[+] Converted image format to {args.format} -> {out}")


def handle_audio(args):
    """Audio transformations via ffmpeg."""
    if args.action == "extract":
        cmd = ["ffmpeg", "-y", "-i", args.input, "-vn", "-c:a", args.codec or "mp3", args.output]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[+] Extracted audio track -> {args.output}")
    elif args.action == "trim":
        cmd = ["ffmpeg", "-y", "-ss", str(args.start), "-to", str(args.end), "-i", args.input, "-c", "copy", args.output]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[+] Trimmed audio -> {args.output}")


def handle_video(args):
    """Video transformations via ffmpeg."""
    if args.action == "clip":
        cmd = ["ffmpeg", "-y", "-ss", str(args.start), "-to", str(args.end), "-i", args.input, "-c", "copy", args.output]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[+] Extracted video clip -> {args.output}")
    elif args.action == "thumbnail":
        timestamp = args.time or "00:00:01"
        cmd = ["ffmpeg", "-y", "-ss", timestamp, "-i", args.input, "-vframes", "1", args.output]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[+] Extracted frame thumbnail at {timestamp} -> {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Universal Media & Data Processing Hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. OCR
    p_ocr = subparsers.add_parser("ocr", help="Run OCR via local Ollama with thermal circuit breakers")
    p_ocr.add_argument("file", help="Path to image or scan")
    p_ocr.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Ollama endpoint (defaults to localhost)")
    p_ocr.add_argument("--model", default="glm-ocr", help="Vision model name")
    p_ocr.add_argument("--max-tokens", type=int, default=1500, help="Cap max tokens (prevents runaway loop)")
    p_ocr.add_argument("--threads", type=int, default=4, help="CPU threads (prevents full core overheating)")
    p_ocr.add_argument("--timeout", type=int, default=45, help="Hard socket timeout in seconds")
    p_ocr.add_argument("--output", "-o", help="Save markdown output to file")
    p_ocr.add_argument("--unload", action="store_true", help="Immediately unload model after run")
    p_ocr.set_defaults(func=handle_ocr)

    # 2. DATA
    p_data = subparsers.add_parser("data", help="Process tabular data (CSV, JSON, SQL)")
    d_subs = p_data.add_subparsers(dest="data_action", required=True)
    
    d_conv = d_subs.add_parser("convert", help="Convert between CSV, JSON, JSONL")
    d_conv.add_argument("input", help="Source file")
    d_conv.add_argument("output", help="Destination file")
    d_conv.set_defaults(func=handle_data_convert)

    d_sql = d_subs.add_parser("sql", help="Run SQL query on CSV or JSON")
    d_sql.add_argument("input", help="Data file")
    d_sql.add_argument("query", help="SQL query. Use {table} or 'data' for table name")
    d_sql.add_argument("--limit", type=int, default=20, help="Display limit")
    d_sql.add_argument("--json", action="store_true", help="Output JSON instead of table")
    d_sql.set_defaults(func=handle_data_sql)

    # 3. IMAGE
    p_img = subparsers.add_parser("image", help="Process images")
    p_img.add_argument("input", help="Input image file")
    p_img.add_argument("--resize", type=int, help="Max dimension constraint (px)")
    p_img.add_argument("--format", choices=["jpeg", "png", "tiff", "heic"], help="Target format")
    p_img.add_argument("--output", "-o", help="Output file path (defaults to in-place)")
    p_img.set_defaults(func=handle_image)

    # 4. AUDIO
    p_aud = subparsers.add_parser("audio", help="Process audio tracks")
    p_aud.add_argument("action", choices=["extract", "trim"])
    p_aud.add_argument("input", help="Input audio/video file")
    p_aud.add_argument("output", help="Output audio file")
    p_aud.add_argument("--start", help="Start timestamp (e.g. 00:00:10)")
    p_aud.add_argument("--end", help="End timestamp (e.g. 00:00:30)")
    p_aud.add_argument("--codec", help="Audio codec (e.g. mp3, aac, flac)")
    p_aud.set_defaults(func=handle_audio)

    # 5. VIDEO
    p_vid = subparsers.add_parser("video", help="Process video files")
    p_vid.add_argument("action", choices=["clip", "thumbnail"])
    p_vid.add_argument("input", help="Input video file")
    p_vid.add_argument("output", help="Output file")
    p_vid.add_argument("--start", help="Clip start timestamp")
    p_vid.add_argument("--end", help="Clip end timestamp")
    p_vid.add_argument("--time", help="Thumbnail timestamp (default: 00:00:01)")
    p_vid.set_defaults(func=handle_video)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
