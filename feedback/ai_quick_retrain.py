import os
import joblib
import numpy as np
import pandas as pd

from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from ai_core.ai_config import FAMILIES, RANDOM_SEED

# Use absolute paths based on script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, "ai_feedback.csv")
MODEL_PATH = os.path.join(SCRIPT_DIR, "ai_quick_retrain.save")
META_PATH = os.path.join(PROJECT_ROOT, ".ai_retrain_meta")

RETRAIN_MIN_SAMPLES = 30
RETRAIN_EVERY = 30


def quick_retrain():
    if not os.path.exists(FEEDBACK_FILE):
        print(f"[quick_retrain] Feedback file not found: {FEEDBACK_FILE}")
        return False

    try:
        df = pd.read_csv(FEEDBACK_FILE).dropna()
    except Exception as e:
        print(f"[quick_retrain] Error reading feedback file: {e}")
        return False
    
    n = len(df)
    print(f"[quick_retrain] Feedback file has {n} samples")
    
    # Validate measurement quality
    invalid_mask = (df['actual_Fr_GHz'] <= 0) | (df['actual_BW_MHz'] <= 0)
    n_invalid = invalid_mask.sum()
    if n_invalid > 0:
        print(f"[quick_retrain] WARNING: {n_invalid} rows with invalid measurements (Fr<=0 or BW<=0)")
        df = df[~invalid_mask]
        n = len(df)
        print(f"[quick_retrain] Using {n} valid samples after filtering")

    if n < RETRAIN_MIN_SAMPLES:
        print(f"[quick_retrain] Need {RETRAIN_MIN_SAMPLES} total samples to start retraining (have {n})")
        return False

    last_trained = 0
    if os.path.exists(META_PATH):
        try:
            last_trained = int(open(META_PATH).read().strip())
        except Exception as e:
            print(f"[quick_retrain] Could not read meta file: {e}")
            last_trained = 0

    new_samples = n - last_trained
    print(f"[quick_retrain] New samples since last training: {new_samples} (need {RETRAIN_EVERY})")
    
    if new_samples < RETRAIN_EVERY:
        return False

    # ---------------------------------
    # Feature engineering
    # ---------------------------------

    fam_to_id = {f: i for i, f in enumerate(FAMILIES)}
    df["family_id"] = df["family"].map(fam_to_id)

    df["err_Fr"] = df["actual_Fr_GHz"] - df["target_Fr_GHz"]
    # Handle missing actual_BW_MHz (use 0 if not available)
    if "actual_BW_MHz" in df.columns:
        df["err_BW"] = df["actual_BW_MHz"] - df["target_BW_MHz"]
    else:
        df["err_BW"] = 0.0

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

    try:
        model.fit(Xn, yn)
    except Exception as e:
        print(f"[quick_retrain] Error during model training: {e}")
        return False

    try:
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
        print(f"[quick_retrain] Model saved to {MODEL_PATH}")
    except Exception as e:
        print(f"[quick_retrain] Error saving model: {e}")
        return False

    try:
        with open(META_PATH, "w") as f:
            f.write(str(n))
        print(f"[quick_retrain] Meta file updated: {n} samples")
    except Exception as e:
        print(f"[quick_retrain] Error writing meta file: {e}")
        return False

    print(f"[quick_retrain] ✓ Correction model trained on {n} samples ({new_samples} new)")

    return True


if __name__ == "__main__":
    quick_retrain()
