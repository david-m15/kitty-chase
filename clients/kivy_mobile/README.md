# `clients/kivy_mobile`

Shared mobile client contract for Android, iOS, and iPadOS.

## Contract
- Input: touch gestures and controller events mapped to `InputFrame`.
- Render: Kivy widgets/canvas bound to `GameState`.
- Storage: platform app-private paths.
- Updater: disabled in-app; use store delivery flow.

## Toolchain targets
- Android: `python-for-android`
- iOS/iPadOS: `kivy-ios`

## Build output naming
- `kittychase-android-{arch}-{version}.apk`
- `kittychase-ios-{arch}-{version}.ipa`
- `kittychase-ipados-{arch}-{version}.ipa`

