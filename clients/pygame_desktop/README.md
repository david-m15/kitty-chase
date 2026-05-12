# `clients/pygame_desktop`

Desktop rendering and input client that consumes the shared `engine` package.

## Contract
- Reads `GameState` and draws circles/sprites/UI overlays.
- Converts keyboard/mouse/touch events into `InputFrame`.
- Delegates save/load and updater actions to storage/update adapters.

## Current status
- Implemented by the existing `chase_game.py` runtime.
- Uses `engine.step.step(...)` for deterministic rules execution.

