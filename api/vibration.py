import asyncio
import glob
import logging
import os

logger = logging.getLogger("vibration")

# Logitech USB Receiver (Unifying/Bolt), vendor:product 046d:c53e.
# The vendor-specific HID++ channel is the interface with no evdev node
# (interfaces 0/1 carry standard keyboard/mouse/consumer-control usages,
# which evdev claims; interface 2 is HID++-only and is what we need here).
HID_ID_MATCH = "HID_ID=0003:0000046D:0000C53E"
HIDPP_INTERFACE_MARKER = "input2"

PRESENTER_CONTROL_FEATURE = 0x1A00  # {MSB, LSB} = 0x1a, 0x00
DEVICE_INDEX = 0x01  # first (only) device paired to the receiver

_feature_index_cache: int | None = None


def _find_hidpp_device_path() -> str:
    for uevent_path in glob.glob("/sys/class/hidraw/hidraw*/device/uevent"):
        with open(uevent_path) as f:
            content = f.read()
        if HID_ID_MATCH in content and HIDPP_INTERFACE_MARKER in content:
            hidraw_name = uevent_path.split("/")[4]
            return f"/dev/{hidraw_name}"
    raise RuntimeError("Logitech Spotlight HID++ interface not found")


def _send_recv(fd: int, report: bytes) -> bytes:
    os.write(fd, report)
    return os.read(fd, 20)


def _discover_feature_index(fd: int) -> int:
    swid = 0x01
    req = bytes([
        0x10, DEVICE_INDEX, 0x00,
        (0x00 << 4) | swid,
        (PRESENTER_CONTROL_FEATURE >> 8) & 0xFF,
        PRESENTER_CONTROL_FEATURE & 0xFF,
        0x00,
    ])
    reply = _send_recv(fd, req)
    return reply[4]


def _vibrate_sync(intensity: int, length: int):
    global _feature_index_cache
    device_path = _find_hidpp_device_path()
    fd = os.open(device_path, os.O_RDWR)
    try:
        if _feature_index_cache is None:
            _feature_index_cache = _discover_feature_index(fd)
            logger.info("PresenterControl feature index resolved: 0x%02x", _feature_index_cache)
        if _feature_index_cache == 0:
            raise RuntimeError("PresenterControl feature not supported by this device")

        swid = 0x02
        req = bytes([
            0x10, DEVICE_INDEX, _feature_index_cache,
            (0x01 << 4) | swid,  # function 1 = vibrate
            max(0, min(length, 10)),
            0xE8,  # fixed constant per protocol
            max(25, min(intensity, 255)),
        ])
        _send_recv(fd, req)
    finally:
        os.close(fd)


async def vibrate(intensity: int = 0x80, length: int = 0x00):
    """Trigger the Spotlight remote's haptic vibration motor.

    intensity: 25-255 (default 128). length: 0-10, exact meaning undocumented
    by Logitech (reverse-engineered from Projecteur) - 0 gives a short pulse.
    """
    try:
        await asyncio.to_thread(_vibrate_sync, intensity, length)
    except (FileNotFoundError, OSError, RuntimeError) as e:
        logger.warning("vibrate() failed: %s", e)
