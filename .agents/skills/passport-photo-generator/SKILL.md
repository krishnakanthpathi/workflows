---
name: passport-photo-generator
description: "CRITICAL MUST-USE: Use whenever the user asks to generate, format, tile, or prepare passport photos, visa photos, or stamp-size photos onto printable paper sheets (4x4 inch, 4x6 inch, A4, Letter). When given an image, NEVER provide manual editing steps; you MUST run generate_passport_pdf.py via terminal and return the compiled PDF with MEDIA:<path_to_pdf>."
version: 1.1.0
author: Krishna Kanth
license: MIT
metadata:
  icon: "📸"
hermes:
  tags: [passport, photo-generator, pdf-generation, printing, photography, tiling, media]
  related_skills: [python, pdf-generation]
---

# 📸 Passport Photo Sheet Generator

> [!CRITICAL]
> **STRICT EXECUTION PROTOCOL — AUTOMATED DISPATCH & PHOTO COUNTS**:
> When the user asks to create, tile, format, or generate passport photos from an image:
> 1. **DO NOT** give manual Photoshop / editing instructions in chat.
> 2. **PHOTO COUNT RULES**:
>    - Standard allowed counts: **8 photos**, **6 photos**, or **4 photos**.
>    - **DEFAULT**: If the user does not specify a count (or says "one", "a passport sheet", or gives an image without a number), **ALWAYS USE 8 PHOTOS: TOP 4, BOTTOM 4** (`--count 8`).
>    - If user specifies 6 photos: 3 on top, 3 on bottom (`--count 6`).
>    - If user specifies 4 photos: 2 on top, 2 on bottom (`--count 4`).
> 3. **RUN THE CLI IMMEDIATELY**:
>    ```bash
>    python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py <input_image_path> --count 8 --paper 4x6 [options]
>    ```
> 4. **RETURN MEDIA DISPATCH**:
>    The CLI compiles a print-ready PDF and prints:
>    `MEDIA:<absolute_path_to_pdf>`
>    In your reply, provide a 1-sentence confirmation and print the exact `MEDIA:<path>` line along with a clickable Markdown file link `[passport_photos.pdf](file://<path>)`.
>    The platform gateway (WhatsApp bridge / Discord / Web) will automatically deliver the PDF file directly to the user!

---

## 📌 Grid Layouts by Count

| Count | Grid Layout | Description | Best Paper |
| :---: | :---: | :--- | :--- |
| **8** *(Default)* | **4 cols × 2 rows** | **Top 4, Bottom 4** | `4x6` (100% full size), `a4`, `4x4` (scaled) |
| **6** | **3 cols × 2 rows** | **Top 3, Bottom 3** | `4x6`, `a4` |
| **4** | **2 cols × 2 rows** | **Top 2, Bottom 2** | `4x4` (100% full size), `4x6`, `a4` |

---

## 📌 Features & Capabilities

- **Paper Sizes**:
  - `4x6`: Standard 4R photo paper (ideal default for 8 photos: Top 4, Bottom 4).
  - `4x4`: 4 × 4 inch square sheet (ideal for 4 photos, or 8 scaled stamp/mini photos).
  - `a4`: Standard international document size (210 x 297 mm) for home/office printing.
  - `letter`: 8.5 x 11 inch US paper.
  - `5x7`: 5R photo paper (127 x 178 mm).
  - Custom dimension support: `--paper 100x150mm`, `--paper 5x5in`.
- **Photo Standards**:
  - `indian` / `uk` / `eu` / `schengen`: 35mm × 45mm (Standard international biometric).
  - `us` / `usa` / `2x2`: 2.0 × 2.0 inch (50.8mm × 50.8mm).
  - `ca` / `canada`: 50mm × 70mm.
  - `china`: 33mm × 48mm.
  - `pan`: 25mm × 35mm (Indian PAN card format).
  - Custom size support: `--photo-size 35x45mm`, `--photo-size 2x2in`.
- **Smart Aspect Framing**:
  - `face_upper` (default): Focuses on the upper 35% of the portrait so the person's head, chin, and hair are naturally framed without awkward cuts.
  - `center`: Exact geometric center crop.
  - `fit`: Letterboxed with clean white padding.
- **Precision Cutting Guides**:
  - `solid` (default): Clean, ultra-thin light gray cut-lines for scissors/cutter.
  - `dashed`: Dashed cut borders.
  - `corners`: Professional photo studio corner tick marks.
  - `none`: Borderless edge-to-edge prints.
- **Output & Print Quality**:
  - Vector PDF compiled at crisp **300 DPI** print resolution via ReportLab.
  - Optional companion JPEG (`--also-image`) for digital photo kiosk machines.
  - Instant preview on macOS with `--open`.

---

## 🚀 Quick CLI Reference

```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py <input_image> [flags]
```

### Common Commands

#### 1. Default: 8 Photos (Top 4, Bottom 4) on Standard 4x6 Photo Paper
```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py \
  photo.jpg --open
```

#### 2. 8 Photos on 4x4 Paper
```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py \
  photo.jpg --paper 4x4 --count 8 --open
```

#### 3. 4 Photos (Top 2, Bottom 2) on 4x4 Paper
```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py \
  photo.jpg --paper 4x4 --count 4 --open
```

#### 4. 6 Photos (Top 3, Bottom 3) on 4x6 Paper
```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py \
  photo.jpg --paper 4x6 --count 6 --open
```

#### 5. 8 Photos on A4 Sheet
```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/generate_passport_pdf.py \
  photo.jpg --paper a4 --count 8 --open
```

---

## 🛠️ CLI Arguments Reference

| Argument | Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| `image` | Positional | *Required* | Path to input portrait photo (JPG, PNG, WEBP, HEIC) |
| `--count` | `-c` | `8` | Photo count: `8` (top 4, bottom 4), `6` (top 3, bottom 3), or `4` (top 2, bottom 2) |
| `--paper` | `-p` | `4x6` | Paper format: `4x6`, `4x4`, `a4`, `letter`, `5x7`, or `WIDTHxHEIGHT` |
| `--photo-size` | `-s` | `indian` | Passport size: `indian` (35x45mm), `us` (2x2in), `ca`, `china`, `pan`, or `WxH` |
| `--spacing` | | `1.5` mm | Gap between adjacent photos in mm |
| `--margin` | | `3.0` mm | Minimum sheet outer margin in mm |
| `--border` | | `solid` | Cut border style: `solid`, `dashed`, `corners`, `none` |
| `--border-color`| | `#BBBBBB` | Hex color of cutting guidelines |
| `--crop` | | `face_upper` | Framing mode: `face_upper`, `center`, `fit` |
| `--orientation`| | `auto` | Sheet orientation: `auto`, `portrait`, `landscape` |
| `--dpi` | | `300` | Output resolution DPI |
| `--output` | `-o` | `./dist/` | Custom destination path for the PDF |
| `--also-image` | | `False` | Also export 300 DPI `.jpg` for photo kiosks |
| `--open` | | `False` | Automatically launch PDF in macOS Preview |

---

## 🧪 Verification & Testing

```bash
python3 /Users/krishnakanth/.gemini/config/skills/passport-photo-generator/scripts/test_generator.py
```
