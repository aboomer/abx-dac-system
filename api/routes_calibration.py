from fastapi import APIRouter

from api.clicker_modes import manager, ClickerHandlers

router = APIRouter()

# Meter start/stop endpoints and real Next/Back/Reveal/Hide behaviour for a
# future guided-calibration routine arrive in a later build stage. This mode
# is registered now (no-op) so the remote does nothing unexpected while the
# Calibration page is open, and so that later work can register real
# handlers into this exact slot without touching api/clicker.py again.


async def _noop():
    pass


def register_clicker_mode():
    manager.register(
        "calibration",
        ClickerHandlers(on_next=_noop, on_replay=_noop, on_reveal=_noop, on_hide=_noop),
    )
