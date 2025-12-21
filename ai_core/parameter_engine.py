import os
import time
import numpy as np
import joblib

from ai_core.ai_core_manager import AICoreManager
from ai_core.ai_config import (
    FAMILIES,
    PATCH_W_RANGE, PATCH_L_RANGE, FEED_W_RANGE,
    MONOPOLE_LENGTH_RANGE, MONOPOLE_WIDTH_RANGE,
    DIPOLE_LENGTH_RANGE, DIPOLE_WIDTH_RANGE,
)

CORRECTION_MODEL_PATH = r"feedback\ai_quick_retrain.save"

class ParameterEngine:
    def __init__(
            self,
            alpha=0.3, # correction step size (ex. 0.2 or 0.4)
            exploration_sigma=0.03, # ultiplicative noise level
            reload_interval=300 # seconds between correction model reloads
    ):
        self.ai_mgr = AICoreManager()
        self.alpha = float(alpha)
        self.exploration_sigma = float(exploration_sigma)
        self.reload_interval = reload_interval

        self.family_to_id = {f: i for i, f in enumerate(FAMILIES)}

        self._correction_model = None
        self._last_reload_time = 0.0
        self._load_correction_model(force=True)
    
    #----------------------------------------------------------------------
    #       Internal Methods
    #----------------------------------------------------------------------

    def _load_correction_model(self, force=False):
        # load or reload the correction model if enough time has passed
        now = time.time()
        if not force and (now - self._last_reload_time) < self.reload_interval:
            return
        
        self._last_reload_time = now
        self._correction_model = None

        if os.path.exists(CORRECTION_MODEL_PATH):
            try:
                self._correction_model = joblib.load(CORRECTION_MODEL_PATH)
            except:
                self._correction_model = None
    
    def _apply_exploration(self, params):
        # Small multiplicative noise to avoid stagnation

        noise = np.random.normal(
            loc=0.0,
            scale=self.exploration_sigma,
            size=len(params)
        )
        return params * (1.0 + noise)
    
    def _clamp_params(self, family, params):
        # Safety feature to limit cst crashes

        p = np.array(params, dtype = float)
        p = np.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0)

        # Normal Structure : [param_a, param_b, feed_width, substrate_h, eps_r]

        if family.startswith("patch"):
            p[0] = np.clip(p[0], *PATCH_W_RANGE)
            p[1] = np.clip(p[1], *PATCH_L_RANGE)
            p[2] = np.clip(p[2], *FEED_W_RANGE)
            p[3] = np.clip(p[3], 0.0005, 0.005)
            p[4] = np.clip([4], 2.0, 10.0)  # default eps_r=4.0
        
        elif family == "monopole":
            p[0] = np.clip(p[0], *MONOPOLE_LENGTH_RANGE)
            p[1] = np.clip(p[1], *MONOPOLE_WIDTH_RANGE)
            p[2] = 0.0  # feed_width not used
            p[3] = np.clip(p[3], 0.0005, 0.005)
            p[4] = np.clip([4], 2.0, 10.0)  
        
        elif family == "dipole":
            p[0] = np.clip(p[0], *DIPOLE_LENGTH_RANGE)
            p[1] = np.clip(p[1], *DIPOLE_WIDTH_RANGE)
            p[2] = 0.0  # feed_width not used
            p[3] = np.clip(p[3], 0.0005, 0.005)
            p[4] = np.clip([4], 2.0, 10.0)  
        
        else:
            # General fallback
            p[0:2] = np.clip(p[0:2], 1e-4, 0.2)
            p[2] = np.clip(p[2], 1e-4, 0.02)
            p[3] = np.clip(p[3], 0.0005, 0.005)
            p[4] = np.clip([4], 2.0, 10.0)
        
        return p.tolist()
    
    #----------------------------------------------------------------------
    #       Public Methods
    #----------------------------------------------------------------------

    def predict(
            self,
            family,
            target_Fr,
            target_BW,
            explore=True,
            apply_correction=True
    ):
        # Uniiversal parameter prediction method
        # Used By UI, Automatic Self Training Mode, Goal-Seeking Mode

        self._load_correction_model()

        base_params = self.ai_mgr.predict_inverse(
            family, target_Fr, target_BW
        )
        params = np.array(base_params, dtype=float)

        if apply_correction and self._correction_model is not None:
            try:
                fam_id = self.family_to_id[family]

                X = np.array([[
                    fam_id,
                    target_Fr,
                    target_BW,
                    *params
                ]])

                Xn = (X - self._correction_model['X_mean']) / self._correction_model['X_std']
                delta_norm = self._correction_model["sk_model"].predict(Xn)[0]
                delta = (
                    delta_norm * self._correction_model['y_std']
                    + self._correction_model['y_mean']
                )

                params = params + self.alpha * delta

            except Exception:
                pass
        
        if explore:
            params = self._apply_exploration(params)
        
        params = self._clamp_params(family, params)

        return params
    
    def refine(
            self,
            family,
            params,
            target_Fr,
            target_BW,
            actual_Fr,
            actual_BW,
            step_scale=1.0
    ):
        # Performs refinement step for goal-seeking mode, does not retrain models.
        # Only controlled parameter nudging.

        err_Fr = actual_Fr - target_Fr
        err_BW = actual_BW - target_BW

        direction = np.array([
            -err_Fr,
            -err_Fr,
            -err_BW * 0.1,
            0.0,
            0.0
        ])

        params = np.array(params, dtype=float)
        params = params + step_scale * self.alpha * direction

        params = self._clamp_params(family, params)
        return params
    
    def within_tolerance(
            self,
            target_Fr,
            target_BW,
            actual_Fr,
            actual_BW,
            tol_Fr,
            tol_BW
    ):
        # Goal Seeking Mode Stop Condition

        return (
            abs(actual_Fr - target_Fr) <= tol_Fr and
            abs(actual_BW - target_BW) <= tol_BW
        )