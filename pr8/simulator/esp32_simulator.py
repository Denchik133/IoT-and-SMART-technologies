
import time
import random
import getpass
import threading
import sys
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# ==========================================
# MQTT CONFIGURATION
# ==========================================

MQTT_BROKER = "localhost"
MQTT_PORT = 1884
MQTT_USERNAME = "greenhouse_app"

MQTT_TOPIC_PREFIX = "greenhouse"

SENSOR_INTERVAL = 3
HEARTBEAT_INTERVAL = 5

mqtt_connected = threading.Event()

# ==========================================
# MQTT TOPICS
# ==========================================

TOPICS = {
    "air_temp": f"{MQTT_TOPIC_PREFIX}/sensors/air_temp",
    "air_humidity": f"{MQTT_TOPIC_PREFIX}/sensors/air_humidity",
    "soil_temp": f"{MQTT_TOPIC_PREFIX}/sensors/soil_temp",
    "soil_humidity": f"{MQTT_TOPIC_PREFIX}/sensors/soil_humidity",
    "lux": f"{MQTT_TOPIC_PREFIX}/sensors/lux",
    "co2": f"{MQTT_TOPIC_PREFIX}/sensors/co2",

    "pump": f"{MQTT_TOPIC_PREFIX}/actuators/pump",
    "fan": f"{MQTT_TOPIC_PREFIX}/actuators/fan",
    "light": f"{MQTT_TOPIC_PREFIX}/actuators/light",
    "window": f"{MQTT_TOPIC_PREFIX}/actuators/window",
    "heater": f"{MQTT_TOPIC_PREFIX}/actuators/heater",

    "status": f"{MQTT_TOPIC_PREFIX}/system/status",
}

# 11 virtual devices
DEVICE_IDS = [
    "air_temp",
    "air_humidity",
    "soil_temp",
    "soil_humidity",
    "lux",
    "co2",
    "pump",
    "fan",
    "light",
    "heater",
    "window",
]


def current_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def health_topic(device_id, field):
    return f"{MQTT_TOPIC_PREFIX}/health/{device_id}/{field}"


# ==========================================
# INITIAL SENSOR VALUES
# ==========================================

air_temp = 24.0
air_humidity = 60.0

soil_temp = 20.0
soil_humidity = 55.0

lux = 5000.0
co2 = 450.0

# ==========================================
# ACTUATOR STATES
# ==========================================

actuators = {
    "pump": "OFF",
    "fan": "OFF",
    "light": "OFF",
    "window": "0",
    "heater": "OFF",
}


# ==========================================
# DEVICE HEALTH MONITORING
# ==========================================

def publish_device_health(client, status="ONLINE"):
    timestamp = current_timestamp()

    for device_id in DEVICE_IDS:
        client.publish(
            health_topic(device_id, "status"),
            status,
            qos=1,
            retain=True
        )

        client.publish(
            health_topic(device_id, "heartbeat"),
            timestamp,
            qos=0,
            retain=False
        )

        client.publish(
            health_topic(device_id, "last_seen"),
            timestamp,
            qos=1,
            retain=True
        )

    print(
        f"[HEALTH] {len(DEVICE_IDS)} devices: {status} "
        f"| Last Seen: {timestamp}"
    )


# ==========================================
# MQTT CONNECTION CALLBACK
# ==========================================

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[ESP32] MQTT connection: Success")

        mqtt_connected.set()

        client.subscribe(f"{MQTT_TOPIC_PREFIX}/actuators/#")

        client.publish(
            TOPICS["status"],
            "ONLINE",
            qos=1,
            retain=True
        )

        publish_device_health(client, "ONLINE")

        print("[ESP32] Actuator topics subscribed")
        print("[ESP32] System status: ONLINE")

    else:
        print(f"[ESP32] MQTT connection error: {reason_code}")


# ==========================================
# MQTT MESSAGE CALLBACK
# ==========================================

