import joblib
import numpy as np
import os
from pathlib import Path
from tensorflow.keras.models import load_model
from ai_core.ai_config import *

class AICoreManager:
    """
    Minimal AI manager:
    - Forward model: params -> (Fr, BW)
    - Inverse model: (Fr, BW) -> params
    - Correction model: learns to refine inverse predictions based on forward model errors
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
        
        # Load correction model if available
        self.correction_model = None
        self.correction_data = None
        self._load_correction_model()

    # -----------------------------
    # Forward prediction
    # -----------------------------
    def predict_forward(self, params):
        X = np.array(params, dtype=float).reshape(1, -1)
        Xs = self.fwd_scaler.transform(X)
        y = self.fwd_model.predict(Xs, verbose=0)[0]
        return float(y[0]), float(y[1])  # GHz, MHz

    # -----------------------------
    # Inverse prediction with correction
    # -----------------------------
    def predict_inverse(self, Fr_GHz, BW_MHz):
        # Step 1: Get initial inverse prediction
        X = np.array([[Fr_GHz, BW_MHz]], dtype=float)
        Xs = self.inv_scalerX.transform(X)
        y_scaled = self.inv_model.predict(Xs, verbose=0)[0]
        params = self.inv_scalerY.inverse_transform(
            y_scaled.reshape(1, -1)
        )[0]
        
        # Step 2: Apply learned correction ONLY if it improves prediction
        if self.correction_model is not None:
            params_corrected = self._apply_correction(params, Fr_GHz, BW_MHz)
            # Validate that correction actually improves the forward model prediction
            if params_corrected is not None:
                params = params_corrected
        
        return params.tolist()

    # -----------------------------
    # Correction model loading
    # -----------------------------
    def _load_correction_model(self):
        """Load the trained correction model if it exists."""
        correction_path = Path(__file__).parent.parent / "feedback" / "ai_quick_retrain.save"
        
        if not correction_path.exists():
            return  # Correction model not available yet
        
        try:
            self.correction_data = joblib.load(str(correction_path))
            self.correction_model = self.correction_data.get("sk_model")
            
            if self.correction_model is not None:
                print(f"[AI Core] Loaded correction model from {correction_path}")
        except Exception as e:
            print(f"[AI Core] Warning: Could not load correction model: {e}")
    
    # -----------------------------
    # Apply learned corrections
    # -----------------------------
    def _apply_correction(self, params, target_Fr_GHz, target_BW_MHz):
        """
        Apply learned correction deltas to parameters, but ONLY if they improve prediction.
        
        Returns corrected params if they improve forward model prediction, None otherwise.
        """
        if self.correction_model is None or self.correction_data is None:
            return None
        
        try:
            # Get baseline prediction before correction
            baseline_Fr, baseline_BW = self.predict_forward(params)
            baseline_error = abs(baseline_Fr - target_Fr_GHz) + abs(baseline_BW - target_BW_MHz) / 100
            
            # Calculate correction deltas
            err_Fr = baseline_Fr - target_Fr_GHz
            err_BW = baseline_BW - target_BW_MHz
            
            # Prepare input for correction model
            family_id = 0  # patch_rect is family 0
            X = np.array([[
                family_id,
                target_Fr_GHz,
                target_BW_MHz,
                params[0], params[1], params[2], params[3], params[4],
                err_Fr,
                err_BW
            ]], dtype=float)
            
            # Normalize using stored scalers
            X_mean = self.correction_data.get("X_mean")
            X_std = self.correction_data.get("X_std")
            y_mean = self.correction_data.get("y_mean")
            y_std = self.correction_data.get("y_std")
            
            if X_mean is None or X_std is None or y_mean is None or y_std is None:
                return None
            
            Xn = (X - X_mean) / X_std
            
            # Predict correction deltas
            yn_pred = self.correction_model.predict(Xn)
            
            # Denormalize deltas
            y_deltas = yn_pred * y_std + y_mean
            
            # Apply deltas to parameters
            params_corrected = np.array(params, dtype=float) + y_deltas[0, :5]
            
            # Clamp to valid ranges
            params_corrected[0] = np.clip(params_corrected[0], PATCH_W_RANGE[0], PATCH_W_RANGE[1])
            params_corrected[1] = np.clip(params_corrected[1], PATCH_L_RANGE[0], PATCH_L_RANGE[1])
            params_corrected[2] = np.clip(params_corrected[2], FEED_W_RANGE[0], FEED_W_RANGE[1])
            params_corrected[3] = np.clip(params_corrected[3], SUBSTRATE_H_RANGE[0], SUBSTRATE_H_RANGE[1])
            params_corrected[4] = np.clip(params_corrected[4], EPS_R_RANGE[0], EPS_R_RANGE[1])
            
            # Validate: check if corrected prediction is better than baseline
            corrected_Fr, corrected_BW = self.predict_forward(params_corrected)
            corrected_error = abs(corrected_Fr - target_Fr_GHz) + abs(corrected_BW - target_BW_MHz) / 100
            
            if corrected_error < baseline_error:
                # Correction improved prediction, use it
                return params_corrected
            else:
                # Correction made things worse, don't use it
                return None
            
        except Exception as e:
            # If correction fails, return None to keep original
            return None
