# trainers/train_inverse_family.py
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

for fam in FAMILIES:
    df_f = df[df['family'] == fam].copy()
    if len(df_f) < 50:
        print(f"[train_inverse] skipping {fam}: not enough samples")
        continue

    X = df_f[['freq_Hz', 'bandwidth_Hz']].values
    # convert to GHz / MHz
    X[:,0] = X[:,0] / 1e9
    X[:,1] = X[:,1] / 1e6

    # output: param_a, param_b, feed_width_m, substrate_h, eps_r
    y = df_f[['param_a', 'param_b', 'feed_width_m', 'substrate_h', 'eps_r']].values

    scalerX = StandardScaler()
    scalerY = StandardScaler()
    Xs = scalerX.fit_transform(X)
    ys = scalerY.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(Xs, ys, test_size=TRAIN_TEST_SPLIT, random_state=RANDOM_SEED)

    model = Sequential([
        Dense(256, activation='relu', input_shape=(Xs.shape[1],)),
        Dense(128, activation='relu'),
        Dense(64, activation='relu'),
        Dense(y.shape[1])
    ])
    model.compile(optimizer='adam', loss=MeanSquaredError())

    print(f"[train_inverse] training inverse model for {fam} on {len(df_f)} samples")
    model.fit(X_train, y_train, epochs=INVERSE_EPOCHS, batch_size=BATCH_SIZE, validation_split=0.15)

    loss = model.evaluate(X_test, y_test)
    if PRINT_ERROR:
        print(f"[train_inverse] test loss for inverse {fam}: {loss}")

    model_path = MODELS_DIR / f"inverse_{fam}.keras"
    model.save(str(model_path))
    joblib.dump(scalerX, str(MODELS_DIR / f"inverse_{fam}_scalerX.save"))
    joblib.dump(scalerY, str(MODELS_DIR / f"inverse_{fam}_scalerY.save"))
    print(f"[train_inverse] saved inverse model and scalers for {fam}")
