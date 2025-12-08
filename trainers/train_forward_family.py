# trainers/train_forward_family.py
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from ai_config import *
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.losses import MeanSquaredError

MODELS_DIR.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(DATASET_PATH)

# For each family: build X,y and train separate model
for fam in FAMILIES:
    df_f = df[df['family'] == fam].copy()
    if len(df_f) < 50:
        print(f"[train_forward] skipping {fam}: not enough samples ({len(df_f)})")
        continue

    # Define features depending on family:
    # We'll use param_a, param_b, feed_width_m, substrate_h, eps_r
    X = df_f[['param_a', 'param_b', 'feed_width_m', 'substrate_h', 'eps_r']].values
    y = df_f[['freq_Hz', 'bandwidth_Hz']].values
    # convert targets to convenient units
    y[:,0] = y[:,0] / 1e9  # GHz
    y[:,1] = y[:,1] / 1e6  # MHz

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(Xs, y, test_size=TRAIN_TEST_SPLIT, random_state=RANDOM_SEED)

    model = Sequential([
        Dense(256, activation='relu', input_shape=(X.shape[1],)),
        Dense(128, activation='relu'),
        Dense(64, activation='relu'),
        Dense(2)
    ])
    model.compile(optimizer='adam', loss=MeanSquaredError())

    print(f"[train_forward] training forward model for {fam} on {len(df_f)} samples")
    model.fit(X_train, y_train, epochs=FORWARD_EPOCHS, batch_size=BATCH_SIZE, validation_split=0.15)

    loss = model.evaluate(X_test, y_test)
    if PRINT_ERROR:
        print(f"[train_forward] test loss for {fam}: {loss}")

    # save
    model_path = MODELS_DIR / f"forward_{fam}.keras"
    model.save(str(model_path))
    joblib.dump(scaler, str(MODELS_DIR / f"forward_{fam}_scaler.save"))
    print(f"[train_forward] saved forward model and scaler for {fam}")
