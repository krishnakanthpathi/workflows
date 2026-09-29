#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_FILE="${ROOT_DIR}/src/main.swift"
INSTALL_DIR="${HOME}/.local/bin"
BIN_NAME="live-wallpaper"

echo "==> Compiling native Swift live wallpaper engine..."
mkdir -p "${INSTALL_DIR}"
swiftc -O "${SRC_FILE}" -o "${INSTALL_DIR}/${BIN_NAME}"
chmod +x "${INSTALL_DIR}/${BIN_NAME}"

echo "==> Successfully installed to ${INSTALL_DIR}/${BIN_NAME}"
echo "Run 'live-wallpaper --help' or 'live-wallpaper status' to get started."
