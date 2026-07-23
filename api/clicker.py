import asyncio
import logging

import evdev

logger = logging.getLogger("clicker")

# Forward/Back nav buttons show up as standard keys on the "kbd" interface.
KBD_DEVICE_PATH = "/dev/input/by-id/usb-Logitech_USB_Receiver-event-kbd"
# The pointer/laser button shows up as a left mouse click on the "mouse" interface.
MOUSE_DEVICE_PATH = "/dev/input/by-id/usb-Logitech_USB_Receiver-if01-event-mouse"

RECONNECT_DELAY_SECONDS = 3


async def _watch_device(device_path, handlers):
    """handlers: dict of (evdev.ecodes code) -> async callback(value).

    value passed to the callback is the raw evdev key value: 1=down, 0=up.
    """
    while True:
        try:
            device = evdev.InputDevice(device_path)
            logger.info("clicker connected: %s (%s)", device.name, device_path)
            async for event in device.async_read_loop():
                if event.type != evdev.ecodes.EV_KEY:
                    continue
                if event.value == 2:
                    continue  # ignore auto-repeat
                handler = handlers.get(event.code)
                if handler:
                    await handler(event.value)
        except (FileNotFoundError, OSError) as e:
            logger.warning("clicker device %s disconnected (%s), retrying in %ss",
                            device_path, e, RECONNECT_DELAY_SECONDS)
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)


async def watch_clicker(on_next, on_replay, on_reveal, on_hide):
    """Listen for Logitech Spotlight button presses and fire callbacks.

    Forward button -> KEY_RIGHT       -> on_next()   (key-down only)
    Back button    -> KEY_LEFT        -> on_replay() (key-down only)
    Pointer button  -> BTN_LEFT (mouse) -> on_reveal() on press, on_hide() on release

    Runs forever, reconnecting either interface if the receiver is unplugged.
    """
    async def next_handler(value):
        if value == 1:
            await on_next()

    async def replay_handler(value):
        if value == 1:
            await on_replay()

    async def pointer_handler(value):
        if value == 1:
            await on_reveal()
        elif value == 0:
            await on_hide()

    await asyncio.gather(
        _watch_device(KBD_DEVICE_PATH, {
            evdev.ecodes.KEY_RIGHT: next_handler,
            evdev.ecodes.KEY_LEFT: replay_handler,
        }),
        _watch_device(MOUSE_DEVICE_PATH, {
            evdev.ecodes.BTN_LEFT: pointer_handler,
        }),
    )
