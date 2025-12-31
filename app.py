import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import time
import requests
from datetime import datetime
from collections import deque
from flask import Flask, render_template, jsonify, request

from predict import cnn_predict
from alerts import send_email_alert, send_sms_alert
from retrain import retrain_model_with_steps

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================
TOKEN = "S01Qf4vRbB4NxoPr8sc2mwo-AuBgJJSa"

DATA_MODE = "LIVE"   # LIVE or MANUAL

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

EMAIL_COOLDOWN = 5     # seconds
LAST_EMAIL_TIME = 0

# =========================
# DATA HISTORY (FOR CHARTS)
# =========================
# ~10 minutes of data if reading every 3 seconds
DATA_HISTORY = deque(maxlen=200)

# =========================
# BLYNK READ
# =========================
def read_pin(pin):
    url = f"https://blynk.cloud/external/api/get?token={TOKEN}&{pin}"
    return float(requests.get(url).text)

# =========================
# ROUTES
# =========================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/training")
def training():
    return render_template("training.html")

# -------------------------
# MODE SWITCH
# -------------------------
@app.route("/set_mode/<mode>", methods=["POST"])
def set_mode(mode):
    global DATA_MODE
    if mode.upper() in ["LIVE", "MANUAL"]:
        DATA_MODE = mode.upper()
    return jsonify({"mode": DATA_MODE})

# -------------------------
# MANUAL INPUT
# -------------------------
@app.route("/set_manual_values", methods=["POST"])
def set_manual_values():
    global MANUAL_VALUES
    data = request.json
    MANUAL_VALUES["temp"] = float(data["temp"])
    MANUAL_VALUES["hr"] = float(data["hr"])
    MANUAL_VALUES["motion"] = int(data["motion"])
    return jsonify({"status": "updated"})

# -------------------------
# DATA + DECISION ENGINE
# -------------------------
@app.route("/data")
def data():
    global LAST_EMAIL_TIME

    # Select data source
    if DATA_MODE == "LIVE":
        temp = read_pin("V2")
        hr = read_pin("V3")
        motion = int(read_pin("V5"))
    else:
        temp = MANUAL_VALUES["temp"]
        hr = MANUAL_VALUES["hr"]
        motion = MANUAL_VALUES["motion"]

    # -------------------------
    # STORE DATA FOR CHARTS
    # -------------------------
    DATA_HISTORY.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "temp": temp,
        "hr": hr,
        "motion": motion
    })

    alert = "HEALTHY"
    reason = "Normal parameters"
    send_mail = False

    # 🔴 CONDITION 1: FEVER
    if temp >= CRITICAL_LIMITS["fever_temp"]:
        alert = "FEVER ALERT"
        reason = "High Temperature (≥ 40°C)"
        send_mail = True

    # 🟡 CONDITION 2: NO MOVEMENT
    elif motion == 0:
        issues = []

        if hr < CRITICAL_LIMITS["hr_low"]:
            issues.append("Low Heart Rate")
        elif hr > CRITICAL_LIMITS["hr_high"]:
            issues.append("High Heart Rate")

        if temp >= CRITICAL_LIMITS["fever_temp"]:
            issues.append("High Temperature")

        if issues:
            alert = "CRITICAL ALERT"
            reason = "No Movement + " + ", ".join(issues)
            send_mail = True
        else:
            alert = "NO MOVEMENT BUT HEALTHY"
            reason = "No movement, vitals normal"

    # -------------------------
    # EMAIL WITH COOLDOWN
    # -------------------------
    current_time = time.time()
    if send_mail and (current_time - LAST_EMAIL_TIME >= EMAIL_COOLDOWN):
        send_email_alert(
            "Cattle Health Alert",
            f"""
Mode: {DATA_MODE}
Temperature: {temp} °C
Heart Rate: {hr} BPM
Motion: {'NOT MOVING' if motion == 0 else 'MOVING'}

Alert: {alert}
Reason: {reason}
"""
        )
        LAST_EMAIL_TIME = current_time

    return jsonify({
        "time": datetime.now().strftime("%H:%M:%S"),
        "temperature": temp,
        "heart_rate": hr,
        "motion": motion,
        "alert": alert,
        "reason": reason,
        "mode": DATA_MODE
    })

# -------------------------
# HISTORY API (FOR CHARTS)
# -------------------------
@app.route("/history")
def history():
    return jsonify({
        "time": [d["time"] for d in DATA_HISTORY],
        "temperature": [d["temp"] for d in DATA_HISTORY],
        "heart_rate": [d["hr"] for d in DATA_HISTORY],
        "motion": [d["motion"] for d in DATA_HISTORY]
    })

# -------------------------
# MODEL RETRAIN (STEP LOOP)
# -------------------------
@app.route("/retrain", methods=["POST"])
def retrain():
    steps = retrain_model_with_steps()
    return jsonify({"steps": steps})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
