#!/usr/bin/env bash
set -euo pipefail

# slideforge standalone installer for open-pptd-skill
REPO="shiquda/slideforge"
VERSION="1.0.3"
INSTALL_DIR="${HOME}/.local/bin"

mkdir -p "${INSTALL_DIR}"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m | tr '[:upper:]' '[:lower:]')"

case "${OS}" in
  darwin)
    case "${ARCH}" in
      arm64|aarch64) ARCHIVE="slideforge-${VERSION}-aarch64-macos.tar.gz" ;;
      x86_64|amd64)   ARCHIVE="slideforge-${VERSION}-x86_64-macos.tar.gz" ;;
      *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  linux)
    case "${ARCH}" in
      x86_64|amd64)   ARCHIVE="slideforge-${VERSION}-x86_64-linux.tar.gz" ;;
      arm64|aarch64) ARCHIVE="slideforge-${VERSION}-aarch64-linux.tar.gz" ;;
      *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "Unsupported OS: ${OS}. Please build with cargo install --git https://github.com/${REPO}.git" >&2
    exit 1
    ;;
esac

URL="https://github.com/${REPO}/releases/download/v${VERSION}/${ARCHIVE}"
echo "[open-pptd-skill] Downloading slideforge from ${URL}..."

TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

curl -fsSL "${URL}" -o "${TMPDIR}/${ARCHIVE}"
tar -xzf "${TMPDIR}/${ARCHIVE}" -C "${TMPDIR}"
cp "${TMPDIR}/slideforge" "${INSTALL_DIR}/slideforge"
chmod +x "${INSTALL_DIR}/slideforge"

echo "[open-pptd-skill] Installed slideforge successfully to ${INSTALL_DIR}/slideforge"
"${INSTALL_DIR}/slideforge" --version
