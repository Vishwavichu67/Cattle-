import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense
from sklearn.preprocessing import MinMaxScaler
import time

DATASET = "cow_health_iot_dataset_100rows.csv"
WINDOW = 10

def retrain_model_with_steps():
    steps = []

    steps.append("📂 Loading dataset")
    df = pd.read_csv(DATASET)
    time.sleep(1)

    steps.append("🔄 Preprocessing data")
    X = df[['temperature_celsius', 'heart_rate_bpm']].values
    y_raw = df['health_status'].values

    label_map = {
        "healthy": 0,
        "fever": 1,
        "hypothermia": 2,
        "lethargy": 3
    }
    y = np.array([label_map[v] for v in y_raw])

    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)
    time.sleep(1)

    steps.append("🧠 Building CNN model")
    X_seq, y_seq = [], []
    for i in range(len(X) - WINDOW):
        X_seq.append(X[i:i+WINDOW])
        y_seq.append(y[i+WINDOW])

    X_seq = np.array(X_seq)
    y_seq = np.eye(4)[y_seq]
    time.sleep(1)

    model = Sequential([
        Conv1D(32, 3, activation='relu', input_shape=(WINDOW, 2)),
        MaxPooling1D(2),
        Flatten(),
        Dense(64, activation='relu'),
        Dense(4, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    steps.append("🏋️ Training CNN model")
    model.fit(X_seq, y_seq, epochs=10, batch_size=16, verbose=0)
    time.sleep(1)

    steps.append("💾 Saving model")
    model.save("cattle_cnn_model.h5")
    joblib.dump(scaler, "scaler.save")
    time.sleep(1)

    steps.append("✅ Training completed successfully")

    return steps
