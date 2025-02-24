from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import datetime

app = Flask(__name__)
CORS(app) 

MONGO_URI = "mongodb+srv://ranggaF:42413@cluster0.xzauk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sensor_data"]
collection = db["sensor_readings"]

@app.route('/sensors', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json

        data["timestamp"] = datetime.datetime.utcnow()

        collection.insert_one(data)

        return jsonify({"message": "Data received and saved to MongoDB!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
