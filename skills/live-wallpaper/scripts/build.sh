#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL_DIR="${HOME}/.local/bin"
BIN_NAME="live-wallpaper"
OS="$(uname -s)"

mkdir -p "${INSTALL_DIR}"

if [[ "${OS}" == "Darwin" ]]; then
    echo "==> Compiling native modular Swift live wallpaper engine for macOS..."
    SRC_DIR="${ROOT_DIR}/src/macos"
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
        -o "${INSTALL_DIR}/${BIN_NAME}-macos"

    chmod +x "${INSTALL_DIR}/${BIN_NAME}-macos"
    echo "==> macOS native engine built at ${INSTALL_DIR}/${BIN_NAME}-macos"
elif [[ "${OS}" == "Linux" ]]; then
    echo "==> Setting up Linux live wallpaper engine dependencies..."
    "${SCRIPT_DIR}/setup-linux.sh"
fi

# Install cross-platform launcher into ~/.local/bin
cp "${ROOT_DIR}/bin/live-wallpaper" "${INSTALL_DIR}/${BIN_NAME}"
chmod +x "${INSTALL_DIR}/${BIN_NAME}"

echo "==> Successfully installed ${BIN_NAME} to ${INSTALL_DIR}/${BIN_NAME}"
echo "Run 'live-wallpaper --help' or 'live-wallpaper status' to get started."
