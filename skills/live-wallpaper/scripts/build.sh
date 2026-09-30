#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${ROOT_DIR}/src"
INSTALL_DIR="${HOME}/.local/bin"
BIN_NAME="live-wallpaper"

echo "==> Compiling native modular Swift live wallpaper engine..."
mkdir -p "${INSTALL_DIR}"

swiftc -O \
    "${SRC_DIR}/Models.swift" \
    "${SRC_DIR}/SkyLight.swift" \
    "${SRC_DIR}/MediaResolver.swift" \
    "${SRC_DIR}/Renderers.swift" \
    "${SRC_DIR}/Screensaver.swift" \
    "${SRC_DIR}/IPC.swift" \
    "${SRC_DIR}/Service.swift" \
    "${SRC_DIR}/WallpaperApp.swift" \
    "${SRC_DIR}/main.swift" \
    -o "${INSTALL_DIR}/${BIN_NAME}"

chmod +x "${INSTALL_DIR}/${BIN_NAME}"

echo "==> Successfully installed modular engine to ${INSTALL_DIR}/${BIN_NAME}"
echo "Run 'live-wallpaper --help' or 'live-wallpaper status' to get started."
