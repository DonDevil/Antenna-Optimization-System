import joblib
import numpy as np
from pathlib import Path
from tensorflow.keras.models import load_model
from ai_core.ai_config import *

class AICoreManager:
    """
    Minimal AI manager:
    - fui.new.pyorward model: params -> (Fr, BW)
    - inverse model: (Fr, BW) -> params
    """

    def __init__(self):
        self._load_models()

    def _load_models(self):
        fam = "patch_rect"

        self.fwd_model = load_model(MODELS_DIR / f"forward_{fam}.keras")
        self.inv_model = load_model(MODELS_DIR / f"inverse_{fam}.keras")

        self.fwd_scaler = joblib.load(MODELS_DIR / f"forward_{fam}_scaler.save")
        self.inv_scalerX = joblib.load(MODELS_DIR / f"inverse_{fam}_scalerX.save")
        self.inv_scalerY = joblib.load(MODELS_DIR / f"inverse_{fam}_scalerY.save")

    # -----------------------------
    # Forward prediction
    # -----------------------------
    def predict_forward(self, params):
        X = np.array(params, dtype=float).reshape(1, -1)
        Xs = self.fwd_scaler.transform(X)
        y = self.fwd_model.predict(Xs, verbose=0)[0]
        return float(y[0]), float(y[1])  # GHz, MHz

    # -----------------------------
    # Inverse prediction
    # -----------------------------
    def predict_inverse(self, Fr_GHz, BW_MHz):
        X = np.array([[Fr_GHz, BW_MHz]], dtype=float)
        Xs = self.inv_scalerX.transform(X)
        y_scaled = self.inv_model.predict(Xs, verbose=0)[0]
        params = self.inv_scalerY.inverse_transform(
            y_scaled.reshape(1, -1)
        )[0]
        return params.tolist()
