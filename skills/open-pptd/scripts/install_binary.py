#!/usr/bin/env python3
"""Standalone installer for the `slideforge` native PPTD compiler binary.

Downloads the pre-compiled binary from GitHub Releases for macOS, Linux, or Windows,
or builds from source via `cargo` if pre-compiled binaries are not supported.
"""

from __future__ import annotations

import argparse
import io
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Tuple

REPO = "shiquda/slideforge"
VERSION = "1.0.2"


def detect_target() -> Optional[Tuple[str, str]]:
    """Return (target_triple, archive_name)."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return ("aarch64-apple-darwin", f"slideforge-{VERSION}-aarch64-macos.tar.gz")
        elif machine in ("x86_64", "amd64"):
            return ("x86_64-apple-darwin", f"slideforge-{VERSION}-x86_64-macos.tar.gz")
    elif system == "linux":
        if machine in ("x86_64", "amd64"):
            return ("x86_64-unknown-linux-gnu", f"slideforge-{VERSION}-x86_64-linux.tar.gz")
        elif machine in ("aarch64", "arm64"):
            return ("aarch64-unknown-linux-gnu", f"slideforge-{VERSION}-aarch64-linux.tar.gz")
    elif system == "windows":
        if machine in ("x86_64", "amd64"):
            return ("x86_64-pc-windows-msvc", f"slideforge-{VERSION}-x86_64-windows.zip")

    return None


def find_slideforge() -> Optional[Path]:
    """Find existing slideforge executable in PATH or standard user directories."""
    found = shutil.which("slideforge")
    if found:
        return Path(found)

    home = Path.home()
    candidates = [
        home / ".local" / "bin" / "slideforge",
        home / ".cargo" / "bin" / "slideforge",
        Path("/usr/local/bin/slideforge"),
        Path("/opt/homebrew/bin/slideforge"),
        Path(__file__).resolve().parent.parent / "bin" / "slideforge",
    ]
    if platform.system().lower() == "windows":
        candidates.extend([
            home / "AppData" / "Local" / "Programs" / "slideforge" / "slideforge.exe",
            home / ".cargo" / "bin" / "slideforge.exe",
        ])

    for c in candidates:
        if c.is_file() and os.access(c, os.X_OK):
            return c

    return None


def install_from_release(dest_dir: Path) -> Path:
    target_info = detect_target()
    if not target_info:
        raise RuntimeError(f"Unsupported OS / architecture: {platform.system()} {platform.machine()}")

    target, archive_name = target_info
    url = f"https://github.com/{REPO}/releases/download/v{VERSION}/{archive_name}"
    print(f"[open-pptd-skill] Downloading prebuilt slideforge binary for {target}...")
    print(f"[open-pptd-skill] URL: {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "open-pptd-skill-installer/1.0"},
    )
    with urllib.request.urlopen(req) as resp:
        data = resp.read()

    dest_dir.mkdir(parents=True, exist_ok=True)
    bin_name = "slideforge.exe" if platform.system().lower() == "windows" else "slideforge"
    dest_path = dest_dir / bin_name

    if archive_name.endswith(".tar.gz") or archive_name.endswith(".tgz"):
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                if Path(member.name).name == bin_name:
                    f = tar.extractfile(member)
                    if f:
                        dest_path.write_bytes(f.read())
                        break
    elif archive_name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                if Path(name).name == bin_name:
                    dest_path.write_bytes(z.read(name))
                    break

    if not dest_path.is_file():
        raise RuntimeError(f"Archive did not contain executable {bin_name}")

    dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[open-pptd-skill] Installed slideforge to: {dest_path}")
    return dest_path


def install_from_cargo(dest_dir: Path) -> Path:
    print("[open-pptd-skill] Falling back to building slideforge via cargo...")
    subprocess.run(["cargo", "install", "--git", f"https://github.com/{REPO}.git", "--root", str(dest_dir.parent)], check=True)
    installed = dest_dir / ("slideforge.exe" if platform.system().lower() == "windows" else "slideforge")
    if not installed.is_file():
        raise RuntimeError(f"Cargo build completed but binary not found at {installed}")
    return installed


def ensure_slideforge(force_reinstall: bool = False, install_dir: Optional[Path] = None) -> Path:
    if not force_reinstall:
        existing = find_slideforge()
        if existing:
            return existing

    if install_dir is None:
        install_dir = Path.home() / ".local" / "bin"

    try:
        return install_from_release(install_dir)
    except Exception as e:
        print(f"[open-pptd-skill] Release download failed ({e}); attempting cargo fallback...", file=sys.stderr)
        return install_from_cargo(install_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install slideforge native PPTD compiler binary")
    parser.add_argument("--dir", type=Path, default=Path.home() / ".local" / "bin", help="Destination directory (default: ~/.local/bin)")
    parser.add_argument("--force", action="store_true", help="Force re-download even if already installed")
    args = parser.parse_args()

    try:
        bin_path = ensure_slideforge(force_reinstall=args.force, install_dir=args.dir)
        proc = subprocess.run([str(bin_path), "--version"], capture_output=True, text=True, check=True)
        print(f"[open-pptd-skill] Success! {proc.stdout.strip()} is ready to use.")
        return 0
    except Exception as err:
        print(f"[open-pptd-skill] Error installing slideforge: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
