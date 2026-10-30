import paho.mqtt.client as mqtt
import psycopg2
import json
from datetime import datetime

# Σύνδεση με τη βάση δεδομένων
conn = psycopg2.connect(
    host="localhost",
    database="vessel_data",
    user="admin",
    password="nikonasvrs"
)
conn.autocommit = True
cursor = conn.cursor()

# Δημιουργία πίνακα και μετατροπή σε hypertable
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        time TIMESTAMPTZ NOT NULL,
        vessel_id TEXT NOT NULL,
        temperature DOUBLE PRECISION
    );
""")
try:
    cursor.execute("SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);")
except Exception:
    pass

def on_connect(client, userdata, flags, rc):
    print("Συνδέθηκε στον MQTT Broker!")
    client.subscribe("vessel/+/telemetry")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    vessel_id = msg.topic.split('/')[1]
    temp = payload.get("temperature")
    
    cursor.execute(
        "INSERT INTO sensor_data (time, vessel_id, temperature) VALUES (%s, %s, %s)",
        (datetime.now(), vessel_id, temp)
    )
    print(f"Καταγράφηκε: Πλοίο {vessel_id} | Θερμοκρασία {temp}°C")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
print("Η μικροϋπηρεσία ξεκίνησε. Αναμονή για δεδομένα...")
client.loop_forever()
