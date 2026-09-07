#!/usr/bin/env python3
"""
Passport Photo Sheet Generator CLI
----------------------------------
Takes any portrait image, formats standardized passport photos (Indian/UK/EU 35x45mm, US 2x2in, custom),
tiles them across chosen paper sizes (4x4 inch, 4x6 inch, A4, Letter, 5x7 inch, custom),
draws precision cutting guides, and generates a print-ready 300 DPI PDF.

CRITICAL COUNT SPECIFICATION:
- Supported photo counts: 8 photos, 6 photos, or 4 photos.
- Default: 8 photos arranged as TOP 4, BOTTOM 4 (4 columns x 2 rows).
- 6 photos: 3 columns x 2 rows (top 3, bottom 3).
- 4 photos: 2 columns x 2 rows (top 2, bottom 2).

Usage:
  python3 generate_passport_pdf.py <input_image> [options]

Examples:
  # Default: 8 photos (top 4, bottom 4) on 4x6 paper
  python3 generate_passport_pdf.py photo.jpg --open

  # 8 photos on 4x4 paper
  python3 generate_passport_pdf.py photo.jpg --paper 4x4 --count 8 --open

  # 4 photos (2x2) on 4x4 paper
  python3 generate_passport_pdf.py photo.jpg --paper 4x4 --count 4 --open

  # 6 photos on 4x6 paper
  python3 generate_passport_pdf.py photo.jpg --paper 4x6 --count 6 --open

  # 8 photos on A4 sheet
  python3 generate_passport_pdf.py photo.jpg --paper a4 --count 8 --open
"""

import argparse
import io
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Unit conversions to points (1 pt = 1/72 inch, 1 inch = 25.4 mm)
PT_PER_INCH = 72.0
MM_PER_INCH = 25.4
PT_PER_MM = PT_PER_INCH / MM_PER_INCH  # ~ 2.83464567 pt/mm

# Standard Paper Sizes (Width x Height in mm)
STANDARD_PAPERS = {
    "4x4": (4.0 * MM_PER_INCH, 4.0 * MM_PER_INCH),        # 101.6 x 101.6 mm (4x4 inch square)
    "4x6": (6.0 * MM_PER_INCH, 4.0 * MM_PER_INCH),        # 152.4 x 101.6 mm (Standard 4R photo paper landscape)
    "6x4": (6.0 * MM_PER_INCH, 4.0 * MM_PER_INCH),        # 152.4 x 101.6 mm
    "5x7": (7.0 * MM_PER_INCH, 5.0 * MM_PER_INCH),        # 177.8 x 127.0 mm (5R landscape)
    "7x5": (7.0 * MM_PER_INCH, 5.0 * MM_PER_INCH),
    "a4": (210.0, 297.0),                                  # 210.0 x 297.0 mm
    "letter": (8.5 * MM_PER_INCH, 11.0 * MM_PER_INCH),    # 215.9 x 279.4 mm
    "3.5x5": (5.0 * MM_PER_INCH, 3.5 * MM_PER_INCH),      # 127.0 x 88.9 mm (3R)
}

# Standard Passport Photo Sizes (Width x Height in mm)
STANDARD_PHOTO_SIZES = {
    "indian": (35.0, 45.0),
    "india": (35.0, 45.0),
    "in": (35.0, 45.0),
    "uk": (35.0, 45.0),
    "eu": (35.0, 45.0),
    "schengen": (35.0, 45.0),
    "australia": (35.0, 45.0),
    "au": (35.0, 45.0),
    "singapore": (35.0, 45.0),
    "sg": (35.0, 45.0),
    "japan": (35.0, 45.0),
    "jp": (35.0, 45.0),
    "us": (2.0 * MM_PER_INCH, 2.0 * MM_PER_INCH),          # 50.8 x 50.8 mm (2x2 inch)
    "usa": (2.0 * MM_PER_INCH, 2.0 * MM_PER_INCH),
    "2x2": (2.0 * MM_PER_INCH, 2.0 * MM_PER_INCH),
    "ca": (50.0, 70.0),
    "canada": (50.0, 70.0),
    "china": (33.0, 48.0),
    "cn": (33.0, 48.0),
    "pan": (25.0, 35.0),                                   # Indian PAN card size (approx 25x35mm)
}


