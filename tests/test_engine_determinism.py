import json
import unittest

from engine import GameState, InputFrame, game_state_to_dict, step


class EngineDeterminismTests(unittest.TestCase):
    def test_same_input_stream_yields_same_state(self):
        initial_state_a = GameState(
            width=800,
            height=600,
            level=3,
            num_blue=3,
            player_pos=(400, 300),
            red_balls=[(20, 20), (780, 580)],
            blue_balls=[(420, 300), (500, 300), (600, 300)],
            freeze_pos=(420, 300),
            speedup_pos=(500, 300),
            slowdown_pos=(600, 300),
            base_red_speed=3,
            current_red_speed=3,
        )
        initial_state_b = GameState(
            width=800,
            height=600,
            level=3,
            num_blue=3,
            player_pos=(400, 300),
            red_balls=[(20, 20), (780, 580)],
            blue_balls=[(420, 300), (500, 300), (600, 300)],
            freeze_pos=(420, 300),
            speedup_pos=(500, 300),
            slowdown_pos=(600, 300),
            base_red_speed=3,
            current_red_speed=3,
        )

        frames = [
            InputFrame(direction_x=1, direction_y=0, timestamp_ms=16),
            InputFrame(direction_x=1, direction_y=0, timestamp_ms=32),
            InputFrame(direction_x=0, direction_y=1, timestamp_ms=48),
            InputFrame(direction_x=0, direction_y=1, timestamp_ms=64),
            InputFrame(direction_x=-1, direction_y=0, timestamp_ms=80),
        ]

        state_a = initial_state_a
        state_b = initial_state_b
        for frame in frames:
            state_a = step(state_a, frame, 16).state
            state_b = step(state_b, frame, 16).state

        a_json = json.dumps(game_state_to_dict(state_a), sort_keys=True)
        b_json = json.dumps(game_state_to_dict(state_b), sort_keys=True)
        self.assertEqual(a_json, b_json)


if __name__ == "__main__":
    unittest.main()

