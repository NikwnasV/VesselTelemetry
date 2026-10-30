import paho.mqtt.client as mqtt
import time
import json
import random
import math

client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Σημεία ελέγχου: Καλαμάτα -> Έξοδος Κόλπου -> Ταίναρο -> Βόρεια Κρήτη -> Σούδα
waypoints = [
    (37.0166, 22.1127),
    (36.7588, 22.0463),
    (36.3538, 22.4697),
    (35.5348, 23.9930),
    (35.4907, 24.0682)
]

current_wp = 0
direction = 1
lat, lng = waypoints[0]
current_temp = 65.0

# Ταχύτητα κίνησης στον χάρτη ανά κύκλο (περίπου 300 μέτρα)
step_size = 0.003 

print("Έναρξη ρεαλιστικής προσομοίωσης: Καλαμάτα <-> Κρήτη...")

while True:
    target_lat, target_lng = waypoints[current_wp + direction]
    
    # Υπολογισμός απόστασης μέχρι το επόμενο waypoint
    dist = math.hypot(target_lat - lat, target_lng - lng)
    
    if dist < step_size:
        # Μόλις φτάσει στο waypoint, αλλάζει στόχο
        current_wp += direction
        if current_wp == len(waypoints) - 1 or current_wp == 0:
            direction *= -1  # Επιστροφή αν έφτασε στο τέλος
        lat, lng = waypoints[current_wp]
    else:
        # Κίνηση προς τον στόχο
        lat += (target_lat - lat) / dist * step_size
        lng += (target_lng - lng) / dist * step_size

    # Προσθήκη ρεαλιστικού "θορύβου" στα δεδομένα GPS (κύματα/απόκλιση)
    lat_drift = lat + random.uniform(-0.0001, 0.0001)
    lng_drift = lng + random.uniform(-0.0001, 0.0001)

    # Ομαλή διακύμανση θερμοκρασίας κινητήρα
    current_temp = max(50.0, min(85.0, current_temp + random.uniform(-0.5, 0.5)))
    
    payload = json.dumps({
        "temperature": round(current_temp, 1),
        "lat": round(lat_drift, 6),
        "lng": round(lng_drift, 6)
    })
    
    client.publish("vessel/ship_01/telemetry", payload)
    print(f"Στάλθηκε: {payload}")
    time.sleep(2) # Στέλνει στίγμα κάθε 2 δευτερόλεπτα 
