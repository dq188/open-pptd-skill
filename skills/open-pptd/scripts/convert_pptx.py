#!/usr/bin/env python3
"""Decompile a native PPTX file into an editable PPTD project via pptd.

Reverses an existing presentation into a declarative `deck.pptd` manifest with
per-page `.page` YAML files, extracting text, shapes, colors, layout, and tables.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

try:
    from .install_binary import ensure_pptd
except ImportError:
    from install_binary import ensure_pptd


def convert_pptx(
    pptx_path: Path,
    out_dir: Optional[Path] = None,
    pptd_bin: Optional[Path] = None,
) -> Path:
    pptx_path = pptx_path.expanduser().resolve()
    if not pptx_path.is_file() or pptx_path.suffix.lower() != ".pptx":
        raise ValueError(f"Expected a valid .pptx file, got: {pptx_path}")

    if out_dir is None:
        out_dir = pptx_path.with_suffix("")
    else:
        out_dir = out_dir.expanduser().resolve()

    out_dir.mkdir(parents=True, exist_ok=True)

    if pptd_bin is None:
        compiler = ensure_pptd()
    else:
        compiler = pptd_bin

    if not compiler or not compiler.is_file():
        raise RuntimeError("pptd compiler binary could not be located or installed.")

    t0 = time.monotonic()
    print(f"[open-pptd] Decompiling {pptx_path.name} -> {out_dir}/ via pptd convert...")
    proc = subprocess.run(
        [str(compiler), "convert", str(pptx_path), str(out_dir)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"[open-pptd] Decompilation failed:\n{proc.stderr}", file=sys.stderr)
        raise RuntimeError(f"pptd convert exited with code {proc.returncode}")

    elapsed = time.monotonic() - t0
    manifest = out_dir / "deck.pptd"
    pages = list((out_dir / "pages").glob("*.page")) if (out_dir / "pages").is_dir() else []
    print(f"[open-pptd] Successfully decompiled into PPTD project in {elapsed:.2f}s ({len(pages)} pages)")
    print(f"[open-pptd] Manifest: {manifest}")
    return out_dir


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert/decompile a PPTX presentation into a PPTD project")
    parser.add_argument("pptx", type=Path, help="Path to input .pptx presentation")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output project directory")
    parser.add_argument("--compiler", type=Path, default=None, help="Explicit path to pptd binary")
    args = parser.parse_args(argv)

    try:
        convert_pptx(args.pptx, out_dir=args.output, pptd_bin=args.compiler)
        return 0
    except Exception as err:
        print(f"[open-pptd] Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
