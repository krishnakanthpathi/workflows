#!/usr/bin/env python3
"""
Test suite for Passport Photo Generator (Strict 8, 6, 4 Photo Counts)
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import fitz

from generate_passport_pdf import generate_passport_pdf

TEST_DIR = Path("/tmp/passport_test")
TEST_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_IMAGE = TEST_DIR / "sample_portrait.jpg"


def create_sample_portrait(path: Path):
    img = Image.new("RGB", (1200, 1600), color="#E0E6ED")
    draw = ImageDraw.Draw(img)
    draw.ellipse([200, 1100, 1000, 1900], fill="#2C3E50")
    draw.rectangle([500, 850, 700, 1200], fill="#E5AA70")
    draw.ellipse([400, 450, 800, 1000], fill="#E5AA70")
    draw.ellipse([380, 400, 820, 700], fill="#1A1A1A")
    draw.ellipse([480, 650, 530, 690], fill="#1A1A1A")
    draw.ellipse([670, 650, 720, 690], fill="#1A1A1A")
    draw.arc([520, 780, 680, 850], start=0, end=180, fill="#7A3B18", width=6)
    img.save(path, quality=95)


def verify_pdf(pdf_path: str, expected_w_pt: float, expected_h_pt: float):
    doc = fitz.open(pdf_path)
    assert len(doc) == 1, f"Expected 1 page, got {len(doc)}"
    page = doc[0]
    rect = page.rect
    assert abs(rect.width - expected_w_pt) < 1.5, f"Width mismatch: got {rect.width}, expected {expected_w_pt}"
    assert abs(rect.height - expected_h_pt) < 1.5, f"Height mismatch: got {rect.height}, expected {expected_h_pt}"
    assert os.path.getsize(pdf_path) > 5000, "File size too small"
    print(f"   Verified {Path(pdf_path).name}: {rect.width:.1f} x {rect.height:.1f} pt")


def run_all_tests():
    create_sample_portrait(SAMPLE_IMAGE)

    print("\n--- Test 1: DEFAULT (8 Photos: Top 4, Bottom 4) on 4x6 paper ---")
    out1 = TEST_DIR / "test_default_8photos_4x6.pdf"
    res1 = generate_passport_pdf(SAMPLE_IMAGE, out1, paper_size="4x6", count=8, also_image=True)
    verify_pdf(res1["pdf_path"], 432.0, 288.0)
    assert res1["count"] == 8, f"Expected 8 photos, got {res1['count']}"
    assert "Top 4, Bottom 4" in res1["layout"]
    print(f"✅ Test 1 Passed: {res1['layout']}")

    print("\n--- Test 2: 8 Photos (Top 4, Bottom 4) on 4x4 paper ---")
    out2 = TEST_DIR / "test_8photos_4x4.pdf"
    res2 = generate_passport_pdf(SAMPLE_IMAGE, out2, paper_size="4x4", count=8)
    verify_pdf(res2["pdf_path"], 288.0, 288.0)
    assert res2["count"] == 8, f"Expected 8 photos, got {res2['count']}"
    assert "Top 4, Bottom 4" in res2["layout"]
    print(f"✅ Test 2 Passed: {res2['layout']}")

    print("\n--- Test 3: 6 Photos (Top 3, Bottom 3) on 4x6 paper ---")
    out3 = TEST_DIR / "test_6photos_4x6.pdf"
    res3 = generate_passport_pdf(SAMPLE_IMAGE, out3, paper_size="4x6", count=6)
    verify_pdf(res3["pdf_path"], 432.0, 288.0)
    assert res3["count"] == 6, f"Expected 6 photos, got {res3['count']}"
    assert "Top 3, Bottom 3" in res3["layout"]
    print(f"✅ Test 3 Passed: {res3['layout']}")

    print("\n--- Test 4: 4 Photos (Top 2, Bottom 2) on 4x4 paper ---")
    out4 = TEST_DIR / "test_4photos_4x4.pdf"
    res4 = generate_passport_pdf(SAMPLE_IMAGE, out4, paper_size="4x4", count=4)
    verify_pdf(res4["pdf_path"], 288.0, 288.0)
    assert res4["count"] == 4, f"Expected 4 photos, got {res4['count']}"
    assert "Top 2, Bottom 2" in res4["layout"]
    print(f"✅ Test 4 Passed: {res4['layout']}")

    print("\n--- Test 5: 8 Photos on A4 paper ---")
    out5 = TEST_DIR / "test_8photos_a4.pdf"
    res5 = generate_passport_pdf(SAMPLE_IMAGE, out5, paper_size="a4", count=8)
    verify_pdf(res5["pdf_path"], 841.89, 595.28)
    assert res5["count"] == 8, f"Expected 8 photos, got {res5['count']}"
    assert "Top 4, Bottom 4" in res5["layout"]
    print(f"✅ Test 5 Passed: {res5['layout']}")

    print("\n🎉 ALL 5 TESTS FOR 8, 6, AND 4 PHOTO COUNTS PASSED PERFECTLY!\n")


if __name__ == "__main__":
    run_all_tests()
