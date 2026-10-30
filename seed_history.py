import psycopg2
import math
import random
from datetime import datetime, timedelta

conn = psycopg2.connect(
    host="localhost",
    database="vessel_data",
    user="admin",
    password="nikonasvrs"
)
conn.autocommit = True
cursor = conn.cursor()

end_time = datetime.now()
start_time = end_time - timedelta(days=7)
current_time = start_time

print("Γέμισμα βάσης με ιστορικά δεδομένα 7 ημερών. Περίμενε λίγο...")

while current_time < end_time:
    # Προσομοίωση ρεαλιστικής καμπύλης βάσει της ώρας της ημέρας + λίγος "θόρυβος"
    hour = current_time.hour
    curve = math.sin(math.pi * (hour / 12.0)) * 10 
    noise = random.uniform(-0.5, 0.5)
    temp = round(65.0 + curve + noise, 2)
    
    cursor.execute(
        "INSERT INTO sensor_data (time, vessel_id, temperature) VALUES (%s, %s, %s)",
        (current_time, "ship_01", temp)
    )
    current_time += timedelta(minutes=5) # 1 μέτρηση ανά 5 λεπτά

print("Τα ιστορικά δεδομένα προστέθηκαν επιτυχώς!")
cursor.close()
conn.close()
