#!/usr/bin/env bash
set -euo pipefail

# pptd standalone installer for open-pptd
REPOS=("shiquda/open-pptd-skill")
REPO="${REPOS[0]}"
VERSION="1.3.5"
INSTALL_DIR="${HOME}/.local/bin"
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --force|-f)
      FORCE=1
      ;;
    --dir=*)
      INSTALL_DIR="${arg#*=}"
      ;;
    --version=*)
      VERSION="${arg#*=}"
      ;;
    --help|-h)
      echo "Usage: $0 [--force] [--dir=/path/to/bin]"
      exit 0
      ;;
  esac
done

# If already installed and not forced, verify version and return
if [ "$FORCE" -eq 0 ] && command -v pptd >/dev/null 2>&1; then
  CURRENT_BIN="$(command -v pptd)"
  echo "[open-pptd] pptd is already installed at: ${CURRENT_BIN}"
  "${CURRENT_BIN}" --version
  exit 0
fi

if [ "$FORCE" -eq 0 ] && [ -x "${INSTALL_DIR}/pptd" ]; then
  echo "[open-pptd] pptd found at: ${INSTALL_DIR}/pptd"
  "${INSTALL_DIR}/pptd" --version
  exit 0
fi

mkdir -p "${INSTALL_DIR}"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m | tr '[:upper:]' '[:lower:]')"

case "${OS}" in
  darwin)
    case "${ARCH}" in
      arm64|aarch64) ARCHIVES=("pptd-${VERSION}-aarch64-macos.tar.gz" "pptd-aarch64-macos.tar.gz") ;;
      x86_64|amd64)   ARCHIVES=("pptd-${VERSION}-x86_64-macos.tar.gz" "pptd-x86_64-macos.tar.gz") ;;
      *) echo "[open-pptd] Unsupported macOS architecture: ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  linux)
    case "${ARCH}" in
      x86_64|amd64)   ARCHIVES=("pptd-${VERSION}-x86_64-linux.tar.gz" "pptd-x86_64-linux.tar.gz") ;;
      arm64|aarch64) ARCHIVES=("pptd-${VERSION}-aarch64-linux.tar.gz" "pptd-aarch64-linux.tar.gz") ;;
      *) echo "[open-pptd] Unsupported Linux architecture: ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "[open-pptd] Unsupported OS: ${OS}. Please build with cargo install --git https://github.com/${REPO}.git" >&2
    exit 1
    ;;
esac

TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

DOWNLOAD_SUCCESS=0
CHOSEN_ARCHIVE=""

for repo_candidate in "${REPOS[@]}"; do
  for archive_candidate in "${ARCHIVES[@]}"; do
    URL="https://github.com/${repo_candidate}/releases/download/v${VERSION}/${archive_candidate}"
    SUMS_URL="https://github.com/${repo_candidate}/releases/download/v${VERSION}/SHA256SUMS.txt"
    echo "[open-pptd] Attempting to download from ${repo_candidate} (${archive_candidate})..."
    if curl -fSL --connect-timeout 15 --max-time 60 "${URL}" -o "${TMPDIR}/${archive_candidate}" 2>/dev/null; then
      DOWNLOAD_SUCCESS=1
      REPO="${repo_candidate}"
      CHOSEN_ARCHIVE="${archive_candidate}"
      echo "[open-pptd] Download complete from ${repo_candidate}. Verifying checksum..."
      
      if curl -fSL --connect-timeout 10 --max-time 30 "${SUMS_URL}" -o "${TMPDIR}/SHA256SUMS.txt" 2>/dev/null; then
        EXPECTED_SHA="$(grep "${archive_candidate}" "${TMPDIR}/SHA256SUMS.txt" | awk '{print $1}' || true)"
        if [ -n "${EXPECTED_SHA}" ]; then
          if command -v sha256sum >/dev/null 2>&1; then
            ACTUAL_SHA="$(sha256sum "${TMPDIR}/${archive_candidate}" | awk '{print $1}')"
          elif command -v shasum >/dev/null 2>&1; then
            ACTUAL_SHA="$(shasum -a 256 "${TMPDIR}/${archive_candidate}" | awk '{print $1}')"
          else
            ACTUAL_SHA=""
          fi

          if [ -n "${ACTUAL_SHA}" ] && [ "${ACTUAL_SHA}" != "${EXPECTED_SHA}" ]; then
            echo "[open-pptd] Checksum verification failed for ${repo_candidate}!" >&2
            DOWNLOAD_SUCCESS=0
            continue
          else
            echo "[open-pptd] Checksum verified: ${EXPECTED_SHA:0:12}..."
          fi
        fi
      fi
      break 2
    fi
  done
done

if [ "$DOWNLOAD_SUCCESS" -eq 1 ]; then
  tar -xzf "${TMPDIR}/${CHOSEN_ARCHIVE}" -C "${TMPDIR}"
  BIN_FOUND=""
  for b in "pptd" "open-pptd"; do
    if [ -f "${TMPDIR}/${b}" ]; then
      BIN_FOUND="${TMPDIR}/${b}"
      break
    fi
  done

  if [ -n "${BIN_FOUND}" ]; then
    cp "${BIN_FOUND}" "${INSTALL_DIR}/pptd"
    chmod +x "${INSTALL_DIR}/pptd"
    # Also create slideforge alias if not already present
    if [ ! -e "${INSTALL_DIR}/slideforge" ]; then
      ln -sf "pptd" "${INSTALL_DIR}/slideforge" 2>/dev/null || cp "${INSTALL_DIR}/pptd" "${INSTALL_DIR}/slideforge"
    fi
    echo "[open-pptd] Successfully installed pptd to ${INSTALL_DIR}/pptd"
    "${INSTALL_DIR}/pptd" --version
    if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
      echo ""
      echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      echo "[open-pptd] NOTICE: ${INSTALL_DIR} is not in your current PATH."
      echo "[open-pptd] To invoke 'pptd' directly, run:"
      echo "    export PATH=\"${INSTALL_DIR}:\$PATH\""
      echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      echo ""
    fi
    exit 0
  fi
fi

# Fallback: compile via cargo
echo "[open-pptd] Falling back to building pptd via cargo..." >&2
if command -v cargo >/dev/null 2>&1; then
  if cargo install --git "https://github.com/${REPO}.git" --root "${INSTALL_DIR}/.." --force; then
    echo "[open-pptd] Cargo build succeeded!"
    "${INSTALL_DIR}/pptd" --version
    exit 0
  fi
fi

# Fallback guide
echo "======================================================================" >&2
echo "PPTD MANUAL INSTALLATION REQUIRED" >&2
echo "======================================================================" >&2
echo "Automatic download and cargo fallback could not complete." >&2
echo "Options to install pptd:" >&2
echo "1. Prebuilt releases: https://github.com/${REPO}/releases" >&2
echo "   Download the archive for ${OS}-${ARCH}, extract 'pptd' into ${INSTALL_DIR}/" >&2
echo "2. Build with Rust: cargo install --git https://github.com/${REPO}.git" >&2
echo "3. Add ${INSTALL_DIR} to your PATH: export PATH=\"${INSTALL_DIR}:\$PATH\"" >&2
echo "======================================================================" >&2
exit 1
