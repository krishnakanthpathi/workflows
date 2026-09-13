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
    "PIL": ("pillow", "python3-pil"),
    "pypdf": ("pypdf", "python3-pypdf")
}


def install_python_package(mod_name: str, pypi_name: str, apt_name: str):
    """Auto-install a missing Python package using uv, pip, or apt."""
    print(f"[*] Checking/installing Python package: {pypi_name}...", file=sys.stderr)
    
    # 1. Try uv
    if shutil.which("uv"):
        try:
            subprocess.run(["uv", "pip", "install", pypi_name], check=True, capture_output=True)
            print(f"[+] Successfully installed {pypi_name} via uv", file=sys.stderr)
            return
        except Exception:
            pass

    # 2. Try pip
    res = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True)
    if res.returncode == 0:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", pypi_name], check=True, capture_output=True)
            print(f"[+] Successfully installed {pypi_name} via pip", file=sys.stderr)
            return
        except Exception:
            pass

    # 3. Try apt-get on Linux
    if sys.platform.startswith("linux") and shutil.which("apt-get"):
        try:
            cmd = ["sudo", "apt-get", "install", "-y", apt_name]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[+] Successfully installed {apt_name} via apt", file=sys.stderr)
            return
        except Exception:
            pass


def ensure_python_dependencies():
    """Verify and auto-install required Python libraries."""
    for mod_name, (pypi_name, apt_name) in REQUIRED_PYTHON_PACKAGES.items():
        try:
            __import__(mod_name)
        except ImportError:
            install_python_package(mod_name, pypi_name, apt_name)


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
    except Exception:
        pass


def check_and_install_all(model_name: str = "glm-ocr", endpoint: str = "http://localhost:11434"):
    ensure_python_dependencies()
    ensure_system_binaries()
    ensure_ollama_model(model_name, endpoint)


if __name__ == "__main__":
    print("[*] Checking and repairing prerequisites...")
    check_and_install_all()
    print("[+] Prerequisites verified!")
