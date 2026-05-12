import unittest

from engine import (
    ACCOUNT_SCHEMA_VERSION,
    GAME_STATE_SCHEMA_VERSION,
    GameState,
    game_state_from_dict,
    game_state_to_dict,
    migrate_accounts_payload,
)


class SerializeTests(unittest.TestCase):
    def test_game_state_round_trip(self):
        state = GameState(
            width=1024,
            height=768,
            level=7,
            num_blue=4,
            collected=2,
            player_pos=(320, 240),
            red_balls=[(10, 10), (20, 20)],
            blue_balls=[(100, 120), (140, 120)],
            freeze_pos=(100, 120),
            speedup_pos=(140, 120),
            slowdown_pos=None,
            freeze_active=True,
            freeze_timer_ms=1234,
        )
        payload = game_state_to_dict(state)
        self.assertEqual(payload["schema_version"], GAME_STATE_SCHEMA_VERSION)
        round_tripped = game_state_from_dict(payload)
        self.assertEqual(round_tripped.level, state.level)
        self.assertEqual(round_tripped.player_pos, state.player_pos)
        self.assertEqual(round_tripped.freeze_active, state.freeze_active)

    def test_account_migration_from_legacy(self):
        legacy = {
            "guest1": 4,
            "kate": {"level": 10, "password": None, "is_admin": False},
            "admin": {"level": 22, "password": "x", "is_admin": True},
        }
        migrated = migrate_accounts_payload(legacy)
        self.assertEqual(migrated["guest1"]["level"], 4)
        self.assertEqual(migrated["admin"]["is_admin"], True)
        self.assertEqual(
            migrated["kate"]["schema_version"], ACCOUNT_SCHEMA_VERSION
        )


if __name__ == "__main__":
    unittest.main()

