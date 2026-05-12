# Kitty Chase — Playtest Notes

## Environment
- Date:
- OS:
- Run mode: Source (`python chase_game.py`) / Packaged (PyInstaller EXE/App)
- Python version:
- Pygame version:
- Commit (git SHA):

## Fresh-start reset (source runs)
Source runs store data in this repo directory. For a clean playtest run, rename or delete:
- `accounts.json`
- `unlocked_levels.json`

## Scenarios (mark PASS/FAIL)
- [ ] Admin first-run (no admin exists) — create admin + password
- [ ] Guest flow — play Level 1, verify no progress saved
- [ ] Create account — create non-admin user and log in
- [ ] Sign out — return to account selection
- [ ] Level select pagination — navigate pages, jump to farthest
- [ ] Play Level 1 — win and return to level select
- [ ] Play Level 5 — verify difficulty scaling feels right
- [ ] Play Level 20 — verify performance and difficulty
- [ ] Win/Lose screens — restart behavior, settings access
- [ ] Save progress — “Save My Progress” flow works (non-admin)
- [ ] Delete account — remove user and confirm they’re gone

## Issues
| Priority (P0/P1/P2) | Title | Repro steps | Expected | Actual | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

