# Python1

Kitty Chase is now organized as a cross-platform game program with a shared Python rules engine and multiple client targets.

## Platform Support Matrix

Status terms:
- `Production`: packaged delivery path is implemented in this repo.
- `Production target`: contract and build wave are defined; client implementation is staged.
- `Companion target`: non-primary gameplay companion app target.
- `Source porting kit`: source-first bring-up with smoke tooling and compatibility matrix.
- `Archival feasibility`: documented legacy target with emulator/toolchain research track.

| Operating system | Status | Notes |
|---|---|---|
| Windows | Production | Desktop client + installer + updater |
| Ubuntu / Fedora / Debian / CentOS | Production | Linux AppImage pipeline + updater |
| BOSS Linux | Production | Uses Linux AppImage pipeline |
| macOS | Production | Apple Silicon + Intel DMG pipelines |
| Android | Production target | Kivy mobile client contract in `clients/kivy_mobile` |
| iOS | Production target | Kivy iOS contract path in `clients/kivy_mobile` |
| iPadOS | Production target | Kivy iPadOS contract path in `clients/kivy_mobile` |
| tvOS | Production target | Native tvOS contract path in `clients/tvos_native` |
| watchOS | Companion target | Companion app contract in `clients/watchos_companion` |
| FreeBSD | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| Solaris | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| ReactOS | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| HarmonyOS | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| Fuchsia | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| QNX | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| AIX (IBM) | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| HP-UX (Hewlett Packard) | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| OpenVMS | Source porting kit | See `porting_kits` + `tools/legacy_smoke.py` |
| IRIX (SGI) | Archival feasibility | Wave 4 archival/emulator track |

Full capability metadata is tracked in `platform_capabilities.json`.

## Shared Engine API

Cross-platform rules now live under `engine/`:
- `engine/state.py`: `GameState`, `InputFrame`, `EngineTickResult`, account/progress types
- `engine/step.py`: deterministic `step(state, input_frame, dt_ms)`
- `engine/serialize.py`: schema versioning + migration helpers
- `engine/adapters.py`: `RenderAdapter`, `InputAdapter`, `StorageAdapter`, `UpdateAdapter`

Desktop gameplay in `chase_game.py` now executes rules through `engine.step.step(...)`.

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

This must be run on macOS Apple Silicon (or via GitHub Actions).

1. Install build dependencies:
```
pip install -r requirements.txt
```
1. Build the app + DMG (Apple Silicon default):
```
bash tools/build_macos.sh
```

The app will be created at `dist/KittyChase.app` and the installer at `dist/installer/KittyChase-macOS.dmg`.

## Build Linux App + AppImage (Linux)

This must be run on Linux (e.g., Ubuntu/Debian, which is supported on Chrome OS via Crostini).

1. Install build dependencies:
```
pip install -r requirements.txt
```
1. Build the app + AppImage:
```
bash tools/build_linux.sh
```

The app will be created at `dist/KittyChase` and the installer at `dist/installer/KittyChase-linux.AppImage`.

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
LINUX_INSTALLER_ASSET_NAME = "KittyChase-linux.AppImage"
```
1. Keep `AppVersion` in `installer.iss` in sync with `APP_VERSION`.
1. Build the installers (run on the matching OS):
```
# Windows
pyinstaller chase_game.spec
iscc installer.iss

# macOS
bash tools/build_macos.sh

# Linux
bash tools/build_linux.sh
```
1. Create a GitHub Release with tag `v1.0.0` (matching `APP_VERSION`).
1. Upload the installers to that release:
```
dist\\installer\\KittyChase-Setup.exe
dist/installer/KittyChase-macOS.dmg
dist/installer/KittyChase-macOS-intel.dmg
dist/installer/KittyChase-linux.AppImage
```

On next launch, the packaged app will prompt to update. On Linux, the update downloads and launches the AppImage.

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

The workflow will create the release and upload `KittyChase-Setup.exe`, `KittyChase-macOS.dmg`, `KittyChase-macOS-intel.dmg`, and `KittyChase-linux.AppImage`.

## GitHub Actions CI Build

Every push to `main` or `master` runs Windows, macOS, and Linux builds to catch build issues early.

## Universal Wave Validation

`.github/workflows/universal-wave-validation.yml` enforces:
- deterministic engine and schema tests
- platform manifest coverage for every requested OS
- source-porting smoke validation (`tools/legacy_smoke.py`)

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
- engine/: shared deterministic rules engine + schemas + adapters
- clients/: per-platform client contracts (desktop/mobile/tvOS/watchOS)
- platform_capabilities.json: OS capability manifest for all waves
- porting_kits/: source-first compatibility kits for legacy/rare OS targets
- tests/: engine determinism, serialization, and manifest coverage tests
- chase_game.spec: PyInstaller build recipe
- installer.iss: Inno Setup installer script
- requirements.txt: Dependencies
- tools/build_macos.sh: macOS build + DMG packaging script
- tools/build_linux.sh: Linux build + AppImage packaging script
- tools/legacy_smoke.py: headless engine smoke for porting-kit targets