def parse_dimension(dim_str: str, default_unit="mm") -> tuple[float, float]:
    """
    Parses a dimension string like '4x4', '4x6in', '35x45mm', '210x297', or standard named size.
    Returns (width_mm, height_mm).
    """
    clean = dim_str.strip().lower()

    if clean in STANDARD_PAPERS:
        return STANDARD_PAPERS[clean]

    if clean in STANDARD_PHOTO_SIZES:
        return STANDARD_PHOTO_SIZES[clean]

    m = re.match(r"^([\d.]+)\s*[xX*]\s*([\d.]+)\s*(in|inch|inches|mm|cm|pt)?$", clean)
    if not m:
        raise ValueError(f"Cannot parse dimension: '{dim_str}'. Examples: '4x4', '4x6', 'a4', '35x45mm', '2x2in'")

    val_w = float(m.group(1))
    val_h = float(m.group(2))
    unit = m.group(3) or default_unit

    if unit in ("in", "inch", "inches"):
        return (val_w * MM_PER_INCH, val_h * MM_PER_INCH)
    elif unit == "cm":
        return (val_w * 10.0, val_h * 10.0)
    elif unit == "pt":
        return (val_w / PT_PER_MM, val_h / PT_PER_MM)
    else:  # mm
        return (val_w, val_h)


def crop_and_prep_image(
    image_path: str | Path,
    target_w_mm: float,
    target_h_mm: float,
    dpi: int = 300,
    crop_mode: str = "face_upper",
) -> Image.Image:
    """
    Loads, normalizes, crops to exact aspect ratio, and resizes to target print DPI.
    """
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)

    if img.mode != "RGB":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")

    orig_w, orig_h = img.size
    target_aspect = target_w_mm / target_h_mm
    orig_aspect = orig_w / orig_h

    if crop_mode == "fit":
        if orig_aspect > target_aspect:
            fit_w = orig_w
            fit_h = int(round(orig_w / target_aspect))
        else:
            fit_h = orig_h
            fit_w = int(round(orig_h * target_aspect))

        padded = Image.new("RGB", (fit_w, fit_h), (255, 255, 255))
        paste_x = (fit_w - orig_w) // 2
        paste_y = (fit_h - orig_h) // 2
        padded.paste(img, (paste_x, paste_y))
        cropped = padded

    else:
        if orig_aspect > target_aspect:
            new_w = int(round(orig_h * target_aspect))
            offset_x = (orig_w - new_w) // 2
            cropped = img.crop((offset_x, 0, offset_x + new_w, orig_h))
        else:
            new_h = int(round(orig_w / target_aspect))
            slack_y = orig_h - new_h
            if crop_mode == "face_upper":
                # Portrait bias: face is in upper portion
                offset_y = int(round(slack_y * 0.25))
            else:
                offset_y = slack_y // 2
            offset_y = max(0, min(offset_y, slack_y))
            cropped = img.crop((0, offset_y, orig_w, offset_y + new_h))

    target_px_w = int(round((target_w_mm / MM_PER_INCH) * dpi))
    target_px_h = int(round((target_h_mm / MM_PER_INCH) * dpi))

    resized = cropped.resize((target_px_w, target_px_h), resample=Image.Resampling.LANCZOS)
    return resized


