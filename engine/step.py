from copy import deepcopy
from math import sqrt

from .state import EngineTickResult, GameState, InputFrame, UiHints


FREEZE_DURATION_MS = 5000
SPEEDUP_DURATION_MS = 5000
SLOWDOWN_DURATION_MS = 5000


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _seconds_left(timer_ms: int) -> int:
    return max(0, int((timer_ms + 999) // 1000))


def _distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _collides(a: tuple[int, int], ar: int, b: tuple[int, int], br: int) -> bool:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 < (ar + br) ** 2


def _deterministic_opposite_edge_spawn(
    state: GameState, player_pos: tuple[int, int], salt: int
) -> tuple[int, int]:
    px, py = player_pos
    dists = [
        (px, "left"),
        (state.width - px, "right"),
        (py, "top"),
        (state.height - py, "bottom"),
    ]
    max_dist = max(value for value, _ in dists)
    candidates = sorted(edge for value, edge in dists if value == max_dist)
    edge = candidates[salt % len(candidates)]
    if edge in {"left", "right"}:
        y_range = max(1, state.height - 2 * state.red_radius)
        y = state.red_radius + ((salt * 97 + state.tick * 31) % (y_range + 1))
        x = state.red_radius if edge == "left" else state.width - state.red_radius
    else:
        x_range = max(1, state.width - 2 * state.red_radius)
        x = state.red_radius + ((salt * 89 + state.tick * 29) % (x_range + 1))
        y = state.red_radius if edge == "top" else state.height - state.red_radius
    return (x, y)


def step(state: GameState, input_frame: InputFrame, dt_ms: int) -> EngineTickResult:
    next_state = deepcopy(state)
    events: list[str] = []

    if next_state.win or next_state.lose:
        return EngineTickResult(
            state=next_state,
            events=[],
            ui_hints=UiHints(
                freeze_seconds_left=_seconds_left(next_state.freeze_timer_ms),
                speedup_seconds_left=_seconds_left(next_state.speedup_timer_ms),
                slowdown_seconds_left=_seconds_left(next_state.slowdown_timer_ms),
            ),
        )

    if next_state.freeze_active:
        next_state.freeze_timer_ms -= dt_ms
        if next_state.freeze_timer_ms <= 0:
            next_state.freeze_active = False
            next_state.freeze_timer_ms = 0
            events.append("freeze_ended")
    if next_state.speedup_active:
        next_state.speedup_timer_ms -= dt_ms
        if next_state.speedup_timer_ms <= 0:
            next_state.speedup_active = False
            next_state.speedup_timer_ms = 0
            next_state.player_speed = next_state.base_player_speed
            events.append("speedup_ended")
    if next_state.slowdown_active:
        next_state.slowdown_timer_ms -= dt_ms
        if next_state.slowdown_timer_ms <= 0:
            next_state.slowdown_active = False
            next_state.slowdown_timer_ms = 0
            next_state.current_red_speed = next_state.base_red_speed
            events.append("slowdown_ended")

    direction_x = _clamp(input_frame.direction_x, -1, 1)
    direction_y = _clamp(input_frame.direction_y, -1, 1)

    new_player_x = next_state.player_pos[0] + direction_x * next_state.player_speed
    new_player_y = next_state.player_pos[1] + direction_y * next_state.player_speed
    player_moving = direction_x != 0 or direction_y != 0

    if input_frame.touch_target is not None and not player_moving:
        dx = input_frame.touch_target[0] - next_state.player_pos[0]
        dy = input_frame.touch_target[1] - next_state.player_pos[1]
        dist = max(1.0, sqrt(dx**2 + dy**2))
        if dist > next_state.player_speed:
            new_player_x += int(round(next_state.player_speed * dx / dist))
            new_player_y += int(round(next_state.player_speed * dy / dist))
            player_moving = True

    new_player_x = _clamp(
        new_player_x, next_state.player_radius, next_state.width - next_state.player_radius
    )
    new_player_y = _clamp(
        new_player_y,
        next_state.player_radius,
        next_state.height - next_state.player_radius,
    )
    next_state.player_pos = (new_player_x, new_player_y)

    if not next_state.freeze_active:
        moved_red: list[tuple[int, int]] = []
        for red_pos in next_state.red_balls:
            dx = next_state.player_pos[0] - red_pos[0]
            dy = next_state.player_pos[1] - red_pos[1]
            dist = max(1.0, sqrt(dx**2 + dy**2))
            move_x = round(next_state.current_red_speed * dx / dist)
            move_y = round(next_state.current_red_speed * dy / dist)
            if move_x == 0 and dx != 0:
                move_x = 1 if dx > 0 else -1
            if move_y == 0 and dy != 0:
                move_y = 1 if dy > 0 else -1
            moved_red.append((red_pos[0] + move_x, red_pos[1] + move_y))
        next_state.red_balls = moved_red

    if player_moving:
        for i in range(len(next_state.red_balls)):
            for j in range(i + 1, len(next_state.red_balls)):
                r1 = next_state.red_balls[i]
                r2 = next_state.red_balls[j]
                if _distance(r1, r2) < 2 * next_state.red_radius:
                    salt1 = (next_state.tick + 1) * 101 + i * 17 + j * 31
                    salt2 = (next_state.tick + 1) * 131 + i * 19 + j * 37
                    next_state.red_balls[i] = _deterministic_opposite_edge_spawn(
                        next_state, next_state.player_pos, salt1
                    )
                    next_state.red_balls[j] = _deterministic_opposite_edge_spawn(
                        next_state, next_state.player_pos, salt2
                    )
                    events.append("red_reposition")

    remaining_blue: list[tuple[int, int]] = []
    for blue in next_state.blue_balls:
        if not _collides(
            next_state.player_pos, next_state.player_radius, blue, next_state.blue_radius
        ):
            remaining_blue.append(blue)
            continue

        next_state.collected += 1
        events.append("collect_blue")
        is_freeze = next_state.freeze_pos is not None and blue == next_state.freeze_pos
        is_speedup = (
            next_state.speedup_pos is not None and blue == next_state.speedup_pos
        )
        is_slowdown = (
            next_state.slowdown_pos is not None and blue == next_state.slowdown_pos
        )
        if is_freeze:
            next_state.freeze_active = True
            next_state.freeze_timer_ms = FREEZE_DURATION_MS
            next_state.freeze_pos = None
            events.append("collect_freeze")
        if is_speedup:
            next_state.speedup_active = True
            next_state.speedup_timer_ms = SPEEDUP_DURATION_MS
            next_state.player_speed = next_state.base_player_speed * 2
            next_state.speedup_pos = None
            events.append("collect_speedup")
        if is_slowdown:
            next_state.slowdown_active = True
            next_state.slowdown_timer_ms = SLOWDOWN_DURATION_MS
            next_state.current_red_speed = max(1, next_state.base_red_speed // 2)
            next_state.slowdown_pos = None
            events.append("collect_slowdown")

    next_state.blue_balls = remaining_blue

    if not next_state.freeze_active:
        for red in next_state.red_balls:
            if _collides(
                next_state.player_pos, next_state.player_radius, red, next_state.red_radius
            ):
                next_state.lose = True
                events.append("lose")
                break

    if next_state.collected >= next_state.num_blue:
        next_state.win = True
        events.append("win")

    next_state.tick += 1
    return EngineTickResult(
        state=next_state,
        events=events,
        ui_hints=UiHints(
            freeze_seconds_left=_seconds_left(next_state.freeze_timer_ms)
            if next_state.freeze_active
            else 0,
            speedup_seconds_left=_seconds_left(next_state.speedup_timer_ms)
            if next_state.speedup_active
            else 0,
            slowdown_seconds_left=_seconds_left(next_state.slowdown_timer_ms)
            if next_state.slowdown_active
            else 0,
        ),
    )

