import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SOURCE = BASE_DIR / "config_v1.json"
BACKUP = BASE_DIR / "config_v1_backup.json"
TARGET = BASE_DIR / "config_v2.json"


def migrate():
    if not SOURCE.exists():
        raise FileNotFoundError("Source configuration not found")

    with open(SOURCE, "r", encoding="utf-8") as file:
        config = json.load(file)

    if config["config_version"] != 1:
        raise ValueError("Only configuration version 1 can be migrated")

    shutil.copy2(SOURCE, BACKUP)

    config["config_version"] = 2

    config["monitoring"].update({
        "device_health_check": True,
        "offline_timeout": 15,
        "anomaly_detection": True
    })

    config["ota"] = {
        "enabled": True,
        "firmware_version": "2.0",
        "rollback_supported": True
    }

    with open(TARGET, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)

    print("Configuration migration completed")
    print(f"Backup: {BACKUP.name}")
    print(f"New configuration: {TARGET.name}")
    print("Configuration version: 1 -> 2")


if __name__ == "__main__":
    migrate()
