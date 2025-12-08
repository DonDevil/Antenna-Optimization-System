# feedback/ai_quick_retrain.py
import pandas as pd
import joblib
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np
from ai_core.ai_config import *
import os

FEEDBACK_FILE = r"feedback\ai_feedback_mode2.csv"
META_PATH = ".ai_retrain_meta_mode2"

def quick_retrain():
    if not os.path.exists(FEEDBACK_FILE):
        print("No feedback file.")
        return False
    df = pd.read_csv(FEEDBACK_FILE)
    df = df.dropna()
    n = len(df)
    if n < RETRAIN_MIN_SAMPLES:
        print("Not enough feedback samples:", n)
        return False
    last = 0
    if os.path.exists(META_PATH):
        try:
            last = int(open(META_PATH).read().strip())
        except Exception:
            last = 0
    if (n - last) < RETRAIN_EVERY:
        print("Not enough new samples since last retrain.")
        return False

    # We'll train a global quick-correct model mapping [family_id, target_Fr, target_BW, param_0..param_4] -> actual_Fr_GHz, actual_BW_MHz
    # Convert family to integer
    fam_to_id = {name:i for i,name in enumerate(FAMILIES)}
    df['family_id'] = df['family'].map(fam_to_id)

    X_cols = ['family_id', 'target_Fr_GHz', 'target_BW_MHz'] + [f'param_{i}' for i in range(5)]
    y_cols = ['actual_Fr_GHz', 'actual_BW_MHz']

    X = df[X_cols].values
    y = df[y_cols].values

    X_mean = X.mean(axis=0); X_std = X.std(axis=0) + 1e-9
    Xn = (X - X_mean) / X_std
    y_mean = y.mean(axis=0); y_std = y.std(axis=0) + 1e-9
    yn = (y - y_mean) / y_std

    model = MLPRegressor(hidden_layer_sizes=(256,128), max_iter=800, random_state=RANDOM_SEED)
    model.fit(Xn, yn)
    joblib.dump({
        "sk_model": model,
        "X_mean": X_mean, "X_std": X_std,
        "y_mean": y_mean, "y_std": y_std
    }, r"feedback\ai_quick_retrain.save")
    open(META_PATH, "w").write(str(n))
    print("Saved quick retrain model on", n, "samples.")
    return True

if __name__ == "__main__":
    quick_retrain()
