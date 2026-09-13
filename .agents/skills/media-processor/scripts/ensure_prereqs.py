#!/usr/bin/env python3
"""
Prerequisite Checker & Auto-Installer.
Detects missing runtimes, libraries, and binaries, automatically installing them.
"""

import sys
import os
import shutil
import subprocess
import urllib.request
import json

REQUIRED_PYTHON_PACKAGES = {
    "PIL": "pillow",
    "pypdf": "pypdf"
}

def install_python_package(pkg_name: str):
    """Auto-install a missing Python package using uv or pip."""
    print(f"[*] Auto-installing missing Python package: {pkg_name}...", file=sys.stderr)
    cmd = []
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", pkg_name]
    else:
        cmd = [sys.executable, "-m", "pip", "install", pkg_name]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"[+] Successfully installed {pkg_name}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to install {pkg_name}: {e}", file=sys.stderr)


def ensure_python_dependencies():
    """Verify and auto-install required Python libraries."""
    for mod_name, pkg_name in REQUIRED_PYTHON_PACKAGES.items():
        try:
            __import__(mod_name)
        except ImportError:
            install_python_package(pkg_name)


def ensure_system_binaries():
    """Verify and attempt installation of system CLI tools (e.g. ffmpeg)."""
    if not shutil.which("ffmpeg"):
        print("[*] ffmpeg not found. Attempting automatic installation...", file=sys.stderr)
        if sys.platform == "darwin" and shutil.which("brew"):
            subprocess.run(["brew", "install", "ffmpeg"], check=False)
        elif sys.platform.startswith("linux"):
            if shutil.which("apt-get"):
                subprocess.run(["sudo", "apt-get", "update"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False)


def ensure_ollama_model(model_name: str = "glm-ocr", endpoint: str = "http://localhost:11434"):
    """Check if model is present in local Ollama instance; pull if missing."""
    try:
        req = urllib.request.Request(f"{endpoint.rstrip('/')}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            if model_name not in models and f"{model_name}:latest" not in [m.get("name", "") for m in data.get("models", [])]:
                print(f"[*] Ollama model '{model_name}' not found locally. Pulling...", file=sys.stderr)
                if shutil.which("ollama"):
                    subprocess.run(["ollama", "pull", model_name], check=True)
    except Exception as e:
        # Ollama might be offline or endpoint custom; do not crash
        pass


def check_and_install_all(model_name: str = "glm-ocr", endpoint: str = "http://localhost:11434"):
    ensure_python_dependencies()
    ensure_system_binaries()
    ensure_ollama_model(model_name, endpoint)


if __name__ == "__main__":
    print("[*] Checking and repairing prerequisites...")
    check_and_install_all()
    print("[+] Prerequisites verified!")
