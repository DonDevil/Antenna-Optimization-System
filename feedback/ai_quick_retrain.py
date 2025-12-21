import os
import joblib
import numpy as np
import pandas as pd

from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from ai_core.ai_config import FAMILIES, RANDOM_SEED

FEEDBACK_FILE = r"feedback\ai_feedback_mode2.csv"
MODEL_PATH = r"feedback\ai_quick_retrain.save"
META_PATH = r".ai_retrain_meta_mode2"

RETRAIN_MIN_SAMPLES = 30
RETRAIN_EVERY = 10


def quick_retrain():
    if not os.path.exists(FEEDBACK_FILE):
        return False

    df = pd.read_csv(FEEDBACK_FILE).dropna()
    n = len(df)

    if n < RETRAIN_MIN_SAMPLES:
        return False

    last_trained = 0
    if os.path.exists(META_PATH):
        try:
            last_trained = int(open(META_PATH).read().strip())
        except Exception:
            last_trained = 0

    if (n - last_trained) < RETRAIN_EVERY:
        return False

    # ---------------------------------
    # Feature engineering
    # ---------------------------------

    fam_to_id = {f: i for i, f in enumerate(FAMILIES)}
    df["family_id"] = df["family"].map(fam_to_id)

    df["err_Fr"] = df["actual_Fr_GHz"] - df["target_Fr_GHz"]
    df["err_BW"] = df["actual_BW_MHz"] - df["target_BW_MHz"]

    X_cols = (
        ["family_id", "target_Fr_GHz", "target_BW_MHz"]
        + [f"param_{i}" for i in range(5)]
        + ["err_Fr", "err_BW"]
    )

    # Target: parameter correction (negative error direction)
    y = np.zeros((n, 5))
    y[:, 0] = -df["err_Fr"].values
    y[:, 1] = -df["err_Fr"].values
    y[:, 2] = -0.1 * df["err_BW"].values
    y[:, 3] = 0.0
    y[:, 4] = 0.0

    X = df[X_cols].values

    # ---------------------------------
    # Normalization
    # ---------------------------------

    X_scaler = StandardScaler()
    y_scaler = StandardScaler()

    Xn = X_scaler.fit_transform(X)
    yn = y_scaler.fit_transform(y)

    # ---------------------------------
    # Train correction model
    # ---------------------------------

    model = MLPRegressor(
        hidden_layer_sizes=(128, 64),
        max_iter=600,
        random_state=RANDOM_SEED,
        early_stopping=True
    )

    model.fit(Xn, yn)

    joblib.dump(
        {
            "sk_model": model,
            "X_mean": X_scaler.mean_,
            "X_std": X_scaler.scale_,
            "y_mean": y_scaler.mean_,
            "y_std": y_scaler.scale_,
            "feature_cols": X_cols
        },
        MODEL_PATH
    )

    with open(META_PATH, "w") as f:
        f.write(str(n))

    print(f"[quick_retrain] correction model trained on {n} samples")

    return True


if __name__ == "__main__":
    quick_retrain()
