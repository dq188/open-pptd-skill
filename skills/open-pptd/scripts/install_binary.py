#!/usr/bin/env python3
"""Standalone installer for the `pptd` native PPTD compiler binary.

Downloads the pre-compiled binary with SHA256 checksum verification from
GitHub Releases for macOS (arm64 & x86_64), Linux (x86_64 & aarch64), or Windows (x86_64),
or falls back smoothly to `cargo install` if pre-compiled assets are unavailable.
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

REPO = "shiquda/open-pptd-skill"
REPO_CANDIDATES = ["shiquda/open-pptd-skill"]
VERSION = "1.3.5"


def detect_target(version: str = VERSION) -> Optional[Tuple[str, list[str]]]:
    """Return (target_triple, candidate_archive_names)."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return (
                "aarch64-apple-darwin",
                [f"pptd-{version}-aarch64-macos.tar.gz", "pptd-aarch64-macos.tar.gz"],
            )
        elif machine in ("x86_64", "amd64"):
            return (
                "x86_64-apple-darwin",
                [f"pptd-{version}-x86_64-macos.tar.gz", "pptd-x86_64-macos.tar.gz"],
            )
    elif system == "linux":
        if machine in ("x86_64", "amd64"):
            return (
                "x86_64-unknown-linux-gnu",
                [f"pptd-{version}-x86_64-linux.tar.gz", "pptd-x86_64-linux.tar.gz"],
            )
        elif machine in ("aarch64", "arm64"):
            return (
                "aarch64-unknown-linux-gnu",
                [f"pptd-{version}-aarch64-linux.tar.gz", "pptd-aarch64-linux.tar.gz"],
            )
    elif system == "windows":
        if machine in ("x86_64", "amd64"):
            return (
                "x86_64-pc-windows-msvc",
                [f"pptd-{version}-x86_64-windows.zip", "pptd-x86_64-windows.zip"],
            )

    return None


def find_pptd() -> Optional[Path]:
    """Find existing pptd executable in PATH or standard user directories."""
    for bin_name in ["pptd", "open-pptd", "slideforge"]:
        found = shutil.which(bin_name)
        if found:
            p = Path(found).resolve()
            if p.is_file() and os.access(p, os.X_OK):
                return p

    home = Path.home()
    names = ["pptd", "open-pptd", "slideforge"]
    candidates = []
    for name in names:
        candidates.extend([
            home / ".local" / "bin" / name,
            home / ".cargo" / "bin" / name,
            Path(f"/usr/local/bin/{name}"),
            Path(f"/opt/homebrew/bin/{name}"),
            Path(__file__).resolve().parent.parent / "bin" / name,
            Path.cwd() / "target" / "release" / name,
            Path.cwd() / "open-pptd-skill" / "target" / "release" / name,
        ])
    if platform.system().lower() == "windows":
        for name in names:
            candidates.extend([
                home / "AppData" / "Local" / "Programs" / "pptd" / f"{name}.exe",
                home / ".cargo" / "bin" / f"{name}.exe",
                home / ".local" / "bin" / f"{name}.exe",
                Path.cwd() / "target" / "release" / f"{name}.exe",
            ])

    for c in candidates:
        if c.is_file() and (platform.system().lower() == "windows" or os.access(c, os.X_OK)):
            return c.resolve()

    return None


find_slideforge = find_pptd


