import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense
from tensorflow.keras.utils import to_categorical

# Load dataset
df = pd.read_csv("cow_health_iot_dataset_100rows.csv")

# Map text labels to numbers
LABEL_MAP = {
    "healthy": 0,
    "fever": 1,
    "hypothermia": 2,
    "lethargy": 3
}

df["label"] = df["health_status"].map(LABEL_MAP)

# Features and labels
X_raw = df[['temperature_celsius', 'heart_rate_bpm']].values
y_raw = df['label'].values

# Normalize
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X_raw)

# Create time-series windows
WINDOW = 10
X, y = [], []

for i in range(len(X_scaled) - WINDOW):
    X.append(X_scaled[i:i+WINDOW])
    y.append(y_raw[i+WINDOW])

X = np.array(X)
y = to_categorical(y, num_classes=4)

# CNN Model (MULTI-CLASS)
model = Sequential([
    Conv1D(32, 3, activation='relu', input_shape=(WINDOW, 2)),
    MaxPooling1D(2),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(4, activation='softmax')   # 4 classes
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Train
model.fit(X, y, epochs=25, batch_size=16, validation_split=0.2)

# Save
model.save("cattle_cnn_model.h5")
joblib.dump(scaler, "scaler.save")

print("✅ Multi-class CNN model trained successfully")
