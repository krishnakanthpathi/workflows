#!/usr/bin/env python3
"""
Automated Verification Suite for Media Processor Skill.
"""

import os
import sys
import json
import csv
import tempfile
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"

def run_cmd(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}\nSTDERR: {res.stderr}", file=sys.stderr)
        raise RuntimeError(f"Command failed: {res.stderr}")
    return res.stdout


def test_data_pipeline():
    print("[*] Testing Data Pipeline...")
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test.csv")
        json_path = os.path.join(tmpdir, "test.json")

        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "role", "score"])
            writer.writerow(["1", "Alice", "Engineer", "95"])
            writer.writerow(["2", "Bob", "Designer", "88"])
            writer.writerow(["3", "Charlie", "Engineer", "92"])

        # 1. Inspect CSV
        out = run_cmd([sys.executable, str(SCRIPTS_DIR / "inspect_media.py"), csv_path])
        meta = json.loads(out)
        assert meta["media_type"] == "data"
        assert meta["row_count"] == 3
        assert "name" in meta["columns"]

        # 2. Convert CSV -> JSON
        run_cmd([sys.executable, str(SCRIPTS_DIR / "process_media.py"), "data", "convert", csv_path, json_path])
        assert os.path.exists(json_path)
        with open(json_path) as f:
            data = json.load(f)
            assert len(data) == 3
            assert data[0]["name"] == "Alice"

        # 3. SQL Query in-memory
        sql_out = run_cmd([
            sys.executable, str(SCRIPTS_DIR / "process_media.py"),
            "data", "sql", csv_path,
            "SELECT role, COUNT(*) as cnt FROM data GROUP BY role ORDER BY cnt DESC",
            "--json"
        ])
        sql_res = json.loads(sql_out)
        assert len(sql_res) == 2
        assert sql_res[0]["role"] == "Engineer"
        assert sql_res[0]["cnt"] == 2

    print("    -> Data Pipeline: PASSED")


def test_image_pipeline():
    print("[*] Testing Image Pipeline...")
    with tempfile.TemporaryDirectory() as tmpdir:
        png_path = os.path.join(tmpdir, "test.png")
        jpg_path = os.path.join(tmpdir, "test.jpg")

        from PIL import Image
        img = Image.new("RGB", (200, 200), color="blue")
        img.save(png_path)

        # 1. Inspect Image
        out = run_cmd([sys.executable, str(SCRIPTS_DIR / "inspect_media.py"), png_path])
        meta = json.loads(out)
        assert meta["media_type"] == "image"
        assert meta["width"] == 200
        assert meta["height"] == 200

        # 2. Resize Image
        run_cmd([sys.executable, str(SCRIPTS_DIR / "process_media.py"), "image", png_path, "--resize", "100"])
        out = run_cmd([sys.executable, str(SCRIPTS_DIR / "inspect_media.py"), png_path])
        meta = json.loads(out)
        assert meta["width"] == 100

        # 3. Convert Image format
        run_cmd([sys.executable, str(SCRIPTS_DIR / "process_media.py"), "image", png_path, "--format", "jpeg", "-o", jpg_path])
        assert os.path.exists(jpg_path)
        out = run_cmd([sys.executable, str(SCRIPTS_DIR / "inspect_media.py"), jpg_path])
        meta = json.loads(out)
        assert meta["format"].lower() in ("jpeg", "jpg")

    print("    -> Image Pipeline: PASSED")


def test_prereq_installer():
    print("[*] Testing Auto-Prerequisite Checker...")
    out = run_cmd([sys.executable, str(SCRIPTS_DIR / "ensure_prereqs.py")])
    assert "Prerequisites verified" in out
    print("    -> Auto-Prerequisite Checker: PASSED")


if __name__ == "__main__":
    test_prereq_installer()
    test_data_pipeline()
    test_image_pipeline()
    print("\n[✓] ALL TESTS PASSED SUCCESSFULLY!")
