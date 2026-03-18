#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip install --upgrade pip
pip install -r requirements.txt

ICON_SRC="tiger.png"

pyinstaller --windowed --name "KittyChase" --icon "$ICON_SRC" --add-data "tiger.png:." chase_game.py

mkdir -p dist/installer
TAR_NAME="${LINUX_TAR_NAME:-KittyChase-linux.tar.gz}"
TAR_PATH="dist/installer/$TAR_NAME"
APP_DIR="dist/KittyChase"
if [ ! -d "$APP_DIR" ]; then
  echo "Could not find KittyChase directory in dist/. Build may have failed."
  exit 1
fi
tar -czf "$TAR_PATH" -C dist KittyChase