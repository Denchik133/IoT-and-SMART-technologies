import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEVICES_FILE = BASE_DIR / "devices.json"
TARGET_VERSION = "2.0"


def load_devices():
    with open(DEVICES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_devices(data):
    with open(DEVICES_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def update_device(device):
    device_id = device["id"]

    if device["status"] != "ONLINE":
        print(f"[SKIP] {device_id}: device is OFFLINE")
        return False

    print(f"[OTA] {device_id}: downloading firmware {TARGET_VERSION}...")
    time.sleep(0.5)

    print(f"[OTA] {device_id}: verifying firmware...")
    time.sleep(0.3)

    print(f"[OTA] {device_id}: applying update...")
    time.sleep(0.5)

    device["version"] = TARGET_VERSION
    print(f"[SUCCESS] {device_id}: updated to v{TARGET_VERSION}")
    return True


def main():
    data = load_devices()
    devices = data["devices"]

    print("Smart Greenhouse OTA Update")
    print("Current version: 1.0")
    print(f"Target version: {TARGET_VERSION}")
    print(f"Devices: {len(devices)}")
    print("-" * 40)

    successful = 0

    # First update one device as a pilot rollout.
    pilot = devices[0]
    print("\nPILOT ROLLOUT")
    if update_device(pilot):
        successful += 1
        save_devices(data)

    print("\nBATCH ROLLOUT")
    for device in devices[1:]:
        if update_device(device):
            successful += 1
            save_devices(data)

    print("\nUPDATE SUMMARY")
    print(f"Successfully updated: {successful}/{len(devices)}")

    versions = {}
    for device in devices:
        versions[device["version"]] = versions.get(device["version"], 0) + 1

    for version, count in versions.items():
        print(f"Version {version}: {count} device(s)")


if __name__ == "__main__":
    main()
