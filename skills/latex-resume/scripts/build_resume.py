#!/usr/bin/env python3
"""
Resume Builder CLI using Tectonic and Poppler
Compiles ATS-optimized LaTeX resumes into PDF, renders PNG previews, and handles previewing.
"""

import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_RESUME_TEX = "/Users/krishnakanth/.gemini/antigravity/scratch/latex-resume/resume.tex"

def check_dependencies():
    tectonic = shutil.which("tectonic")
    pdftoppm = shutil.which("pdftoppm")
    if not tectonic:
        print("Error: 'tectonic' is not installed or not in PATH.", file=sys.stderr)
        print("Install via Homebrew: brew install tectonic", file=sys.stderr)
        sys.exit(1)
    return tectonic, pdftoppm

def build_resume(tex_path, render=True, preview=False):
    if not os.path.isfile(tex_path):
        print(f"Error: LaTeX file not found at: {tex_path}", file=sys.stderr)
        sys.exit(1)

    work_dir = os.path.dirname(os.path.abspath(tex_path))
    base_name = os.path.splitext(os.path.basename(tex_path))[0]
    pdf_path = os.path.join(work_dir, f"{base_name}.pdf")

    tectonic_bin, pdftoppm_bin = check_dependencies()

    print(f"==> Compiling LaTeX: {tex_path}")
    result = subprocess.run(
        [tectonic_bin, os.path.basename(tex_path)],
        cwd=work_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Error compiling LaTeX with tectonic:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print(f"==> Successfully generated: {pdf_path}")

    # Render PNG preview if pdftoppm is available
    if render and pdftoppm_bin:
        preview_prefix = os.path.join(work_dir, f"{base_name}_preview")
        print(f"==> Rendering PNG preview: {preview_prefix}-1.png")
        subprocess.run(
            [pdftoppm_bin, "-png", "-r", "150", pdf_path, preview_prefix],
            cwd=work_dir,
            check=False
        )

    # Open preview if requested
    if preview:
        print(f"==> Opening preview...")
        subprocess.run(["open", pdf_path], check=False)

    # Print MEDIA protocol line for agent / chat bridge consumption
    print(f"\nMEDIA:{pdf_path}")

def main():
    parser = argparse.ArgumentParser(description="Compile and preview LaTeX resume with Tectonic.")
    parser.add_argument(
        "--tex",
        default=DEFAULT_RESUME_TEX,
        help=f"Path to resume.tex (default: {DEFAULT_RESUME_TEX})"
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Skip generating PNG preview"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open PDF in default viewer after compilation"
    )

    args = parser.parse_args()
    build_resume(args.tex, render=not args.no_render, preview=args.preview)

if __name__ == "__main__":
    main()
