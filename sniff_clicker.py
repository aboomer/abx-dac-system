import asyncio
import evdev

async def watch(dev):
    try:
        async for event in dev.async_read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                print(f"[{dev.name}] {key_event}")
    except Exception as e:
        print(f"[{dev.name}] error: {e}")

async def main():
    devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
    logi = [d for d in devices if "logitech" in d.name.lower()]
    print("Listening on:")
    for d in logi:
        print(f"  {d.path}  {d.name}")
    print("Press buttons on the clicker now (30s)...")
    await asyncio.wait_for(
        asyncio.gather(*(watch(d) for d in logi)),
        timeout=30,
    )

try:
    asyncio.run(main())
except asyncio.TimeoutError:
    print("DONE")
