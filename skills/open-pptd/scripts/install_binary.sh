#!/usr/bin/env bash
set -euo pipefail

# slideforge standalone installer for open-pptd-skill
REPOS=("shiquda/open-pptd" "shiquda/open-pptd-skill" "shiquda/slideforge")
REPO="${REPOS[0]}"
VERSION="1.0.4"
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
    --help|-h)
      echo "Usage: $0 [--force] [--dir=/path/to/bin]"
      exit 0
      ;;
  esac
done

# If already installed and not forced, verify version and return
if [ "$FORCE" -eq 0 ] && command -v slideforge >/dev/null 2>&1; then
  CURRENT_BIN="$(command -v slideforge)"
  echo "[open-pptd-skill] slideforge is already installed at: ${CURRENT_BIN}"
  "${CURRENT_BIN}" --version
  exit 0
fi

if [ "$FORCE" -eq 0 ] && [ -x "${INSTALL_DIR}/slideforge" ]; then
  echo "[open-pptd-skill] slideforge found at: ${INSTALL_DIR}/slideforge"
  "${INSTALL_DIR}/slideforge" --version
  exit 0
fi

mkdir -p "${INSTALL_DIR}"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m | tr '[:upper:]' '[:lower:]')"

case "${OS}" in
  darwin)
    case "${ARCH}" in
      arm64|aarch64) ARCHIVE="slideforge-${VERSION}-aarch64-macos.tar.gz" ;;
      x86_64|amd64)   ARCHIVE="slideforge-${VERSION}-x86_64-macos.tar.gz" ;;
      *) echo "[open-pptd-skill] Unsupported macOS architecture: ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  linux)
    case "${ARCH}" in
      x86_64|amd64)   ARCHIVE="slideforge-${VERSION}-x86_64-linux.tar.gz" ;;
      arm64|aarch64) ARCHIVE="slideforge-${VERSION}-aarch64-linux.tar.gz" ;;
      *) echo "[open-pptd-skill] Unsupported Linux architecture: ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "[open-pptd-skill] Unsupported OS: ${OS}. Please build with cargo install --git https://github.com/${REPO}.git" >&2
    exit 1
    ;;
esac

TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

DOWNLOAD_SUCCESS=0
for repo_candidate in "${REPOS[@]}"; do
  URL="https://github.com/${repo_candidate}/releases/download/v${VERSION}/${ARCHIVE}"
  SUMS_URL="https://github.com/${repo_candidate}/releases/download/v${VERSION}/SHA256SUMS.txt"
  echo "[open-pptd-skill] Attempting to download from ${repo_candidate}..."
  if curl -fSL --connect-timeout 15 --max-time 60 "${URL}" -o "${TMPDIR}/${ARCHIVE}" 2>/dev/null; then
    DOWNLOAD_SUCCESS=1
    REPO="${repo_candidate}"
    echo "[open-pptd-skill] Download complete from ${repo_candidate}. Verifying checksum..."
    
    if curl -fSL --connect-timeout 10 --max-time 30 "${SUMS_URL}" -o "${TMPDIR}/SHA256SUMS.txt" 2>/dev/null; then
      EXPECTED_SHA="$(grep "${ARCHIVE}" "${TMPDIR}/SHA256SUMS.txt" | awk '{print $1}' || true)"
      if [ -n "${EXPECTED_SHA}" ]; then
        if command -v sha256sum >/dev/null 2>&1; then
          ACTUAL_SHA="$(sha256sum "${TMPDIR}/${ARCHIVE}" | awk '{print $1}')"
        elif command -v shasum >/dev/null 2>&1; then
          ACTUAL_SHA="$(shasum -a 256 "${TMPDIR}/${ARCHIVE}" | awk '{print $1}')"
        else
          ACTUAL_SHA=""
        fi

        if [ -n "${ACTUAL_SHA}" ] && [ "${ACTUAL_SHA}" != "${EXPECTED_SHA}" ]; then
          echo "[open-pptd-skill] Checksum verification failed for ${repo_candidate}!" >&2
          DOWNLOAD_SUCCESS=0
          continue
        else
          echo "[open-pptd-skill] Checksum verified: ${EXPECTED_SHA:0:12}..."
        fi
      fi
    fi
    break
  fi
done
if [ "$DOWNLOAD_SUCCESS" -eq 1 ]; then
  tar -xzf "${TMPDIR}/${ARCHIVE}" -C "${TMPDIR}"
  if [ -f "${TMPDIR}/slideforge" ]; then
    cp "${TMPDIR}/slideforge" "${INSTALL_DIR}/slideforge"
    chmod +x "${INSTALL_DIR}/slideforge"
    echo "[open-pptd-skill] Successfully installed slideforge to ${INSTALL_DIR}/slideforge"
    "${INSTALL_DIR}/slideforge" --version
    exit 0
  fi
fi

# Fallback: compile via cargo
echo "[open-pptd-skill] Falling back to building slideforge via cargo..." >&2
if command -v cargo >/dev/null 2>&1; then
  if cargo install --git "https://github.com/${REPO}.git" --root "${INSTALL_DIR}/.." --force; then
    echo "[open-pptd-skill] Cargo build succeeded!"
    "${INSTALL_DIR}/slideforge" --version
    exit 0
  fi
fi

# Fallback guide
echo "======================================================================" >&2
echo "SLIDEFORGE MANUAL INSTALLATION REQUIRED" >&2
echo "======================================================================" >&2
echo "Automatic download and cargo fallback could not complete." >&2
echo "Options to install slideforge:" >&2
echo "1. Prebuilt releases: https://github.com/${REPO}/releases" >&2
echo "   Download the archive for ${OS}-${ARCH}, extract 'slideforge' into ${INSTALL_DIR}/" >&2
echo "2. Build with Rust: cargo install --git https://github.com/${REPO}.git" >&2
echo "3. Add ${INSTALL_DIR} to your PATH: export PATH=\"${INSTALL_DIR}:\$PATH\"" >&2
echo "======================================================================" >&2
exit 1