def compute_optimal_layout(
    paper_w_mm: float,
    paper_h_mm: float,
    photo_w_mm: float,
    photo_h_mm: float,
    count: int = 8,
    margin_mm: float = 3.0,
    spacing_mm: float = 1.5,
    orientation: str = "auto",
) -> tuple[float, float, int, int, int, float, float, float, float]:
    """
    Computes sheet orientation, grid (cols, rows), effective photo dimensions (auto-scaled if needed),
    and effective spacing/margins.
    Returns: (sheet_w_mm, sheet_h_mm, cols, rows, count, eff_photo_w_mm, eff_photo_h_mm, eff_margin_mm, eff_spacing_mm)
    """
    # Enforce standard photo counts: 8 (top 4, bottom 4), 6 (top 3, bottom 3), or 4 (top 2, bottom 2)
    if count == 8 or count is None:
        cols, rows = 4, 2
        total_count = 8
    elif count == 6:
        cols, rows = 3, 2
        total_count = 6
    elif count == 4:
        cols, rows = 2, 2
        total_count = 4
    else:
        # User specified another arbitrary count
        total_count = count
        cols = min(count, 4)
        rows = (count + cols - 1) // cols

    # Determine sheet orientation
    # 4 cols x 2 rows is inherently wider than tall -> landscape orientation is ideal
    if orientation == "portrait":
        sheet_w = min(paper_w_mm, paper_h_mm)
        sheet_h = max(paper_w_mm, paper_h_mm)
        # If portrait requested on 6-photo layout, allow 2 cols x 3 rows
        if count == 6:
            cols, rows = 2, 3
    elif orientation == "landscape":
        sheet_w = max(paper_w_mm, paper_h_mm)
        sheet_h = min(paper_w_mm, paper_h_mm)
    else:  # auto
        if abs(paper_w_mm - paper_h_mm) < 0.1:  # Square sheet like 4x4
            sheet_w = paper_w_mm
            sheet_h = paper_h_mm
        elif cols >= rows:  # Landscape fits 4x2 better
            sheet_w = max(paper_w_mm, paper_h_mm)
            sheet_h = min(paper_w_mm, paper_h_mm)
        else:
            sheet_w = min(paper_w_mm, paper_h_mm)
            sheet_h = max(paper_w_mm, paper_h_mm)

    # Check available printable area
    avail_w = sheet_w - (2 * margin_mm)
    avail_h = sheet_h - (2 * margin_mm)

    needed_w = cols * photo_w_mm + (cols - 1) * spacing_mm
    needed_h = rows * photo_h_mm + (rows - 1) * spacing_mm

    # If it fits within available area with standard margin
    if needed_w <= avail_w and needed_h <= avail_h:
        eff_photo_w = photo_w_mm
        eff_photo_h = photo_h_mm
        eff_spacing = spacing_mm
        eff_margin = margin_mm
    else:
        # Check if reducing margin to 1mm allows 100% scale fit (e.g. 4 photos on 4x4)
        minimal_avail_w = sheet_w - 2.0
        minimal_avail_h = sheet_h - 2.0
        if needed_w <= minimal_avail_w and needed_h <= minimal_avail_h:
            eff_photo_w = photo_w_mm
            eff_photo_h = photo_h_mm
            eff_spacing = spacing_mm
            eff_margin = (sheet_w - needed_w) / 2.0
        else:
            # Scale proportionally to fit exact grid (e.g. 8 photos on 4x4 paper)
            scale_w = (sheet_w - 2.0 * margin_mm - (cols - 1) * spacing_mm) / (cols * photo_w_mm)
            scale_h = (sheet_h - 2.0 * margin_mm - (rows - 1) * spacing_mm) / (rows * photo_h_mm)
            scale = max(0.1, min(scale_w, scale_h))

            eff_photo_w = photo_w_mm * scale
            eff_photo_h = photo_h_mm * scale
            eff_spacing = spacing_mm * scale
            eff_margin = margin_mm

    return (
        sheet_w,
        sheet_h,
        cols,
        rows,
        total_count,
        eff_photo_w,
        eff_photo_h,
        eff_margin,
        eff_spacing,
    )


