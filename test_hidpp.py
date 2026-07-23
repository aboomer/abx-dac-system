import os
import sys

DEV = "/dev/hidraw2"

def send_recv(fd, report: bytes, label: str):
    print(f"--> {label}: {report.hex(' ')}")
    os.write(fd, report)
    reply = os.read(fd, 20)
    print(f"<-- {label}: {reply.hex(' ')}")
    return reply

def main():
    fd = os.open(DEV, os.O_RDWR)
    try:
        # getFeatureIndex(PresenterControl=0x1a00) on Root feature (index 0), function 0
        # [reportId, deviceIndex, featureIndex, (func<<4|swId), featureCode_MSB, featureCode_LSB, pad]
        swid = 0x01
        req = bytes([0x10, 0x01, 0x00, (0x00 << 4) | swid, 0x1a, 0x00, 0x00])
        reply = send_recv(fd, req, "getFeatureIndex(PresenterControl)")

        if len(reply) < 5:
            print("Reply too short, unexpected")
            return

        resolved_index = reply[4]
        print(f"\nResolved PresenterControl feature index: 0x{resolved_index:02x} ({resolved_index})")

        if resolved_index == 0:
            print("Index 0 = feature not found / not supported (or our request format is wrong)")
            return

        # Send vibrate command: function=1, swid arbitrary
        # [reportId, deviceIndex, pcIndex, (func<<4|swId), length, 0xe8, intensity]
        length = 0x00
        intensity = 0x80
        vib_swid = 0x02
        vibrate_req = bytes([0x10, 0x01, resolved_index, (0x01 << 4) | vib_swid, length, 0xe8, intensity])
        input("\nPress Enter to send vibrate command (watch/hold the remote)...")
        send_recv(fd, vibrate_req, "vibrate")

    finally:
        os.close(fd)

if __name__ == "__main__":
    main()
