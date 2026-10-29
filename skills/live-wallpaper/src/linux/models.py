import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".flv", ".m4v"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"}
ALL_MEDIA_EXTENSIONS = SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS

class MediaType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    STREAM = "stream"

class MediaItem:
    def __init__(self, path: str):
        self.path = path
        self.type = self._detect_type()

    def _detect_type(self) -> MediaType:
        if self.path.startswith(("http://", "https://", "rtmp://", "rtsp://")):
            return MediaType.STREAM
        ext = os.path.splitext(self.path)[1].lower()
        if ext in SUPPORTED_IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        return MediaType.VIDEO

    def to_dict(self):
        return {
            "path": self.path,
            "type": self.type.value,
            "name": os.path.basename(self.path)
        }

def resolve_media_sources(sources: List[str]) -> List[str]:
    """Expands directories, wildcards, and handles paths or URLs."""
    resolved = []
    for src in sources:
        if src.startswith(("http://", "https://", "rtmp://", "rtsp://")):
            resolved.append(src)
            continue

        expanded = os.path.abspath(os.path.expanduser(src))
        if os.path.isdir(expanded):
            dir_files = []
            for root, _, files in os.walk(expanded):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ALL_MEDIA_EXTENSIONS:
                        dir_files.append(os.path.join(root, f))
            dir_files.sort()
            resolved.extend(dir_files)
        elif os.path.isfile(expanded):
            ext = os.path.splitext(expanded)[1].lower()
            if ext in ALL_MEDIA_EXTENSIONS:
                resolved.append(expanded)
    return resolved
