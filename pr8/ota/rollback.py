import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

BACKUP = BASE_DIR / "config_v1_backup.json"
CURRENT = BASE_DIR / "config_v2.json"
ROLLBACK = BASE_DIR / "config_rollback.json"


def rollback():
    if not BACKUP.exists():
        raise FileNotFoundError("Backup configuration not found")

    shutil.copy2(BACKUP, ROLLBACK)

    with open(ROLLBACK, "r", encoding="utf-8") as file:
        config = json.load(file)

    print("Rollback completed successfully")
    print(f"Restored configuration version: {config['config_version']}")
    print(f"Restored MQTT broker: {config['mqtt']['broker']}")
    print(f"Restored heartbeat interval: {config['monitoring']['heartbeat_interval']} seconds")


if __name__ == "__main__":
    rollback()
