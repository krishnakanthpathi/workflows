#!/usr/bin/env python3
"""
Question Paper Generator - Compiler Engine
Converts structured exam JSON into authentic, print-ready HTML and compiles to PDF via Headless Chrome.

Usage:
    python3 render_paper.py <path_to_paper.json> [--open] [--out-dir <dir>]
    python3 render_paper.py --all [--open]
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "templates")
EXAMPLES_DIR = os.path.join(SKILL_ROOT, "examples")

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser"
]

def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def convert_md_table_to_html(md_table_str):
    """Converts a multi-line markdown table string into a styled HTML table."""
    lines = [l.strip() for l in md_table_str.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return md_table_str
    
    headers = [c.strip() for c in lines[0].strip('|').split('|')]
    sep_idx = -1
    for idx, l in enumerate(lines):
        if re.match(r'^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$', l):
            sep_idx = idx
            break
            
    if sep_idx == -1:
        return md_table_str
        
    rows = []
    for l in lines[sep_idx + 1:]:
        if '|' in l:
            cells = [c.strip() for c in l.strip('|').split('|')]
            rows.append(cells)
            
    html = ['<table class="data-table">', '  <thead><tr>']
    for h in headers:
        html.append(f'    <th>{h}</th>')
    html.append('  </tr></thead>')
    html.append('  <tbody>')
    for r in rows:
        html.append('    <tr>')
        for c in r:
            html.append(f'      <td>{c}</td>')
        html.append('    </tr>')
    html.append('  </tbody>')
    html.append('</table>')
    return '\n'.join(html)

def process_markdown_tables_in_text(text):
    """
    Scans a text string for markdown table blocks and replaces them
    with semantic <table class="data-table"> HTML markup.
    """
    if not isinstance(text, str) or '|' not in text:
        return text
        
    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect if current line and next line form a markdown table header + separator
        if i + 1 < len(lines) and '|' in line and re.match(r'^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$', lines[i+1]):
            table_lines = [line, lines[i+1]]
            j = i + 2
            while j < len(lines) and '|' in lines[j] and lines[j].strip().startswith('|'):
                table_lines.append(lines[j])
                j += 1
            result.append(convert_md_table_to_html('\n'.join(table_lines)))
            i = j
        else:
            result.append(line)
            i += 1
    return '\n'.join(result)

def preprocess_exam_data(data):
    """Recursively processes exam data to convert markdown tables to HTML tables."""
    if isinstance(data, dict):
        return {k: preprocess_exam_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [preprocess_exam_data(x) for x in data]
    elif isinstance(data, str):
        return process_markdown_tables_in_text(data)
    return data

def detect_template(data):
    """Detect whether to use the Language/Hindi template or Universal STEM/General template."""
    if "metadata" in data and ("subject_hindi" in data["metadata"] or "blueprint_table" in data):
        return "language_template.html"
    return "universal_template.html"

def render_json(json_path, out_dir=None):
    if not os.path.exists(json_path):
        print(f"[!] Error: JSON file not found: {json_path}")
        return None, None

    stem = os.path.splitext(os.path.basename(json_path))[0]
    target_dir = out_dir if out_dir else os.path.dirname(os.path.abspath(json_path))
    os.makedirs(target_dir, exist_ok=True)

    output_html = os.path.join(target_dir, f"{stem}.html")
    output_pdf = os.path.join(target_dir, f"{stem}.pdf")

    print(f"[*] Reading JSON data from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Preprocess data to convert any embedded markdown tables to HTML
    data = preprocess_exam_data(data)

    template_name = detect_template(data)
    
    # Search for template in multiple locations
    search_dirs = [TEMPLATES_DIR, os.path.dirname(json_path), SCRIPT_DIR, os.getcwd()]
    env = Environment(
        loader=FileSystemLoader(search_dirs),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )

    try:
        template = env.get_template(template_name)
    except Exception:
        # Fallback if language_template is named template.html
        if template_name == "language_template.html":
            try:
                template = env.get_template("template.html")
            except Exception as e:
                print(f"[!] Failed to load template: {e}")
                return None, None
        else:
            raise

    print(f"[*] Mapping JSON into template: {template_name}...")
    rendered_html = template.render(**data)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"[+] HTML generated: {output_html}")
    return output_html, output_pdf

def compile_pdf(html_path, pdf_path):
    chrome = find_chrome()
    if not chrome:
        print("[!] Error: No compatible Chrome/Chromium binary found for PDF generation.")
        return False

    print(f"[*] Compiling to PDF via Chrome ({os.path.basename(chrome)})...")
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file://{os.path.abspath(html_path)}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"[+] PDF successfully created: {pdf_path} ({size_kb:.1f} KB)")
        try:
            pinfo = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True)
            if pinfo.returncode == 0:
                for line in pinfo.stdout.splitlines():
                    if "Pages:" in line or "Page size:" in line:
                        print(f"    {line}")
        except Exception:
            pass
        return True
    else:
        print(f"[-] PDF compilation failed: {res.stderr}")
        return False

def open_pdf(pdf_path):
    if sys.platform == "darwin":
        subprocess.run(["open", pdf_path])
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", pdf_path])
    elif sys.platform == "win32":
        os.startfile(pdf_path)
    print(f"[+] Opened PDF: {pdf_path}")

def main():
    parser = argparse.ArgumentParser(description="Exam Question Paper Generator (JSON -> PDF)")
    parser.add_argument("json_file", nargs="?", help="Path to input question paper JSON")
    parser.add_argument("-o", "--open", action="store_true", help="Automatically open generated PDF")
    parser.add_argument("-d", "--out-dir", help="Directory where HTML and PDF outputs should be saved")
    parser.add_argument("-a", "--all", action="store_true", help="Compile all example question papers")
    args = parser.parse_args()

    if args.all:
        json_files = sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.json")))
        if not json_files:
            print(f"[!] No JSON files found in {EXAMPLES_DIR}")
            sys.exit(1)
        print(f"[*] Batch processing {len(json_files)} question papers from examples/...")
        for jf in json_files:
            html, pdf = render_json(jf, out_dir=args.out_dir)
            if html and pdf and compile_pdf(html, pdf):
                if args.open:
                    open_pdf(pdf)
            print("-" * 50)
        return

    if not args.json_file:
        parser.print_help()
        print("\nExample:")
        print("  python3 render_paper.py ../examples/physics_class10_model_paper.json --open")
        sys.exit(1)

    html, pdf = render_json(args.json_file, out_dir=args.out_dir)
    if html and pdf:
        if compile_pdf(html, pdf):
            if args.open:
                open_pdf(pdf)
            print(f"\n[✔] Success! Artifacts ready:\n    PDF:  {pdf}\n    HTML: {html}")

if __name__ == "__main__":
    main()
