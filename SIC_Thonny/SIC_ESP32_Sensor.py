from machine import Pin, ADC
import network
import ujson
import utime as time
import dht
import urequests as requests

DEVICE_ID = "demo-machine"
WIFI_SSID = "poco"
WIFI_PASSWORD = "hotspot44231"
UBIDOTS_TOKEN = "BBUS-jsfxoukARnkvGzSfmBBAdtzV60TQF3"

MONGO_URL = "http://192.168.208.67:5000/sensors"

UBIDOTS_URL = f"http://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_ID}"

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

def send_to_mongo(temperature, humidity, motion, ldr_value):
    headers = {"Content-Type": "application/json"}
    data = {
        "device_id": DEVICE_ID,
        "temp": temperature,
        "humidity": humidity,
        "motion_detected": motion,
        "ldr_value": ldr_value
    }
    try:
        print(f"Sending data to {MONGO_URL}...")  # Debug
        response = requests.post(MONGO_URL, json=data, headers=headers)
        print("Response Code:", response.status_code)  # Debug
        print("Response:", response.text)  # Debug
        response.close()
    except Exception as e:
        print("Failed to send data to MongoDB:", e)


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
        print("Data sent to Ubidots! Response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data to Ubidots:", e)

connect_wifi()

print("ESP32 IP Address:", network.WLAN(network.STA_IF).ifconfig()[0])

dht_sensor = dht.DHT11(DHT_PIN)

while True:
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()

        motion = PIR_PIN.value()  

        ldr_value = LDR_PIN.read()  

        if ldr_value < 2000:
            LED_RED.on()  
        else:
            LED_RED.off()

        if motion == 1:
            LED_GREEN.on()  
        else:
            LED_GREEN.off()
            
        if temperature >= 35:
            LED_YELLOW.on()
        else:
            LED_YELLOW.off()

        print(f"Temperature: {temperature}°C, Humidity: {humidity}%, Motion: {'Detected' if motion else 'None'}, LDR: {ldr_value}")

        send_to_mongo(temperature, humidity, motion, ldr_value)
        send_to_ubidots(temperature, humidity, motion, ldr_value)

    except Exception as sensor_error:
        print("Sensor read error:", sensor_error)

    time.sleep(2)
