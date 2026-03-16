# Python1

Kitty Chase is a Pygame desktop game.

## Run From Source

1. Install dependencies:
```
pip install -r requirements.txt
```
1. Run the game:
```
python chase_game.py
```

## Build Windows App (PyInstaller)

1. Install build dependencies:
```
pip install -r requirements.txt
```
1. Build:
```
pyinstaller chase_game.spec
```
1. Launch the app:
```
dist\\chase_game\\chase_game.exe
```

Saved data is stored in `%LOCALAPPDATA%\\KittyChase` when running the packaged app.

## Build Installer (Inno Setup)

1. Install Inno Setup.
1. Build the app first:
```
pyinstaller chase_game.spec
```
1. Create the installer:
```
iscc installer.iss
```

The installer will be created at `dist\\installer\\KittyChase-Setup.exe`.

## Build macOS App + DMG (macOS)

This must be run on macOS (or via GitHub Actions).

1. Install build dependencies:
```
pip install -r requirements.txt
```
1. Build the app + DMG (Apple Silicon default):
```
bash tools/build_macos.sh
```

The app will be created at `dist/KittyChase.app` and the installer at `dist/installer/KittyChase-macOS.dmg`.

To build an Intel macOS installer, set the DMG name:
```
MAC_DMG_NAME=KittyChase-macOS-intel.dmg bash tools/build_macos.sh
```

## Auto-Update (GitHub Releases)

The app checks GitHub Releases and can download/run the latest installer.

1. Set these constants in `chase_game.py`:
```
APP_VERSION = "1.0.0"
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"
GITHUB_REPO = "YOUR_REPO_NAME"
WINDOWS_INSTALLER_ASSET_NAME = "KittyChase-Setup.exe"
MAC_APPLE_SILICON_INSTALLER_ASSET_NAME = "KittyChase-macOS.dmg"
MAC_INTEL_INSTALLER_ASSET_NAME = "KittyChase-macOS-intel.dmg"
```
1. Keep `AppVersion` in `installer.iss` in sync with `APP_VERSION`.
1. Build the installers (run on the matching OS):
```
# Windows
pyinstaller chase_game.spec
iscc installer.iss

# macOS
bash tools/build_macos.sh
```
1. Create a GitHub Release with tag `v1.0.0` (matching `APP_VERSION`).
1. Upload the installers to that release:
```
dist\\installer\\KittyChase-Setup.exe
dist/installer/KittyChase-macOS.dmg
dist/installer/KittyChase-macOS-intel.dmg
```

On next launch, the packaged app will prompt to download and run the newer installer.

## GitHub Actions Release Workflow

This repo includes a workflow that builds the Windows EXE + installer and the macOS DMG, then attaches them to a GitHub Release whenever you push a tag like `v1.0.1`.

Release steps:
1. Update `APP_VERSION` in `chase_game.py` and `AppVersion` in `installer.iss`.
1. Commit your changes.
1. Create a tag (example):
```
git tag v1.0.1
git push origin v1.0.1
```

The workflow will create the release and upload `KittyChase-Setup.exe`, `KittyChase-macOS.dmg`, and `KittyChase-macOS-intel.dmg`.

## GitHub Actions CI Build

Every push to `main` or `master` runs Windows and macOS builds to catch build issues early.

## Automatic Version Bump

Every push to `main` or `master` bumps the patch version in `chase_game.py` and `installer.iss` and commits the change back to the repo.

Recommended release flow:
1. Push your code changes.
1. Wait for the "Bump Version" workflow to finish.
1. Tag the new version (example):
```
git tag v1.0.2
git push origin v1.0.2
```

## Project Structure
- chase_game.py: Game entry point
- chase_game.spec: PyInstaller build recipe
- installer.iss: Inno Setup installer script
- requirements.txt: Dependencies
- tools/build_macos.sh: macOS build + DMG packaging script
