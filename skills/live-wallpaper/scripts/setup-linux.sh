#!/usr/bin/env bash
set -euo pipefail

SHARE_DIR="${HOME}/.local/share/live-wallpaper"
BIN_DIR="${SHARE_DIR}/bin"
LIB_DIR="${SHARE_DIR}/lib"

mkdir -p "${BIN_DIR}" "${LIB_DIR}"

if command -v mpv >/dev/null 2>&1; then
    echo "==> System mpv detected: $(command -v mpv)"
    exit 0
fi

if [[ -x "${BIN_DIR}/mpv" ]]; then
    if LD_LIBRARY_PATH="${LIB_DIR}:${LD_LIBRARY_PATH:-}" "${BIN_DIR}/mpv" --version >/dev/null 2>&1; then
        echo "==> Standalone mpv is already verified in ${BIN_DIR}/mpv"
        exit 0
    fi
fi

echo "==> Setting up standalone mpv runtime for Linux live wallpaper..."
TMP_DIR=$(mktemp -d /tmp/live-wallpaper-mpv-XXXXXX)
trap 'rm -rf "${TMP_DIR}"' EXIT

cd "${TMP_DIR}"
echo "==> Fetching required packages..."
apt-get download mpv libmujs3 liblua5.2-0 libsndio7.0 libsixel1 libva-wayland2 >/dev/null 2>&1 || true

for deb in *.deb; do
    if [[ -f "${deb}" ]]; then
        dpkg -x "${deb}" .
    fi
done

if [[ -f "./usr/bin/mpv" ]]; then
    cp ./usr/bin/mpv "${BIN_DIR}/"
    chmod +x "${BIN_DIR}/mpv"
fi

if [[ -d "./usr/lib/x86_64-linux-gnu" ]]; then
    cp -d ./usr/lib/x86_64-linux-gnu/*.so* "${LIB_DIR}/" 2>/dev/null || true
fi

if LD_LIBRARY_PATH="${LIB_DIR}:${LD_LIBRARY_PATH:-}" "${BIN_DIR}/mpv" --version >/dev/null 2>&1; then
    echo "==> Successfully installed standalone mpv runtime to ${SHARE_DIR}"
else
    echo "==> Note: Please ensure mpv is installed via 'sudo apt install mpv' or package manager."
fi
