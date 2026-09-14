#!/usr/bin/env python3
"""
YouTube Downloader Helper Script
Provides CLI and programmatic access to downloading YouTube videos,
audio extraction, subtitle fetching, and metadata inspection via yt-dlp.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Verify that yt-dlp and ffmpeg are available."""
    has_yt_dlp = False
    try:
        import yt_dlp
        has_yt_dlp = True
    except ImportError:
        has_yt_dlp = shutil.which("yt-dlp") is not None

    has_ffmpeg = shutil.which("ffmpeg") is not None
    return has_yt_dlp, has_ffmpeg


def get_info(url: str):
    """Retrieve video metadata without downloading."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except ImportError:
        cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)


def build_ydl_opts(args, output_template: str):
    """Build yt-dlp options dictionary."""
    ydl_opts = {
        "outtmpl": output_template,
        "quiet": args.quiet,
        "no_warnings": True,
        "noplaylist": not args.playlist,
    }

    if args.audio_only or args.quality == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": args.audio_format,
            "preferredquality": "192",
        }]
    else:
        # Prioritize universally playable H.264 (avc1) video + AAC (mp4a) audio
        if args.quality == "best":
            ydl_opts["format"] = "bv*[vcodec^=avc]+ba[acodec^=mp4a]/bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b"
        elif args.quality == "1080p":
            ydl_opts["format"] = "bv*[height<=1080][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=1080]+ba/b[height<=1080]/best"
        elif args.quality == "720p":
            ydl_opts["format"] = "bv*[height<=720][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=720]+ba/b[height<=720]/best"
        elif args.quality == "480p":
            ydl_opts["format"] = "bv*[height<=480][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=480]+ba/b[height<=480]/best"
        elif args.quality == "4k":
            ydl_opts["format"] = "bv*[height<=2160][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=2160]+ba/b[height<=2160]/best"
        else:
            ydl_opts["format"] = args.quality

        # Ensure container is standard MP4 and re-encode non-standard codecs (AV1/VP9/Opus) if needed
        ydl_opts["merge_output_format"] = "mp4"
        ydl_opts["recodevideo"] = "mp4"

    if args.subtitles:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = [args.sub_lang]

    return ydl_opts


def run_download_cli(args, output_template: str):
    """Fallback to yt-dlp CLI if python library is not installed."""
    cmd = ["yt-dlp", "--no-playlist" if not args.playlist else "--yes-playlist"]
    cmd.extend(["-o", output_template])

    if args.audio_only or args.quality == "audio":
        cmd.extend(["-x", "--audio-format", args.audio_format, "--audio-quality", "192K"])
    else:
        if args.quality == "best":
            cmd.extend(["-f", "bv*[vcodec^=avc]+ba[acodec^=mp4a]/bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b"])
        elif args.quality == "1080p":
            cmd.extend(["-f", "bv*[height<=1080][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=1080]+ba/b[height<=1080]/best"])
        elif args.quality == "720p":
            cmd.extend(["-f", "bv*[height<=720][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=720]+ba/b[height<=720]/best"])
        elif args.quality == "480p":
            cmd.extend(["-f", "bv*[height<=480][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=480]+ba/b[height<=480]/best"])
        elif args.quality == "4k":
            cmd.extend(["-f", "bv*[height<=2160][vcodec^=avc]+ba[acodec^=mp4a]/bv*[height<=2160]+ba/b[height<=2160]/best"])
        else:
            cmd.extend(["-f", args.quality])

        cmd.extend(["--merge-output-format", "mp4", "--recode-video", "mp4"])

    if args.subtitles:
        cmd.extend(["--write-auto-sub", "--sub-lang", args.sub_lang])

    if args.quiet:
        cmd.append("--quiet")

    cmd.append(args.url)
    res = subprocess.run(cmd, check=True)
    return res.returncode


def download_media(args):
    """Main download logic."""
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title)s [%(id)s].%(ext)s")

    has_yt_dlp, has_ffmpeg = check_dependencies()
    if not has_yt_dlp:
        print("Error: yt-dlp is not installed. Please install it with: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)
    if not has_ffmpeg and (args.audio_only or args.quality != "best"):
        print("Warning: ffmpeg was not found. High-resolution streams may not merge properly.", file=sys.stderr)

    downloaded_files = []

    try:
        import yt_dlp

        class PathCollector:
            def __init__(self):
                self.paths = []

            def hook(self, d):
                if d.get("status") == "finished":
                    filename = d.get("filename")
                    if filename and filename not in self.paths:
                        self.paths.append(filename)

        collector = PathCollector()
        ydl_opts = build_ydl_opts(args, output_template)
        ydl_opts["progress_hooks"] = [collector.hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            retcode = ydl.download([args.url])

        downloaded_files = collector.paths

    except ImportError:
        run_download_cli(args, output_template)

    return {
        "status": "success",
        "output_dir": str(output_dir),
        "files": downloaded_files
    }


DEFAULT_DOWNLOADS_DIR = Path(__file__).resolve().parent.parent / "downloads"


def clean_downloads(download_dir: Path):
    """Remove all files inside the downloads directory."""
    if not download_dir.exists():
        print(f"Directory {download_dir} does not exist. Nothing to clean.")
        return 0
    count = 0
    for item in download_dir.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_file() or item.is_symlink():
            item.unlink()
            count += 1
        elif item.is_dir():
            shutil.rmtree(item)
            count += 1
    print(f"✓ Cleaned {count} item(s) from {download_dir}")
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos or extract audio with quality controls and metadata inspection."
    )
    parser.add_argument("url", nargs="?", help="YouTube video URL, shorts URL, or playlist URL")
    parser.add_argument(
        "-q", "--quality",
        choices=["best", "4k", "1080p", "720p", "480p", "audio"],
        default="best",
        help="Target video quality (default: best)"
    )
    parser.add_argument(
        "-a", "--audio-only",
        action="store_true",
        help="Extract audio only (shortcut for -q audio)"
    )
    parser.add_argument(
        "--audio-format",
        choices=["mp3", "m4a", "wav", "opus"],
        default="mp3",
        help="Target audio format when downloading audio (default: mp3)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=str(DEFAULT_DOWNLOADS_DIR),
        help=f"Output directory (default: {DEFAULT_DOWNLOADS_DIR})"
    )
    parser.add_argument(
        "-i", "--info-only",
        action="store_true",
        help="Fetch and display video metadata/available formats without downloading"
    )
    parser.add_argument(
        "-s", "--subtitles",
        action="store_true",
        help="Download video subtitles"
    )
    parser.add_argument(
        "--sub-lang",
        default="en",
        help="Subtitle language code (default: en)"
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Allow downloading the entire playlist if URL contains a playlist ID"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean/delete all downloaded files in the output directory"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress download progress output"
    )

    args = parser.parse_args()

    if args.clean:
        clean_downloads(Path(args.output_dir).expanduser().resolve())
        return

    if not args.url:
        parser.error("the following arguments are required: url (unless --clean is specified)")

    if args.info_only:
        try:
            info = get_info(args.url)
            summary = {
                "title": info.get("title"),
                "id": info.get("id"),
                "duration_seconds": info.get("duration"),
                "uploader": info.get("uploader"),
                "upload_date": info.get("upload_date"),
                "view_count": info.get("view_count"),
                "description_snippet": (info.get("description") or "")[:200],
            }
            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print(f"Title:    {summary['title']}")
                print(f"Uploader: {summary['uploader']}")
                print(f"Duration: {summary['duration_seconds']}s")
                print(f"Views:    {summary['view_count']}")
            return
        except Exception as e:
            print(f"Error fetching info: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        result = download_media(args)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"✓ Download completed to {result['output_dir']}")
    except Exception as e:
        print(f"Error downloading video: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
