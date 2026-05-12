#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip install --upgrade pip
pip install -r requirements.txt

ICON_SRC="tiger.png"

pyinstaller --windowed --name "KittyChase" --icon "$ICON_SRC" --add-data "tiger.png:." chase_game.py

mkdir -p dist/installer
APPIMAGE_NAME="${LINUX_APPIMAGE_NAME:-KittyChase-linux.AppImage}"
APPIMAGE_PATH="dist/installer/$APPIMAGE_NAME"

PYI_DIR="dist/KittyChase"
if [ ! -d "$PYI_DIR" ]; then
  echo "Could not find KittyChase directory in dist/. Build may have failed."
  exit 1
fi

APPDIR_ROOT="build/KittyChase.AppDir"
rm -rf "$APPDIR_ROOT"
mkdir -p "$APPDIR_ROOT/usr/bin"

# Minimal AppDir contents (root desktop entry, icon, AppRun)
cat > "$APPDIR_ROOT/KittyChase.desktop" <<'EOF'
[Desktop Entry]
Name=Kitty Chase
Exec=KittyChase
Icon=KittyChase
Type=Application
Categories=Game;
Terminal=false
EOF

cp -f "$ICON_SRC" "$APPDIR_ROOT/KittyChase.png"

cat > "$APPDIR_ROOT/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="${APPDIR:-$(dirname "$(readlink -f "$0")")}"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/KittyChase" "$@"
EOF
chmod +x "$APPDIR_ROOT/AppRun"

# Copy the PyInstaller onedir bundle into AppDir's usr/bin
cp -a "$PYI_DIR/." "$APPDIR_ROOT/usr/bin/"

# Download and run appimagetool (x86_64) to build the AppImage
APPIMAGETOOL="build/appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
  echo "Downloading appimagetool..."
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$APPIMAGETOOL" "$APPIMAGETOOL_URL"
  else
    echo "Neither curl nor wget is available to download appimagetool."
    exit 1
  fi
fi
chmod +x "$APPIMAGETOOL"

export ARCH=x86_64
export APPIMAGE_EXTRACT_AND_RUN=1
"$APPIMAGETOOL" "$APPDIR_ROOT" "$APPIMAGE_PATH"

echo "Built AppImage: $APPIMAGE_PATH"