def generate_passport_pdf(
    image_path: str | Path,
    output_pdf: str | Path,
    paper_size: str = "4x6",
    photo_size: str = "indian",
    count: int = 8,
    spacing_mm: float = 1.5,
    margin_mm: float = 3.0,
    border_style: str = "solid",
    border_color: str = "#CCCCCC",
    border_width_pt: float = 0.5,
    crop_mode: str = "face_upper",
    dpi: int = 300,
    orientation: str = "auto",
    also_image: bool = False,
) -> dict:
    """
    Main generator routine. Produces the print PDF and optional preview raster.
    """
    image_path = Path(image_path).resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    # Default paper: if count is 4 and paper not explicitly set, 4x4 works great; otherwise 4x6
    paper_w_mm, paper_h_mm = parse_dimension(
        paper_size,
        default_unit="in" if "x" in paper_size and not any(u in paper_size for u in ["mm", "cm", "pt"]) else "mm"
    )
    base_photo_w_mm, base_photo_h_mm = parse_dimension(photo_size, default_unit="mm")

    # Compute layout
    (
        sheet_w_mm,
        sheet_h_mm,
        cols,
        rows,
        total_count,
        photo_w_mm,
        photo_h_mm,
        eff_margin,
        eff_spacing,
    ) = compute_optimal_layout(
        paper_w_mm=paper_w_mm,
        paper_h_mm=paper_h_mm,
        photo_w_mm=base_photo_w_mm,
        photo_h_mm=base_photo_h_mm,
        count=count,
        margin_mm=margin_mm,
        spacing_mm=spacing_mm,
        orientation=orientation,
    )

    # Crop and prep image at print DPI
    cropped_img = crop_and_prep_image(
        image_path,
        target_w_mm=photo_w_mm,
        target_h_mm=photo_h_mm,
        dpi=dpi,
        crop_mode=crop_mode,
    )

    img_buffer = io.BytesIO()
    cropped_img.save(img_buffer, format="JPEG", quality=98, dpi=(dpi, dpi))
    img_buffer.seek(0)

    # Convert dimensions to ReportLab points
    sheet_w_pt = sheet_w_mm * PT_PER_MM
    sheet_h_pt = sheet_h_mm * PT_PER_MM
    photo_w_pt = photo_w_mm * PT_PER_MM
    photo_h_pt = photo_h_mm * PT_PER_MM
    spacing_pt = eff_spacing * PT_PER_MM

    grid_w_pt = cols * photo_w_pt + (cols - 1) * spacing_pt
    grid_h_pt = rows * photo_h_pt + (rows - 1) * spacing_pt

    start_x_pt = (sheet_w_pt - grid_w_pt) / 2.0
    start_y_pt = (sheet_h_pt - grid_h_pt) / 2.0

    output_pdf = Path(output_pdf).resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_pdf), pagesize=(sheet_w_pt, sheet_h_pt))
    c.setTitle(f"Passport Photos Sheet - {total_count} Photos")
    c.setAuthor("Passport Photo Generator")

    placed = 0
    img_reader = ImageReader(img_buffer)

    for r in range(rows):
        for col in range(cols):
            if placed >= total_count:
                break

            x = start_x_pt + col * (photo_w_pt + spacing_pt)
            y = start_y_pt + (rows - 1 - r) * (photo_h_pt + spacing_pt)

            c.drawImage(
                img_reader,
                x,
                y,
                width=photo_w_pt,
                height=photo_h_pt,
                preserveAspectRatio=False,
            )

            if border_style != "none":
                c.saveState()
                c.setStrokeColor(HexColor(border_color))
                c.setLineWidth(border_width_pt)

                if border_style == "dashed":
                    c.setDash(2, 2)
                    c.rect(x, y, photo_w_pt, photo_h_pt)
                elif border_style == "corners":
                    tick = 2.0 * PT_PER_MM
                    c.line(x - tick, y, x, y)
                    c.line(x, y - tick, x, y)
                    c.line(x + photo_w_pt, y, x + photo_w_pt + tick, y)
                    c.line(x + photo_w_pt, y - tick, x + photo_w_pt, y)
                    c.line(x - tick, y + photo_h_pt, x, y + photo_h_pt)
                    c.line(x, y + photo_h_pt, x, y + photo_h_pt + tick)
                    c.line(x + photo_w_pt, y + photo_h_pt, x + photo_w_pt + tick, y + photo_h_pt)
                    c.line(x + photo_w_pt, y + photo_h_pt, x + photo_w_pt, y + photo_h_pt + tick)
                else:  # solid
                    c.rect(x, y, photo_w_pt, photo_h_pt)

                c.restoreState()

            placed += 1

    c.showPage()
    c.save()

    image_out_path = None
    if also_image:
        sheet_px_w = int(round((sheet_w_mm / MM_PER_INCH) * dpi))
        sheet_px_h = int(round((sheet_h_mm / MM_PER_INCH) * dpi))
        sheet_img = Image.new("RGB", (sheet_px_w, sheet_px_h), (255, 255, 255))
        draw = ImageDraw.Draw(sheet_img)

        photo_px_w = cropped_img.width
        photo_px_h = cropped_img.height
        spacing_px = int(round((eff_spacing / MM_PER_INCH) * dpi))

        grid_px_w = cols * photo_px_w + (cols - 1) * spacing_px
        grid_px_h = rows * photo_px_h + (rows - 1) * spacing_px

        start_px_x = (sheet_px_w - grid_px_w) // 2
        start_px_y = (sheet_px_h - grid_px_h) // 2

        img_placed = 0
        for r in range(rows):
            for col in range(cols):
                if img_placed >= total_count:
                    break
                px = start_px_x + col * (photo_px_w + spacing_px)
                py = start_px_y + r * (photo_px_h + spacing_px)

                sheet_img.paste(cropped_img, (px, py))

                if border_style in ("solid", "dashed"):
                    draw.rectangle(
                        [px, py, px + photo_px_w, py + photo_px_h],
                        outline=border_color,
                        width=1,
                    )
                img_placed += 1

        image_out_path = output_pdf.with_suffix(".jpg")
        sheet_img.save(image_out_path, quality=95, dpi=(dpi, dpi))

    layout_desc = f"{cols} cols x {rows} rows"
    if count == 8:
        layout_desc += " (Top 4, Bottom 4)"
    elif count == 6:
        layout_desc += " (Top 3, Bottom 3)"
    elif count == 4:
        layout_desc += " (Top 2, Bottom 2)"

    return {
        "pdf_path": str(output_pdf),
        "image_path": str(image_out_path) if image_out_path else None,
        "paper_size": f"{sheet_w_mm:.1f} x {sheet_h_mm:.1f} mm ({sheet_w_mm/MM_PER_INCH:.2f} x {sheet_h_mm/MM_PER_INCH:.2f} in)",
        "photo_size": f"{photo_w_mm:.1f} x {photo_h_mm:.1f} mm ({photo_w_mm/MM_PER_INCH:.2f} x {photo_h_mm/MM_PER_INCH:.2f} in)",
        "layout": layout_desc,
        "count": total_count,
        "dpi": dpi,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Passport Photo Generator: Formats and tiles portrait images onto printable paper sheets as PDF."
    )
    parser.add_argument("image", help="Path to input portrait photo (JPG, PNG, WEBP, etc.)")
    parser.add_argument(
        "--paper",
        "-p",
        default="4x6",
        help="Paper size: '4x6', '4x4', 'a4', 'letter', '5x7', or custom 'WxH[in|mm]' (default: 4x6)",
    )
    parser.add_argument(
        "--photo-size",
        "-s",
        default="indian",
        help="Passport standard: 'indian'/'uk'/'eu' (35x45mm), 'us' (2x2in), 'ca' (50x70mm), or 'WxH[in|mm]' (default: indian)",
    )
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        choices=[4, 6, 8],
        default=8,
        help="Number of photos: 8 (default: top 4, bottom 4), 6 (top 3, bottom 3), or 4 (top 2, bottom 2)",
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=1.5,
        help="Spacing between adjacent photos in mm (default: 1.5 mm)",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=3.0,
        help="Minimum outer sheet margin in mm (default: 3.0 mm)",
    )
    parser.add_argument(
        "--border",
        choices=["solid", "dashed", "corners", "none"],
        default="solid",
        help="Cutting guide border style (default: solid)",
    )
    parser.add_argument(
        "--border-color",
        default="#BBBBBB",
        help="Hex color for cutting guidelines (default: #BBBBBB)",
    )
    parser.add_argument(
        "--crop",
        choices=["face_upper", "center", "fit"],
        default="face_upper",
        help="Aspect framing: 'face_upper' (portrait upper bias), 'center', or 'fit' (letterboxed) (default: face_upper)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output resolution in DPI (default: 300)",
    )
    parser.add_argument(
        "--orientation",
        choices=["auto", "portrait", "landscape"],
        default="auto",
        help="Paper orientation (default: auto)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output PDF path (default: dist/passport_<paper>_<count>_<timestamp>.pdf)",
    )
    parser.add_argument(
        "--also-image",
        action="store_true",
        help="Also export companion 300 DPI JPEG image file of the sheet",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated PDF immediately on macOS Preview",
    )
    parser.add_argument(
        "--discord",
        help="Optional Discord channel ID or webhook to dispatch the PDF",
    )

    args = parser.parse_args()

    if args.output:
        out_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        paper_clean = args.paper.replace("*", "x").replace("/", "-")
        out_dir = Path.cwd() / "dist"
        out_path = out_dir / f"passport_{paper_clean}_{args.count}photos_{timestamp}.pdf"

    try:
        res = generate_passport_pdf(
            image_path=args.image,
            output_pdf=out_path,
            paper_size=args.paper,
            photo_size=args.photo_size,
            count=args.count,
            spacing_mm=args.spacing,
            margin_mm=args.margin,
            border_style=args.border,
            border_color=args.border_color,
            crop_mode=args.crop,
            dpi=args.dpi,
            orientation=args.orientation,
            also_image=args.also_image,
        )

        print("\n==========================================")
        print("  📸 PASSPORT PHOTO SHEET GENERATOR")
        print("==========================================")
        print(f"📄 Paper Size  : {res['paper_size']}")
        print(f"👤 Photo Size  : {res['photo_size']}")
        print(f"🔢 Layout      : {res['layout']} ({res['count']} photos total)")
        print(f"🎯 Resolution  : {res['dpi']} DPI")
        print(f"💾 PDF Output  : {res['pdf_path']}")
        if res["image_path"]:
            print(f"🖼️  Image Output: {res['image_path']}")
        print("------------------------------------------")
        print(f"MEDIA:{res['pdf_path']}")
        print("==========================================\n")

        if args.open:
            if sys.platform == "darwin":
                subprocess.run(["open", res["pdf_path"]], check=False)
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", res["pdf_path"]], check=False)

    except Exception as e:
        print(f"❌ Error generating passport photos: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
