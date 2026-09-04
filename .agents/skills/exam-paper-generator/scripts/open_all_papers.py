#!/usr/bin/env python3
"""
Batch Compiler & PDF Launcher
Compiles all sample examination papers (Physics, Mathematics, Biology, Hindi) and opens them on macOS.

Usage:
    python3 open_all_papers.py
"""

import os
import glob
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RENDER_SCRIPT = os.path.join(SCRIPT_DIR, "render_paper.py")
EXAMPLES_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "examples"))

def main():
    json_files = sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.json")))
    if not json_files:
        print(f"[!] No JSON files found in {EXAMPLES_DIR}")
        return

    print(f"==================================================")
    print(f"🎓 Compiling and Opening {len(json_files)} Examination Papers")
    print(f"==================================================")

    generated_pdfs = []
    for jf in json_files:
        name = os.path.basename(jf)
        print(f"\n▶ Processing: {name}")
        cmd = ["python3", RENDER_SCRIPT, jf]
        res = subprocess.run(cmd)
        if res.returncode == 0:
            pdf_path = os.path.splitext(jf)[0] + ".pdf"
            if os.path.exists(pdf_path):
                generated_pdfs.append(pdf_path)

    print("\n" + "=" * 50)
    print(f"🚀 Opening {len(generated_pdfs)} PDFs in macOS Preview...")
    print("=" * 50)
    for pdf in generated_pdfs:
        print(f"  📂 Opening: {os.path.basename(pdf)}")
        subprocess.run(["open", pdf])
        time.sleep(0.5)

    print("\n[✔] All papers compiled and opened successfully!")

if __name__ == "__main__":
    main()
