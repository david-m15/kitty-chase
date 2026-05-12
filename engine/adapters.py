from typing import Protocol

from .state import GameState, InputFrame


class RenderAdapter(Protocol):
    def render(self, state: GameState) -> None:
        ...


class InputAdapter(Protocol):
    def read_input(self) -> InputFrame:
        ...


class StorageAdapter(Protocol):
    def load_accounts(self) -> dict[str, dict]:
        ...

    def save_accounts(self, accounts: dict[str, dict]) -> None:
        ...

    def load_progress(self, player_name: str | None, admin_mode: bool) -> int:
        ...

    def save_progress(
        self, level: int, player_name: str | None, admin_mode: bool
    ) -> None:
        ...


class UpdateAdapter(Protocol):
    def check_for_update(self) -> tuple[str | None, str | None]:
        ...

    def launch_update(self, installer_path: str) -> None:
        ...

