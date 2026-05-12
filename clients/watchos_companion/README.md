# `clients/watchos_companion`

Companion app contract for watchOS.

## Scope
- Read-only progress, streak, and active-session status.
- Optional quick remote actions for menu/start controls.
- Does not host the primary gameplay renderer.

## Data contract
- Reads synced account and progress payload from engine schema.
- Emits limited remote commands mapped to app-level actions.

## Build output naming
- `kittychase-watchos-{arch}-{version}.ipa`

