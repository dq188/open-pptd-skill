#!/usr/bin/env python3
"""Offline image export and multi-page preview montage for PPTD projects.

Uses the native pptd compiler + headless document renderer to generate
high-resolution PNG images of every slide and a unified grid overview,
without requiring any browser automation, token authentication, or cloud services.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Sequence

from export_pptx import export_pptx


def build_montage(image_paths: list[Path], output_path: Path, cols: int = 5) -> None:
    try:
        from PIL import Image
    except ImportError:
        print("[open-pptd-skill] PIL/Pillow not installed; skipping overview grid generation.", file=sys.stderr)
        return

    if not image_paths:
        return

    n = len(image_paths)
    rows = (n + cols - 1) // cols
    thumb_w = 400
    thumb_h = int(thumb_w * 9 / 16)
    pad = 20

    total_w = cols * thumb_w + (cols + 1) * pad
    total_h = rows * thumb_h + (rows + 1) * pad

    grid = Image.new("RGB", (total_w, total_h), "#EFECE1")

    for idx, img_p in enumerate(image_paths):
        im = Image.open(img_p).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = pad + r * (thumb_h + pad)
        grid.paste(im, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output_path)
    print(f"[open-pptd-skill] Generated overview montage: {output_path}")


def export_images(
    source: Path,
    out_dir: Optional[Path] = None,
    dpi: int = 150,
) -> Path:
    source = source.expanduser().resolve()
    if out_dir is None:
        out_dir = (source.parent if source.is_file() else source) / "qa-images"
    else:
        out_dir = out_dir.expanduser().resolve()

    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pptd_img_") as tmp:
        tmp_pptx = Path(tmp) / "render.pptx"
        export_pptx(source, output=tmp_pptx)

        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        pdftoppm = shutil.which("pdftoppm")

        if not soffice or not pdftoppm:
            print("[open-pptd-skill] Image rendering requires `soffice` (LibreOffice) and `pdftoppm` (poppler-utils).", file=sys.stderr)
            print("[open-pptd-skill] PPTX was built successfully, but PNG rasterization is unavailable in this environment.", file=sys.stderr)
            return out_dir

        # Convert PPTX to PDF
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", str(tmp_pptx), "--outdir", tmp],
            check=True,
            capture_output=True,
        )
        tmp_pdf = Path(tmp) / "render.pdf"

        # Rasterize PDF to PNGs
        print(f"[open-pptd-skill] Rasterizing slides at {dpi} DPI...")
        prefix = pages_dir / "page"
        subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), str(tmp_pdf), str(prefix)],
            check=True,
            capture_output=True,
        )

        rendered_pages = sorted(pages_dir.glob("page-*.png"))
        print(f"[open-pptd-skill] Successfully exported {len(rendered_pages)} slide images to: {pages_dir}")

        # Build overview montage
        overview_path = out_dir / "overview.jpg"
        build_montage(rendered_pages, overview_path)

    return out_dir


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export a PPTD project to PNG images and overview montage")
    parser.add_argument("source", type=Path, help="Path to deck.pptd manifest or project directory")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory for images (default: qa-images)")
    parser.add_argument("--dpi", type=int, default=150, help="Image DPI (default: 150)")
    args = parser.parse_args(argv)

    try:
        export_images(args.source, out_dir=args.output, dpi=args.dpi)
        return 0
    except Exception as err:
        print(f"[open-pptd-skill] Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
