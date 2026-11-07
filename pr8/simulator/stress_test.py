import getpass
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1884
USERNAME = "greenhouse_app"

DEVICE_COUNT = 30
UPDATE_INTERVAL = 0.5
TEST_DURATION = 60

TOPIC_PREFIX = "greenhouse/stress"

devices = [f"virtual_device_{i:02d}" for i in range(1, DEVICE_COUNT + 1)]

sent_messages = 0
failed_messages = 0
connected = False


def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    if reason_code == 0:
        connected = True
        print("Connected to MQTT broker.")
    else:
        print(f"Connection failed: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    global connected
    connected = False


def main():
    global sent_messages, failed_messages

    password = getpass.getpass("MQTT password: ")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="greenhouse_stress_test"
    )

    client.username_pw_set(USERNAME, password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    print("\nStarting stress test...")
    print(f"Virtual devices: {DEVICE_COUNT}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"Duration: {TEST_DURATION} seconds\n")

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()

        wait_start = time.time()
        while not connected and time.time() - wait_start < 10:
            time.sleep(0.1)

        if not connected:
            raise RuntimeError("Could not connect to MQTT broker.")

        start_time = time.time()
        end_time = start_time + TEST_DURATION

        while time.time() < end_time:
            for device in devices:
                if time.time() >= end_time:
                    break

                payload = {
                    "device": device,
                    "temperature": round(random.uniform(18, 35), 2),
                    "humidity": round(random.uniform(30, 85), 2),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                topic = f"{TOPIC_PREFIX}/{device}/sensors"

                result = client.publish(
                    topic,
                    json.dumps(payload),
                    qos=0,
                    retain=False
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    sent_messages += 1
                else:
                    failed_messages += 1

            elapsed = time.time() - start_time
            print(
                f"\rElapsed: {elapsed:.1f}s | "
                f"Sent: {sent_messages} | "
                f"Errors: {failed_messages}",
                end="",
                flush=True
            )

            time.sleep(UPDATE_INTERVAL)

        client.loop_stop()
        client.disconnect()

        elapsed = time.time() - start_time

        print("\n\n========== TEST RESULTS ==========")
        print(f"Virtual devices: {DEVICE_COUNT}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Messages sent: {sent_messages}")
        print(f"Publish errors: {failed_messages}")

        if elapsed > 0:
            print(
                f"Average message rate: "
                f"{sent_messages / elapsed:.2f} messages/second"
            )

        print("Stress test completed.")

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        client.loop_stop()
        client.disconnect()

    except Exception as error:
        print(f"\nStress test error: {error}")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
