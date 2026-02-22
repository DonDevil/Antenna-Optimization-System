import os
import joblib
import numpy as np
import pandas as pd

from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from ai_core.ai_config import FAMILIES, RANDOM_SEED

FEEDBACK_FILE = r"feedback\ai_feedback.csv"
MODEL_PATH = r"feedback\ai_quick_retrain.save"
META_PATH = r".ai_retrain_meta"

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
    # Each parameter has independent correction based on antenna physics
    y = np.zeros((n, 5))
    y[:, 0] = -0.3 * df["err_Fr"].values    # param_0 (W): moderate effect on frequency
    y[:, 1] = -df["err_Fr"].values          # param_1 (L): direct effect on frequency
    y[:, 2] = -0.15 * df["err_BW"].values   # param_2 (feed_w): affects bandwidth
    y[:, 3] = 0.0                           # param_3 (substrate_h): fixed
    y[:, 4] = 0.0                           # param_4 (eps_r): fixed

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
