#!/usr/bin/env python3
"""Native PPTX export for PPTD projects via slideforge compiler.

Replaces the legacy browser-based export pipeline with a 100% offline, native
Rust compiler that generates native OpenXML PPTX with full DrawingML, native tables,
LaTeX math formulas, vector shapes, and safe cross-platform font fallbacks.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

# Import binary installer
try:
    from .install_binary import ensure_slideforge
except ImportError:
    # Standalone execution
    from install_binary import ensure_slideforge


def find_manifest(source: Path) -> Path:
    source = source.expanduser().resolve()
    if source.is_file():
        if source.suffix.lower() == ".pptd":
            return source
        raise ValueError(f"Expected a .pptd file, got {source.name}")

    if not source.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source}")

    manifests = sorted(source.glob("*.pptd"))
    if not manifests:
        raise FileNotFoundError(f"No .pptd manifest found in {source}")
    if len(manifests) > 1:
        exact = source / "deck.pptd"
        if exact.is_file():
            return exact
        raise ValueError(f"Multiple .pptd manifests found: {[m.name for m in manifests]}; please specify one explicitly.")
    return manifests[0]


def export_pptx(
    source: Path,
    output: Optional[Path] = None,
    pdf: bool = False,
    slideforge_bin: Optional[Path] = None,
) -> Path:
    manifest = find_manifest(source)
    if output is None:
        output = manifest.with_suffix(".pptx")
    else:
        output = output.expanduser().resolve()
        if output.is_dir():
            output = output / f"{manifest.stem}.pptx"

    output.parent.mkdir(parents=True, exist_ok=True)

    # 1. Resolve compiler
    if slideforge_bin is None:
        compiler = ensure_slideforge()
    else:
        compiler = slideforge_bin

    if not compiler or not compiler.is_file():
        raise RuntimeError("slideforge compiler binary could not be located or installed.")

    # 2. Build PPTX
    t0 = time.monotonic()
    print(f"[open-pptd-skill] Compiling {manifest.name} -> {output.name} via slideforge...")
    proc = subprocess.run(
        [str(compiler), "build", str(manifest), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"[open-pptd-skill] Compilation failed:\n{proc.stderr}", file=sys.stderr)
        raise RuntimeError(f"slideforge exited with code {proc.returncode}")

    elapsed = time.monotonic() - t0
    size_kb = output.stat().st_size / 1024
    print(f"[open-pptd-skill] Successfully built native PPTX in {elapsed:.2f}s ({size_kb:.1f} KB)")
    print(f"[open-pptd-skill] Output: {output}")

    # 3. Optional PDF conversion via soffice
    if pdf:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if soffice:
            print("[open-pptd-skill] Converting PPTX to PDF via LibreOffice...")
            pdf_proc = subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", str(output), "--outdir", str(output.parent)],
                capture_output=True,
                text=True,
            )
            if pdf_proc.returncode == 0:
                pdf_path = output.with_suffix(".pdf")
                if pdf_path.is_file():
                    print(f"[open-pptd-skill] Generated PDF: {pdf_path}")
        else:
            print("[open-pptd-skill] Notice: LibreOffice not installed; skipping PDF export.", file=sys.stderr)

    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export a PPTD project to native editable PPTX via slideforge")
    parser.add_argument("source", type=Path, help="Path to deck.pptd manifest or project directory")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .pptx path (default: <manifest>.pptx)")
    parser.add_argument("--pdf", action="store_true", help="Also convert to PDF via headless LibreOffice if available")
    parser.add_argument("--compiler", type=Path, default=None, help="Explicit path to slideforge binary")
    args = parser.parse_args(argv)

    try:
        export_pptx(args.source, output=args.output, pdf=args.pdf, slideforge_bin=args.compiler)
        return 0
    except Exception as err:
        print(f"[open-pptd-skill] Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