def fetch_checksums(version: str) -> dict[str, str]:
    """Fetch SHA256SUMS.txt from candidate GitHub releases if available."""
    for repo in REPO_CANDIDATES:
        sums_url = f"https://github.com/{repo}/releases/download/v{version}/SHA256SUMS.txt"
        req = urllib.request.Request(
            sums_url,
            headers={"User-Agent": "open-pptd-installer/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                checksums = {}
                for line in text.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        h, name = parts[0], parts[1].lstrip("*")
                        checksums[name] = h
                if checksums:
                    return checksums
        except Exception:
            continue
    return {}


def install_from_release(dest_dir: Path, version: str = VERSION) -> Path:
    target_info = detect_target(version)
    if not target_info:
        raise RuntimeError(
            f"Unsupported operating system or CPU architecture: system='{platform.system()}', machine='{platform.machine()}'.\n"
            f"Please compile pptd from source using: cargo install --git https://github.com/{REPO}.git"
        )

    target, candidate_archives = target_info
    data = None
    last_err = None
    chosen_archive = None

    for repo in REPO_CANDIDATES:
        for archive_name in candidate_archives:
            url = f"https://github.com/{repo}/releases/download/v{version}/{archive_name}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "open-pptd-installer/1.0"},
            )
            try:
                print(f"[open-pptd] Attempting to download prebuilt binary from {repo} ({archive_name})...")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    chosen_archive = archive_name
                    print(f"[open-pptd] Successfully downloaded from {url}")
                    break
            except Exception as err:
                last_err = err
                continue
        if data is not None:
            break

    if data is None or chosen_archive is None:
        raise RuntimeError(
            f"Failed to download prebuilt binary for v{version} from candidate repositories {REPO_CANDIDATES}: {last_err}"
        )

    # SHA256 checksum verification
    expected_sums = fetch_checksums(version)
    if chosen_archive in expected_sums:
        expected_sha = expected_sums[chosen_archive]
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha.lower() != expected_sha.lower():
            raise RuntimeError(
                f"SHA256 checksum mismatch for {chosen_archive}!\n"
                f"  Expected: {expected_sha}\n"
                f"  Actual:   {actual_sha}\n"
                f"The downloaded archive may be corrupted or compromised."
            )
        print(f"[open-pptd] SHA256 checksum verified: {actual_sha[:12]}...")
    else:
        actual_sha = hashlib.sha256(data).hexdigest()
        print(f"[open-pptd] SHA256 (unverified): {actual_sha[:12]}...")

    dest_dir.mkdir(parents=True, exist_ok=True)
    is_win = platform.system().lower() == "windows"
    target_bin_name = "pptd.exe" if is_win else "pptd"
    dest_path = dest_dir / target_bin_name

    extracted = False
    valid_names = {"pptd", "pptd.exe", "open-pptd", "open-pptd.exe"}
    if chosen_archive.endswith(".tar.gz") or chosen_archive.endswith(".tgz"):
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                fname = Path(member.name).name
                if fname in valid_names:
                    f = tar.extractfile(member)
                    if f:
                        dest_path.write_bytes(f.read())
                        extracted = True
                        break
    elif chosen_archive.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                fname = Path(name).name
                if fname in valid_names:
                    dest_path.write_bytes(z.read(name))
                    extracted = True
                    break

    if not extracted or not dest_path.is_file():
        raise RuntimeError(f"Downloaded archive '{chosen_archive}' did not contain a valid compiler executable.")

    dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Create open-pptd symlink/copy if needed
    open_pptd_bin = dest_dir / ("open-pptd.exe" if is_win else "open-pptd")
    if not open_pptd_bin.exists():
        try:
            open_pptd_bin.symlink_to(dest_path.name)
        except Exception:
            try:
                shutil.copy2(dest_path, open_pptd_bin)
            except Exception:
                pass
    print(f"[open-pptd] Installed pptd to: {dest_path}")
    return dest_path


def install_from_cargo(dest_dir: Path) -> Path:
    print("[open-pptd] Attempting fallback compilation via cargo...", file=sys.stderr)
    cargo_bin = shutil.which("cargo")
    if not cargo_bin:
        raise RuntimeError("`cargo` is not installed on this machine, cannot build from source.")

    dest_dir.mkdir(parents=True, exist_ok=True)
    install_root = dest_dir.parent if dest_dir.name == "bin" else dest_dir
    cmd = ["cargo", "install", "--git", f"https://github.com/{REPO}.git", "--root", str(install_root), "--force"]
    print(f"[open-pptd] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    bin_name = "pptd.exe" if platform.system().lower() == "windows" else "pptd"
    installed = (install_root / "bin" / bin_name) if dest_dir.name == "bin" else (dest_dir / bin_name)
    if not installed.is_file():
        # Fallback check
        installed = (install_root / "bin" / "open-pptd") if dest_dir.name == "bin" else (dest_dir / "open-pptd")

    if not installed.is_file():
        raise RuntimeError(f"Cargo build finished but binary not found at {installed}")

    installed.chmod(installed.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[open-pptd] Successfully built and installed pptd via cargo: {installed}")
    return installed


def print_manual_install_instructions(dest_dir: Path) -> None:
    bin_name = "pptd.exe" if platform.system().lower() == "windows" else "pptd"
    target_path = dest_dir / bin_name
    print("\n" + "=" * 70, file=sys.stderr)
    print("PPTD MANUAL INSTALLATION GUIDE", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("Automatic installation could not be completed. You can install pptd manually:", file=sys.stderr)
    print(f"\n1. Precompiled binary from GitHub Releases:\n   https://github.com/{REPO}/releases", file=sys.stderr)
    print(f"   Download the archive for your OS, extract '{bin_name}', and place it at:\n   {target_path}", file=sys.stderr)
    print(f"\n2. Or compile with Rust / Cargo:\n   cargo install --git https://github.com/{REPO}.git", file=sys.stderr)
    print(f"\n3. Ensure {dest_dir} is in your system PATH:\n   export PATH=\"{dest_dir}:$PATH\"", file=sys.stderr)
    print("=" * 70 + "\n", file=sys.stderr)


def ensure_pptd(force_reinstall: bool = False, install_dir: Optional[Path] = None, version: str = VERSION) -> Path:
    if not force_reinstall:
        existing = find_pptd()
        if existing:
            return existing

    if install_dir is None:
        install_dir = Path.home() / ".local" / "bin"

    errors = []
    # 1. Try download prebuilt release
    try:
        return install_from_release(install_dir, version=version)
    except Exception as e:
        errors.append(f"Release download: {e}")
        print(f"[open-pptd] Precompiled binary download failed: {e}", file=sys.stderr)

    # 2. Try cargo fallback
    try:
        return install_from_cargo(install_dir)
    except Exception as e:
        errors.append(f"Cargo build: {e}")
        print(f"[open-pptd] Cargo build fallback failed: {e}", file=sys.stderr)

    # 3. Print instructions and fail cleanly
    print_manual_install_instructions(install_dir)
    raise RuntimeError(
        "Could not automatically install pptd:\n  - " + "\n  - ".join(errors)
    )


ensure_slideforge = ensure_pptd


def main() -> int:
    parser = argparse.ArgumentParser(description="Install pptd native PPTD compiler binary")
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
        help=f"Specific pptd version to install (default: {VERSION})",
    )
    args = parser.parse_args()

    try:
        bin_path = ensure_pptd(force_reinstall=args.force, install_dir=args.dir, version=args.version)
        proc = subprocess.run([str(bin_path), "--version"], capture_output=True, text=True, check=True)
        version_str = proc.stdout.strip()
        print(f"[open-pptd] Success! {version_str} is ready at: {bin_path}")

        path_env = os.environ.get("PATH", "")
        path_dirs = [Path(p).resolve() for p in path_env.split(os.pathsep) if p.strip()]
        bin_dir = bin_path.parent.resolve()
        if bin_dir not in path_dirs:
            print("\n" + "!" * 68)
            print(f"[open-pptd] NOTICE: '{bin_dir}' is not in your current PATH environment.")
            print(f"[open-pptd] To invoke 'pptd' directly from anywhere, run:")
            print(f"    export PATH=\"{bin_dir}:$PATH\"")
            print(f"[open-pptd] Or add that line to your ~/.bashrc / ~/.zshrc.")
            print(f"[open-pptd] You can also invoke the compiler using its full path:")
            print(f"    {bin_path} --help")
            print("!" * 68 + "\n")
        return 0
    except Exception as err:
        print(f"[open-pptd] Installation error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