def on_message(client, userdata, message):
    topic = message.topic
    value = message.payload.decode("utf-8").strip()

    print(f"[MQTT COMMAND] {topic} -> {value}")

    if topic == TOPICS["pump"]:
        actuators["pump"] = value
        print(f"[ACTUATOR] Pump: {value}")

    elif topic == TOPICS["fan"]:
        actuators["fan"] = value
        print(f"[ACTUATOR] Fan: {value}")

    elif topic == TOPICS["light"]:
        actuators["light"] = value
        print(f"[ACTUATOR] Grow Light: {value}")

    elif topic == TOPICS["window"]:
        actuators["window"] = value
        print(f"[ACTUATOR] Window: {value}%")

    elif topic == TOPICS["heater"]:
        actuators["heater"] = value
        print(f"[ACTUATOR] Heater: {value}")


# ==========================================
# SENSOR DATA GENERATION
# ==========================================

def publish_sensor_data(client):
    global air_temp
    global air_humidity
    global soil_temp
    global soil_humidity
    global lux
    global co2

    # Natural changes
    air_temp += random.uniform(-0.4, 0.4)
    air_humidity += random.uniform(-1.0, 1.0)

    soil_temp += random.uniform(-0.2, 0.2)
    soil_humidity += random.uniform(-1.5, 1.0)

    lux += random.uniform(-300, 300)
    co2 += random.uniform(-15, 15)

    # Sensor limits
    air_temp = max(10, min(45, air_temp))
    air_humidity = max(20, min(90, air_humidity))

    soil_temp = max(10, min(35, soil_temp))
    soil_humidity = max(0, min(100, soil_humidity))

    lux = max(0, min(20000, lux))
    co2 = max(300, min(1500, co2))

    # Actuator influence
    if actuators["pump"] == "ON":
        soil_humidity += 3

    if actuators["fan"] == "ON":
        air_temp -= 0.5

    if actuators["heater"] == "ON":
        air_temp += 0.5

    if actuators["light"] == "ON":
        lux += 500

    # Apply limits again
    soil_humidity = max(0, min(100, soil_humidity))
    air_temp = max(10, min(45, air_temp))
    lux = max(0, min(20000, lux))

    # Publish sensor values
    client.publish(TOPICS["air_temp"], f"{air_temp:.1f}")
    client.publish(TOPICS["air_humidity"], f"{air_humidity:.1f}")

    client.publish(TOPICS["soil_temp"], f"{soil_temp:.1f}")
    client.publish(TOPICS["soil_humidity"], f"{soil_humidity:.1f}")

    client.publish(TOPICS["lux"], f"{lux:.0f}")
    client.publish(TOPICS["co2"], f"{co2:.0f}")

    print(
        f"[DATA] "
        f"T_air: {air_temp:.1f} C | "
        f"Air_Hum: {air_humidity:.1f}% | "
        f"Soil_T: {soil_temp:.1f} C | "
        f"Soil_Hum: {soil_humidity:.1f}% | "
        f"Lux: {lux:.0f} | "
        f"CO2: {co2:.0f}"
    )


# ==========================================
# MQTT CLIENT
# ==========================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="ESP32-Greenhouse-Simulator"
)

client.on_connect = on_connect
client.on_message = on_message


# ==========================================
# MQTT AUTHENTICATION
# ==========================================

print("[ESP32] Smart Greenhouse Simulator started")
print(f"[ESP32] MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"[ESP32] Username: {MQTT_USERNAME}")

password = getpass.getpass("Enter MQTT password: ")

client.username_pw_set(MQTT_USERNAME, password)

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

except Exception as error:
    print(f"[ESP32] MQTT connection error: {error}")
    sys.exit(1)


# ==========================================
# START MQTT NETWORK LOOP
# ==========================================

client.loop_start()

if not mqtt_connected.wait(5):
    print("[ESP32] MQTT authentication or connection failed.")

    client.loop_stop()
    client.disconnect()

    sys.exit(1)


# ==========================================
# MAIN SIMULATION LOOP
# ==========================================

last_heartbeat = time.monotonic()

try:
    while True:
        publish_sensor_data(client)

        current_time = time.monotonic()

        if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
            publish_device_health(client, "ONLINE")
            last_heartbeat = current_time

        time.sleep(SENSOR_INTERVAL)

except KeyboardInterrupt:
    print("\n[ESP32] Stopping simulator...")

    publish_device_health(client, "OFFLINE")

    client.publish(
        TOPICS["status"],
        "OFFLINE",
        qos=1,
        retain=True
    )

    time.sleep(1)

    client.loop_stop()
    client.disconnect()

    print("[ESP32] Simulator stopped.")
