#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip install --upgrade pip
pip install -r requirements.txt

ICON_SRC="tiger.png"
ICONSET_DIR="build/tiger.iconset"
ICNS_OUT="build/tiger.icns"

if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  rm -rf "$ICONSET_DIR"
  mkdir -p "$ICONSET_DIR"
  sips -z 16 16 "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
  sips -z 32 32 "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
  sips -z 64 64 "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
  sips -z 256 256 "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
  sips -z 512 512 "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$ICONSET_DIR" -o "$ICNS_OUT"
fi

ICON_ARGS=()
if [ -f "$ICNS_OUT" ]; then
  ICON_ARGS=(--icon "$ICNS_OUT")
fi

pyinstaller --windowed --name "KittyChase" "${ICON_ARGS[@]}" --add-data "tiger.png:." chase_game.py

mkdir -p dist/installer
APP_PATH="dist/KittyChase.app"
if [ ! -d "$APP_PATH" ]; then
  APP_PATH="dist/KittyChase/KittyChase.app"
fi
if [ ! -d "$APP_PATH" ]; then
  echo "Could not find KittyChase.app in dist/. Build may have failed."
  exit 1
fi
hdiutil create -volname "Kitty Chase" -srcfolder "$APP_PATH" -ov -format UDZO "dist/installer/KittyChase-macOS.dmg"
