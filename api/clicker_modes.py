from dataclasses import dataclass
from typing import Awaitable, Callable

Handler = Callable[[], Awaitable[None]]


@dataclass
class ClickerHandlers:
    on_next: Handler
    on_replay: Handler
    on_reveal: Handler
    on_hide: Handler


class ClickerModeManager:
    def __init__(self):
        self._modes: dict[str, ClickerHandlers] = {}
        self._active: str | None = None

    def register(self, mode: str, handlers: ClickerHandlers) -> None:
        self._modes[mode] = handlers

    def set_active(self, mode: str) -> None:
        if mode not in self._modes:
            raise ValueError(f"unregistered clicker mode: {mode}")
        self._active = mode

    async def dispatch_next(self):
        await self._modes[self._active].on_next()

    async def dispatch_replay(self):
        await self._modes[self._active].on_replay()

    async def dispatch_reveal(self):
        await self._modes[self._active].on_reveal()

    async def dispatch_hide(self):
        await self._modes[self._active].on_hide()


manager = ClickerModeManager()
