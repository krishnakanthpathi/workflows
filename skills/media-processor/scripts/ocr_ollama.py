#!/usr/bin/env python3
"""
Ollama OCR Runner with Thermal & Infinite-Loop Circuit Breakers.
Uses default localhost endpoint with automatic prerequisite repair.
"""

import sys
import os
import json
import base64
import argparse
import urllib.request
import urllib.error
import time
from pathlib import Path

# Auto-heal prerequisites
try:
    from ensure_prereqs import check_and_install_all
    check_and_install_all()
except ImportError:
    pass

DEFAULT_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_OCR_MODEL", "glm-ocr")

# Thermal & safety constraints
DEFAULT_MAX_TOKENS = 1500
DEFAULT_THREADS = 4      # Prevent pinning 100% of all CPU cores
DEFAULT_TIMEOUT = 45     # Seconds before hard kill
DEFAULT_REPEAT_PENALTY = 1.25


def preprocess_image(image_path: str, max_dimension: int = 1600) -> bytes:
    """
    Optically normalize image:
    - Resize down if enormous (prevents memory explosion)
    - Enhance contrast if Pillow is available
    - Returns raw bytes
    """
    try:
        from PIL import Image, ImageEnhance
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            w, h = img.size
            if max(w, h) > max_dimension:
                ratio = max_dimension / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
            
            # Moderate contrast boost for unclear / faint text
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)

            import io
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            return buffer.getvalue()
    except Exception:
        with open(image_path, "rb") as f:
            return f.read()


def unload_model(endpoint: str, model: str):
    """Tell Ollama to immediately unload model to free RAM and cool down CPU."""
    try:
        req = urllib.request.Request(
            f"{endpoint.rstrip('/')}/api/generate",
            data=json.dumps({"model": model, "keep_alive": 0}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass


def run_ocr(
    image_path: str,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
    prompt: str = "Extract all text, tables, and formulas from this document as clean markdown.",
    max_tokens: int = DEFAULT_MAX_TOKENS,
    threads: int = DEFAULT_THREADS,
    timeout: int = DEFAULT_TIMEOUT,
    stream: bool = True
) -> str:
    """
    Execute OCR against Ollama with strict loop detection and thermal limits.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    raw_bytes = preprocess_image(image_path)
    b64_img = base64.b64encode(raw_bytes).decode("utf-8")

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [b64_img],
        "stream": stream,
        "options": {
            "num_predict": max_tokens,       # Hard token ceiling (prevents infinite runaway)
            "num_thread": threads,           # Capped CPU thread count (prevents thermal throttle)
            "repeat_penalty": DEFAULT_REPEAT_PENALTY,  # Breaks repetition attractors
            "temperature": 0.1,
            "stop": ["```\n```", "\n```\n", "<|endoftext|>", "<|user|>", "<|observation|>"]
        },
        "keep_alive": "30s"
    }

    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    result_chunks = []
    recent_tokens = []
    consecutive_repeats = 0

    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if not stream:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("response", "")

            for line in response:
                if time.time() - start_time > timeout:
                    print(f"\n[CIRCUIT BREAKER] Hard timeout ({timeout}s) exceeded. Aborting to protect CPU.", file=sys.stderr)
                    unload_model(endpoint, model)
                    break

                if not line:
                    continue

                chunk = json.loads(line.decode("utf-8"))
                text = chunk.get("response", "")
                result_chunks.append(text)

                # Loop detection watchdog: detect repeated token patterns
                words = text.strip().split()
                for w in words:
                    recent_tokens.append(w)
                    if len(recent_tokens) > 12:
                        recent_tokens.pop(0)
                    
                    if len(recent_tokens) == 12:
                        w_slice = recent_tokens[-3:]
                        if (recent_tokens[0:3] == w_slice and 
                            recent_tokens[3:6] == w_slice and 
                            recent_tokens[6:9] == w_slice):
                            consecutive_repeats += 1
                            if consecutive_repeats >= 2:
                                print("\n[CIRCUIT BREAKER] Infinite text loop detected! Terminating generation immediately.", file=sys.stderr)
                                unload_model(endpoint, model)
                                return "".join(result_chunks)

                if chunk.get("done", False):
                    break

    except (urllib.error.URLError, TimeoutError) as e:
        print(f"\n[ERROR] Connection or timeout error querying {endpoint}: {e}", file=sys.stderr)
        unload_model(endpoint, model)
        raise

    return "".join(result_chunks)


def main():
    parser = argparse.ArgumentParser(description="Ollama OCR runner with thermal & loop protection.")
    parser.add_argument("image", help="Path to document/image file")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Ollama API base URL (defaults to localhost)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (e.g. glm-ocr, minicpm-v)")
    parser.add_argument("--prompt", default="Extract all text, tables, and formulas from this document as clean markdown.", help="OCR prompt")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Maximum tokens to generate")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS, help="CPU threads to assign")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Hard timeout in seconds")
    parser.add_argument("--output", "-o", help="Optional output markdown file path")
    parser.add_argument("--unload-now", action="store_true", help="Immediately unload model from memory after run")

    args = parser.parse_args()

    print(f"[*] Dispatching to Ollama ({args.model}) @ {args.endpoint}...", file=sys.stderr)
    print(f"[*] Circuit Breakers: threads={args.threads}, max_tokens={args.max_tokens}, timeout={args.timeout}s", file=sys.stderr)

    try:
        output_text = run_ocr(
            image_path=args.image,
            endpoint=args.endpoint,
            model=args.model,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            threads=args.threads,
            timeout=args.timeout
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"[+] Output saved to {args.output}", file=sys.stderr)
        else:
            print(output_text)

        if args.unload_now:
            unload_model(args.endpoint, args.model)
            print(f"[+] Model {args.model} unloaded from memory.", file=sys.stderr)

    except Exception as err:
        print(f"[!] OCR execution failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
