
import time
import random
import getpass
import threading
import sys
import paho.mqtt.client as mqtt

# НАЛАШТУВАННЯ MQTT

MQTT_BROKER = "localhost"
MQTT_PORT = 1884
MQTT_USERNAME = "greenhouse_app"

MQTT_TOPIC_PREFIX = "greenhouse"

# ПОДІЯ УСПІШНОГО ПІДКЛЮЧЕННЯ

mqtt_connected = threading.Event()

# MQTT TOPICS

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

# ПОЧАТКОВІ ЗНАЧЕННЯ СЕНСОРІВ

air_temp = 24.0
air_humidity = 60.0

soil_temp = 20.0
soil_humidity = 55.0

lux = 5000.0
co2 = 450.0

# СТАН АКТУАТОРІВ

actuators = {
    "pump": "OFF",
    "fan": "OFF",
    "light": "OFF",
    "window": "0",
    "heater": "OFF",
}

# ФУНКЦІЯ ОБРОБКИ ПІДКЛЮЧЕННЯ MQTT

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[ESP32] Підключення до MQTT: Success")

        mqtt_connected.set()

        # Підписуємося на команди актуаторів
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/actuators/#")

        # Повідомляємо OpenHAB, що симулятор працює
        client.publish(TOPICS["status"], "ONLINE", retain=True)

        print("[ESP32] MQTT topics subscribed")
        print("[ESP32] Status: ONLINE")

    else:
        print(f"[ESP32] Помилка MQTT. Код: {reason_code}")


# ФУНКЦІЯ ОТРИМАННЯ КОМАНД ВІД OPENHAB

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


# ФУНКЦІЯ ПУБЛІКАЦІЇ ДАНИХ

def publish_sensor_data(client):
    global air_temp
    global air_humidity
    global soil_temp
    global soil_humidity
    global lux
    global co2

    # Невеликі природні зміни показників
    air_temp += random.uniform(-0.4, 0.4)
    air_humidity += random.uniform(-1.0, 1.0)

    soil_temp += random.uniform(-0.2, 0.2)
    soil_humidity += random.uniform(-1.5, 1.0)

    lux += random.uniform(-300, 300)
    co2 += random.uniform(-15, 15)

    # Обмеження значень
    air_temp = max(10, min(45, air_temp))
    air_humidity = max(20, min(90, air_humidity))

    soil_temp = max(10, min(35, soil_temp))
    soil_humidity = max(0, min(100, soil_humidity))

    lux = max(0, min(20000, lux))
    co2 = max(300, min(1500, co2))

    # Якщо насос увімкнений - ґрунт поступово зволожується
    if actuators["pump"] == "ON":
        soil_humidity += 3

    # Якщо вентилятор працює - температура трохи знижується
    if actuators["fan"] == "ON":
        air_temp -= 0.5

    # Якщо нагрівач працює - температура підвищується
    if actuators["heater"] == "ON":
        air_temp += 0.5

    # Якщо лампа працює - збільшуємо освітленість
    if actuators["light"] == "ON":
        lux += 500

    # Повторне обмеження після впливу актуаторів
    soil_humidity = max(0, min(100, soil_humidity))
    air_temp = max(10, min(45, air_temp))
    lux = max(0, min(20000, lux))

    # Відправлення даних через MQTT
    client.publish(TOPICS["air_temp"], f"{air_temp:.1f}")
    client.publish(TOPICS["air_humidity"], f"{air_humidity:.1f}")

    client.publish(TOPICS["soil_temp"], f"{soil_temp:.1f}")
    client.publish(TOPICS["soil_humidity"], f"{soil_humidity:.1f}")

    client.publish(TOPICS["lux"], f"{lux:.0f}")
    client.publish(TOPICS["co2"], f"{co2:.0f}")

    # Виведення інформації в консоль
    print(
        f"[Дані відправлено] "
        f"T_air: {air_temp:.1f}°C | "
        f"Air_Hum: {air_humidity:.1f}% | "
        f"Soil_T: {soil_temp:.1f}°C | "
        f"Soil_Hum: {soil_humidity:.1f}% | "
        f"Lux: {lux:.0f} | "
        f"CO2: {co2:.0f}"
    )


# СТВОРЕННЯ MQTT КЛІЄНТА

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="ESP32-Greenhouse-Simulator"
)

client.on_connect = on_connect
client.on_message = on_message


# ПІДКЛЮЧЕННЯ ДО MQTT BROKER

print("[ESP32] Симулятор ESP32 запущено")
print(f"[ESP32] Підключення до MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"[ESP32] Користувач: {MQTT_USERNAME}")

password = getpass.getpass("Введіть пароль greenhouse_app: ")

client.username_pw_set(MQTT_USERNAME, password)

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

except Exception as error:
    print(f"[ESP32] ПОМИЛКА ПІДКЛЮЧЕННЯ: {error}")
    print(f"[ESP32] Перевірте Mosquitto на порту {MQTT_PORT}.")
    sys.exit(1)


# ЗАПУСК MQTT NETWORK LOOP

client.loop_start()

# ОЧІКУВАННЯ УСПІШНОЇ АВТОРИЗАЦІЇ

if not mqtt_connected.wait(5):
    print("[ESP32] Не вдалося підключитися або авторизуватися на MQTT broker.")

    client.loop_stop()
    client.disconnect()

    sys.exit(1)


# ОСНОВНИЙ ЦИКЛ СИМУЛЯТОРА

try:
    while True:
        publish_sensor_data(client)
        time.sleep(3)

except KeyboardInterrupt:
    print("\n[ESP32] Зупинка симулятора...")

    client.publish(TOPICS["status"], "OFFLINE", retain=True)

    time.sleep(0.5)

    client.loop_stop()
    client.disconnect()

    print("[ESP32] Симулятор завершено.")
