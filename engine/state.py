from dataclasses import dataclass, field

Vector2 = tuple[int, int]


@dataclass
class LevelProgress:
    highest_unlocked_level: int = 1


@dataclass
class AccountState:
    level_progress: LevelProgress = field(default_factory=LevelProgress)
    password: str | None = None
    is_admin: bool = False


@dataclass
class InputFrame:
    direction_x: int = 0
    direction_y: int = 0
    touch_target: Vector2 | None = None
    action: str | None = None
    timestamp_ms: int = 0


@dataclass
class UiHints:
    freeze_seconds_left: int = 0
    speedup_seconds_left: int = 0
    slowdown_seconds_left: int = 0


@dataclass
class GameState:
    schema_version: int = 1
    tick: int = 0
    width: int = 800
    height: int = 600
    level: int = 1
    player_radius: int = 20
    red_radius: int = 20
    blue_radius: int = 10
    base_player_speed: int = 5
    base_red_speed: int = 2
    player_speed: int = 5
    current_red_speed: int = 2
    num_blue: int = 0
    collected: int = 0
    player_pos: Vector2 = (400, 300)
    red_balls: list[Vector2] = field(default_factory=list)
    blue_balls: list[Vector2] = field(default_factory=list)
    freeze_pos: Vector2 | None = None
    speedup_pos: Vector2 | None = None
    slowdown_pos: Vector2 | None = None
    freeze_active: bool = False
    speedup_active: bool = False
    slowdown_active: bool = False
    freeze_timer_ms: int = 0
    speedup_timer_ms: int = 0
    slowdown_timer_ms: int = 0
    win: bool = False
    lose: bool = False


@dataclass
class EngineTickResult:
    state: GameState
    events: list[str] = field(default_factory=list)
    ui_hints: UiHints = field(default_factory=UiHints)

