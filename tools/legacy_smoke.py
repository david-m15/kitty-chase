import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import GameState, InputFrame, game_state_to_dict, step


def run_smoke():
    state = GameState(
        width=800,
        height=600,
        level=1,
        num_blue=1,
        player_pos=(100, 100),
        blue_balls=[(110, 100)],
        red_balls=[(700, 500)],
    )
    result = step(state, InputFrame(direction_x=1, direction_y=0, timestamp_ms=10), 16)
    payload = game_state_to_dict(result.state)
    output_path = Path("build") / "legacy_smoke_output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("legacy smoke ok")


if __name__ == "__main__":
    run_smoke()
