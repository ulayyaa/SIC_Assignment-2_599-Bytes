from machine import Pin, ADC
import network
import ujson
import utime as time
import dht
import urequests as requests
import ubinascii
import machine
import micropython
from umqtt.robust import MQTTClient

WIFI_SSID = "poco"
WIFI_PASSWORD = "hotspot44231"

DEVICE_ID = "demo-machine"
UBIDOTS_URL = f"http://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_ID}"
UBIDOTS_TOKEN = "BBUS-jsfxoukARnkvGzSfmBBAdtzV60TQF3"

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"
CLIENT_ID = ubinascii.hexlify(machine.unique_id()).decode()

DHT_PIN = Pin(14)  
PIR_PIN = Pin(13, Pin.IN)  
LDR_PIN = ADC(Pin(32))  
LDR_PIN.atten(ADC.ATTN_11DB)  

LED_RED = Pin(4, Pin.OUT)  
LED_GREEN = Pin(15, Pin.OUT)  
LED_YELLOW = Pin(2, Pin.OUT)  

def connect_wifi():
    wifi_client = network.WLAN(network.STA_IF)
    wifi_client.active(True)
    print("Connecting to WiFi...")
    wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

    retry_count = 0
    while not wifi_client.isconnected():
        print("Connecting...")
        time.sleep(1)
        retry_count += 1
        if retry_count > 20:  
            print("Failed to connect to WiFi. Restarting...")
            machine.reset()  

    print("WiFi Connected! IP:", wifi_client.ifconfig()[0])

def connect_mqtt():
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT)
    try:
        client.connect()
        print("Connected to MQTT Broker:", MQTT_BROKER)
    except Exception as e:
        print("Failed to connect to MQTT:", e)
    return client


def send_to_ubidots(temperature, humidity, motion, ldr_value):
    headers = {"Content-Type": "application/json", "X-Auth-Token": UBIDOTS_TOKEN}
    data = {
        "temp": temperature,
        "humidity": humidity,
        "motion_detected": motion,
        "ldr_value": ldr_value
    }
    try:
        response = requests.post(UBIDOTS_URL, json=data, headers=headers)
        print("Sent to Ubidots:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data to Ubidots:", e)

def send_to_mqtt(client, temperature, humidity, motion, ldr_value):
    try:
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "motion_detected": motion,
            "ldr_value": ldr_value
        }
        mqtt_payload = ujson.dumps(data)
        client.publish(MQTT_TOPIC, mqtt_payload)
        print("Sent to MQTT:", mqtt_payload)
    except Exception as e:
        print("Error sending data to MQTT:", e)

connect_wifi()
mqtt_client = connect_mqtt()

dht_sensor = dht.DHT11(DHT_PIN)

while True:
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        motion = PIR_PIN.value()  
        ldr_value = LDR_PIN.read()  

        LED_RED.value(ldr_value < 2000)  
        LED_GREEN.value(motion)  
        LED_YELLOW.value(temperature >= 35)  

        print(f"Temp: {temperature}°C, Humidity: {humidity}%, Motion: {motion}, LDR: {ldr_value}")

        send_to_ubidots(temperature, humidity, motion, ldr_value)

        send_to_mqtt(mqtt_client, temperature, humidity, motion, ldr_value)

    except Exception as sensor_error:
        print("Sensor read error:", sensor_error)

    time.sleep(2)
