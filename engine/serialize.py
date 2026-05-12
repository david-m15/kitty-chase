from dataclasses import asdict

from .state import AccountState, GameState, LevelProgress

GAME_STATE_SCHEMA_VERSION = 1
ACCOUNT_SCHEMA_VERSION = 1


def _to_int(value, fallback=0):
    try:
        return int(value)
    except Exception:
        return fallback


def game_state_to_dict(state: GameState) -> dict:
    payload = asdict(state)
    payload["schema_version"] = GAME_STATE_SCHEMA_VERSION
    return payload


def game_state_from_dict(payload: dict) -> GameState:
    return GameState(
        schema_version=_to_int(
            payload.get("schema_version"), GAME_STATE_SCHEMA_VERSION
        ),
        tick=_to_int(payload.get("tick"), 0),
        width=_to_int(payload.get("width"), 800),
        height=_to_int(payload.get("height"), 600),
        level=_to_int(payload.get("level"), 1),
        player_radius=_to_int(payload.get("player_radius"), 20),
        red_radius=_to_int(payload.get("red_radius"), 20),
        blue_radius=_to_int(payload.get("blue_radius"), 10),
        base_player_speed=_to_int(payload.get("base_player_speed"), 5),
        base_red_speed=_to_int(payload.get("base_red_speed"), 2),
        player_speed=_to_int(payload.get("player_speed"), 5),
        current_red_speed=_to_int(payload.get("current_red_speed"), 2),
        num_blue=_to_int(payload.get("num_blue"), 0),
        collected=_to_int(payload.get("collected"), 0),
        player_pos=tuple(payload.get("player_pos", [400, 300])),
        red_balls=[tuple(ball) for ball in payload.get("red_balls", [])],
        blue_balls=[tuple(ball) for ball in payload.get("blue_balls", [])],
        freeze_pos=tuple(payload["freeze_pos"]) if payload.get("freeze_pos") else None,
        speedup_pos=tuple(payload["speedup_pos"]) if payload.get("speedup_pos") else None,
        slowdown_pos=tuple(payload["slowdown_pos"])
        if payload.get("slowdown_pos")
        else None,
        freeze_active=bool(payload.get("freeze_active", False)),
        speedup_active=bool(payload.get("speedup_active", False)),
        slowdown_active=bool(payload.get("slowdown_active", False)),
        freeze_timer_ms=_to_int(payload.get("freeze_timer_ms"), 0),
        speedup_timer_ms=_to_int(payload.get("speedup_timer_ms"), 0),
        slowdown_timer_ms=_to_int(payload.get("slowdown_timer_ms"), 0),
        win=bool(payload.get("win", False)),
        lose=bool(payload.get("lose", False)),
    )


def migrate_accounts_payload(payload: dict) -> dict[str, dict]:
    if not isinstance(payload, dict):
        return {}
    migrated: dict[str, dict] = {}
    for name, value in payload.items():
        if isinstance(value, int):
            account = AccountState(
                level_progress=LevelProgress(highest_unlocked_level=max(1, value))
            )
        elif isinstance(value, dict):
            level = _to_int(value.get("level"), 1)
            account = AccountState(
                level_progress=LevelProgress(highest_unlocked_level=max(1, level)),
                password=value.get("password"),
                is_admin=bool(value.get("is_admin", False)),
            )
        else:
            account = AccountState()
        migrated[name] = {
            "level": account.level_progress.highest_unlocked_level,
            "password": account.password,
            "is_admin": account.is_admin,
            "schema_version": ACCOUNT_SCHEMA_VERSION,
        }
    return migrated

