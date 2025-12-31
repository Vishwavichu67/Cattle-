import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import time
import requests
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify, request

from alerts import send_email_alert

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = "S01Qf4vRbB4NxoPr8sc2mwo-AuBgJJSa"

DATA_MODE = "LIVE"   # LIVE / MANUAL

MANUAL_VALUES = {
    "temp": 38.0,
    "hr": 70,
    "motion": 1
}

CRITICAL_LIMITS = {
    "fever_temp": 40.0,
    "hr_low": 45,
    "hr_high": 120
}

# =========================
# TIME-BASED HISTORY
# =========================
# 1 record every ~3 seconds → 2 hours ≈ 2400 records
DATA_HISTORY = deque(maxlen=2500)

# =========================
# BLYNK READ
# =========================
def read_pin(pin):
    url = f"https://blynk.cloud/external/api/get?token={TOKEN}&{pin}"
    return float(requests.get(url).text)

# =========================
# TIME-BASED CHECKS
# =========================
def temp_high_last(seconds):
    cutoff = time.time() - seconds
    records = [d for d in DATA_HISTORY if d["time"] >= cutoff]
    return records and all(d["temp"] >= CRITICAL_LIMITS["fever_temp"] for d in records)

def no_movement_last(seconds):
    cutoff = time.time() - seconds
    records = [d for d in DATA_HISTORY if d["time"] >= cutoff]
    return records and all(d["motion"] == 0 for d in records)

def high_hr_last(seconds):
    cutoff = time.time() - seconds
    records = [d for d in DATA_HISTORY if d["time"] >= cutoff]
    return records and all(d["hr"] > CRITICAL_LIMITS["hr_high"] for d in records)

# =========================
# ROUTES
# =========================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/set_mode/<mode>", methods=["POST"])
def set_mode(mode):
    global DATA_MODE
    if mode.upper() in ["LIVE", "MANUAL"]:
        DATA_MODE = mode.upper()
    return jsonify({"mode": DATA_MODE})

@app.route("/set_manual_values", methods=["POST"])
def set_manual_values():
    data = request.json
    MANUAL_VALUES["temp"] = float(data["temp"])
    MANUAL_VALUES["hr"] = float(data["hr"])
    MANUAL_VALUES["motion"] = int(data["motion"])
    return jsonify({"status": "updated"})

# =========================
# DATA + ALERT ENGINE
# =========================
@app.route("/data")
def data():

    # -------------------------
    # DATA SOURCE
    # -------------------------
    if DATA_MODE == "LIVE":
        temp = read_pin("V2")
        hr = read_pin("V3")
        motion = int(read_pin("V5"))
    else:
        temp = MANUAL_VALUES["temp"]
        hr = MANUAL_VALUES["hr"]
        motion = MANUAL_VALUES["motion"]

    # -------------------------
    # STORE HISTORY
    # -------------------------
    DATA_HISTORY.append({
        "time": time.time(),
        "temp": temp,
        "hr": hr,
        "motion": motion
    })

    alert = "HEALTHY"
    reason = "Normal parameters"
    send_mail = False

    # -------------------------
    # INSTANT CONDITIONS
    # -------------------------
    if temp >= CRITICAL_LIMITS["fever_temp"]:
        alert = "FEVER ALERT"
        reason = "High Temperature (≥ 40°C)"
        send_mail = True

    elif motion == 0:
        issues = []

        if hr < CRITICAL_LIMITS["hr_low"]:
            issues.append("Low Heart Rate")
        elif hr > CRITICAL_LIMITS["hr_high"]:
            issues.append("High Heart Rate")

        if issues:
            alert = "CRITICAL ALERT"
            reason = "No Movement + " + ", ".join(issues)
            send_mail = True
        else:
            alert = "NO MOVEMENT BUT HEALTHY"
            reason = "No movement, vitals normal"

    # -------------------------
    # TIME-BASED CONDITIONS
    # -------------------------
    time_issues = []

    if temp_high_last(2 * 60 * 60):
        time_issues.append("High temperature for last 2 hours")

    if no_movement_last(2 * 60 * 60):
        time_issues.append("No movement for last 2 hours")

    if high_hr_last(1 * 60 * 60):
        time_issues.append("High heart rate for last 1 hour")

    if time_issues:
        alert = "SUSTAINED HEALTH ALERT"
        reason = "; ".join(time_issues)
        send_mail = True

    # -------------------------
    # EMAIL ALERT
    # -------------------------
    if send_mail:
        send_email_alert(
            "Cattle Health Alert (Time-Based Analysis)",
            f"""
Mode: {DATA_MODE}
Temperature: {temp} °C
Heart Rate: {hr} BPM
Motion: {'NOT MOVING' if motion == 0 else 'MOVING'}

Alert: {alert}
Reason:
{reason}
"""
        )

    return jsonify({
        "time": datetime.now().strftime("%H:%M:%S"),
        "temperature": temp,
        "heart_rate": hr,
        "motion": motion,
        "alert": alert,
        "reason": reason,
        "mode": DATA_MODE
    })

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
