#!/usr/bin/env python3
"""Standalone installer for the `slideforge` native PPTD compiler binary.

Downloads the pre-compiled binary with SHA256 checksum verification from
GitHub Releases for macOS (arm64 & x86_64), Linux (x86_64 & aarch64), or Windows (x86_64),
with automatic cargo build fallback and manual installation instructions.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Tuple

REPO = "shiquda/slideforge"
VERSION = "1.0.4"


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
        p = Path(found).resolve()
        if p.is_file() and os.access(p, os.X_OK):
            return p

    home = Path.home()
    candidates = [
        home / ".local" / "bin" / "slideforge",
        home / ".cargo" / "bin" / "slideforge",
        Path("/usr/local/bin/slideforge"),
        Path("/opt/homebrew/bin/slideforge"),
        Path(__file__).resolve().parent.parent / "bin" / "slideforge",
        # Local workspace checkout fallback
        Path.cwd() / "slideforge" / "target" / "release" / "slideforge",
    ]
    if platform.system().lower() == "windows":
        candidates.extend([
            home / "AppData" / "Local" / "Programs" / "slideforge" / "slideforge.exe",
            home / ".cargo" / "bin" / "slideforge.exe",
            home / ".local" / "bin" / "slideforge.exe",
            Path.cwd() / "slideforge" / "target" / "release" / "slideforge.exe",
        ])

    for c in candidates:
        if c.is_file() and (platform.system().lower() == "windows" or os.access(c, os.X_OK)):
            return c.resolve()

    return None


def fetch_checksums(version: str) -> dict[str, str]:
    """Fetch SHA256SUMS.txt from GitHub release if available."""
    sums_url = f"https://github.com/{REPO}/releases/download/v{version}/SHA256SUMS.txt"
    req = urllib.request.Request(
        sums_url,
        headers={"User-Agent": "open-pptd-skill-installer/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            checksums = {}
            for line in text.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    h, name = parts[0], parts[1].lstrip("*")
                    checksums[name] = h
            return checksums
    except Exception:
        return {}


def install_from_release(dest_dir: Path, version: str = VERSION) -> Path:
    target_info = detect_target()
    if not target_info:
        raise RuntimeError(
            f"Unsupported operating system or CPU architecture: system='{platform.system()}', machine='{platform.machine()}'.\n"
            f"Please compile slideforge from source using: cargo install --git https://github.com/{REPO}.git"
        )

    target, archive_name = target_info
    url = f"https://github.com/{REPO}/releases/download/v{version}/{archive_name}"
    print(f"[open-pptd-skill] Downloading prebuilt slideforge v{version} for {target}...")
    print(f"[open-pptd-skill] URL: {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "open-pptd-skill-installer/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as err:
        raise RuntimeError(
            f"Failed to download prebuilt binary (HTTP {err.code}: {err.reason}). "
            f"Release asset '{archive_name}' may not be published yet for v{version}."
        ) from err
    except urllib.error.URLError as err:
        raise RuntimeError(
            f"Network connection failed while downloading {url}: {err.reason}"
        ) from err

    # SHA256 checksum verification
    expected_sums = fetch_checksums(version)
    if archive_name in expected_sums:
        expected_sha = expected_sums[archive_name]
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha.lower() != expected_sha.lower():
            raise RuntimeError(
                f"SHA256 checksum mismatch for {archive_name}!\n"
                f"  Expected: {expected_sha}\n"
                f"  Actual:   {actual_sha}\n"
                f"The downloaded archive may be corrupted or compromised."
            )
        print(f"[open-pptd-skill] SHA256 checksum verified: {actual_sha[:12]}...")
    else:
        actual_sha = hashlib.sha256(data).hexdigest()
        print(f"[open-pptd-skill] SHA256 (unverified): {actual_sha[:12]}...")

    dest_dir.mkdir(parents=True, exist_ok=True)
    bin_name = "slideforge.exe" if platform.system().lower() == "windows" else "slideforge"
    dest_path = dest_dir / bin_name

    extracted = False
    if archive_name.endswith(".tar.gz") or archive_name.endswith(".tgz"):
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                if Path(member.name).name == bin_name:
                    f = tar.extractfile(member)
                    if f:
                        dest_path.write_bytes(f.read())
                        extracted = True
                        break
    elif archive_name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                if Path(name).name == bin_name:
                    dest_path.write_bytes(z.read(name))
                    extracted = True
                    break

    if not extracted or not dest_path.is_file():
        raise RuntimeError(f"Downloaded archive '{archive_name}' did not contain the executable '{bin_name}'.")

    dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[open-pptd-skill] Installed slideforge to: {dest_path}")
    return dest_path


def install_from_cargo(dest_dir: Path) -> Path:
    print("[open-pptd-skill] Attempting fallback compilation via cargo...", file=sys.stderr)
    cargo_bin = shutil.which("cargo")
    if not cargo_bin:
        raise RuntimeError("`cargo` is not installed on this machine, cannot build from source.")

    dest_dir.mkdir(parents=True, exist_ok=True)
    # Install directly into dest_dir.parent to place binary into dest_dir
    install_root = dest_dir.parent if dest_dir.name == "bin" else dest_dir
    cmd = ["cargo", "install", "--git", f"https://github.com/{REPO}.git", "--root", str(install_root), "--force"]
    print(f"[open-pptd-skill] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    bin_name = "slideforge.exe" if platform.system().lower() == "windows" else "slideforge"
    installed = (install_root / "bin" / bin_name) if dest_dir.name == "bin" else (dest_dir / bin_name)
    if not installed.is_file():
        raise RuntimeError(f"Cargo build finished but binary not found at {installed}")

    installed.chmod(installed.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[open-pptd-skill] Successfully built and installed slideforge via cargo: {installed}")
    return installed


def print_manual_install_instructions(dest_dir: Path) -> None:
    bin_name = "slideforge.exe" if platform.system().lower() == "windows" else "slideforge"
    target_path = dest_dir / bin_name
    print("\n" + "=" * 70, file=sys.stderr)
    print("SLIDEFORGE MANUAL INSTALLATION GUIDE", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("Automatic installation could not be completed. You can install slideforge manually:", file=sys.stderr)
    print(f"\n1. Precompiled binary from GitHub Releases:\n   https://github.com/{REPO}/releases", file=sys.stderr)
    print(f"   Download the archive for your OS, extract '{bin_name}', and place it at:\n   {target_path}", file=sys.stderr)
    print(f"\n2. Or compile with Rust / Cargo:\n   cargo install --git https://github.com/{REPO}.git", file=sys.stderr)
    print(f"\n3. Ensure {dest_dir} is in your system PATH:\n   export PATH=\"{dest_dir}:$PATH\"", file=sys.stderr)
    print("=" * 70 + "\n", file=sys.stderr)


def ensure_slideforge(force_reinstall: bool = False, install_dir: Optional[Path] = None) -> Path:
    if not force_reinstall:
        existing = find_slideforge()
        if existing:
            return existing

    if install_dir is None:
        install_dir = Path.home() / ".local" / "bin"

    errors = []
    # 1. Try download prebuilt release
    try:
        return install_from_release(install_dir)
    except Exception as e:
        errors.append(f"Release download: {e}")
        print(f"[open-pptd-skill] Precompiled binary download failed: {e}", file=sys.stderr)

    # 2. Try cargo fallback
    try:
        return install_from_cargo(install_dir)
    except Exception as e:
        errors.append(f"Cargo build: {e}")
        print(f"[open-pptd-skill] Cargo build fallback failed: {e}", file=sys.stderr)

    # 3. Print instructions and fail cleanly
    print_manual_install_instructions(install_dir)
    raise RuntimeError(
        "Could not automatically install slideforge:\n  - " + "\n  - ".join(errors)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Install slideforge native PPTD compiler binary")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.home() / ".local" / "bin",
        help="Destination directory (default: ~/.local/bin)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if already installed",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=VERSION,
        help=f"Specific slideforge version to install (default: {VERSION})",
    )
    args = parser.parse_args()

    try:
        bin_path = ensure_slideforge(force_reinstall=args.force, install_dir=args.dir)
        proc = subprocess.run([str(bin_path), "--version"], capture_output=True, text=True, check=True)
        print(f"[open-pptd-skill] Success! {proc.stdout.strip()} is ready at {bin_path}.")
        return 0
    except Exception as err:
        print(f"[open-pptd-skill] Installation error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
