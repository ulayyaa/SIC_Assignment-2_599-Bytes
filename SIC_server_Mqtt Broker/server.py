import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
import datetime

MONGO_URI = "mongodb+srv://ranggaF:42413@cluster0.xzauk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sensor_data"]
collection = db["sensor_read"]

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883 
MQTT_TOPIC = "sensor/data"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        data["timestamp"] = datetime.datetime.utcnow()
        
        collection.insert_one(data)
        print("Data received and saved:", data)
    
    except Exception as e:
        print("Error processing MQTT message:", e)

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe(MQTT_TOPIC)
    print("Listening for MQTT messages...")
    mqtt_client.loop_forever()

except Exception as e:
    print("MQTT Connection Error:", e)
