import numpy as np
import joblib
from tensorflow.keras.models import load_model

WINDOW = 10

LABEL_MAP_REV = {
    0: "healthy",
    1: "fever",
    2: "hypothermia",
    3: "lethargy"
}

model = load_model("cattle_cnn_model.h5")
scaler = joblib.load("scaler.save")

buffer = []

def cnn_predict(temp, hr):
    global buffer

    scaled = scaler.transform([[temp, hr]])
    buffer.append(scaled[0])

    if len(buffer) < WINDOW:
        return None

    if len(buffer) > WINDOW:
        buffer.pop(0)

    X = np.array(buffer).reshape(1, WINDOW, 2)
    probs = model.predict(X)[0]
    class_id = np.argmax(probs)

    return LABEL_MAP_REV[class_id]
