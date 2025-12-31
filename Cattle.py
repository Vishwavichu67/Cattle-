import requests
import time
from datetime import datetime

# 🔑 Replace with your real Blynk Auth Token
TOKEN = "S01Qf4vRbB4NxoPr8sc2mwo-AuBgJJSa"

# Function to read a virtual pin
def read_pin(pin):
    url = f"https://blynk.cloud/external/api/get?token={TOKEN}&{pin}"
    r = requests.get(url, timeout=5)
    return r.text.strip()

print("📡 Connecting to Blynk Cloud...\n")

while True:
    try:
        temp = float(read_pin("V2"))
        hr = float(read_pin("V3"))
        motion = int(read_pin("V5"))

        status = "MOVING 🐄" if motion == 1 else "NOT MOVING 🛑"

        print("-----------------------------------")
        print("Time       :", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("Temperature:", temp, "°C")
        print("Heart Rate :", hr, "BPM")
        print("Motion     :", status)
        print("-----------------------------------\n")

        time.sleep(5)

    except Exception as e:
        print("❌ Error reading data:", e)
        time.sleep(5)

