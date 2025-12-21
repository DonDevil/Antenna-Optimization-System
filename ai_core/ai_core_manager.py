# ai_core/ai_core_manager.py
import joblib
import numpy as np
from pathlib import Path
from tensorflow.keras.models import load_model
from ai_core.ai_config import *
import scipy.optimize as opt

MODELS_DIR = Path(MODELS_DIR)

class FamilyModels:
    def __init__(self, family):
        self.family = family
        self.fwd_model = None
        self.fwd_scaler = None
        self.inv_model = None
        self.inv_scalerX = None
        self.inv_scalerY = None
        self.load_models()

    def load_models(self):
        fwd_path = MODELS_DIR / f"forward_{self.family}.keras"
        fwd_scaler = MODELS_DIR / f"forward_{self.family}_scaler.save"
        inv_path = MODELS_DIR / f"inverse_{self.family}.keras"
        inv_scalerX = MODELS_DIR / f"inverse_{self.family}_scalerX.save"
        inv_scalerY = MODELS_DIR / f"inverse_{self.family}_scalerY.save"

        if fwd_path.exists():
            self.fwd_model = load_model(str(fwd_path))
            if fwd_scaler.exists():
                self.fwd_scaler = joblib.load(str(fwd_scaler))
        if inv_path.exists():
            self.inv_model = load_model(str(inv_path))
            if inv_scalerX.exists():
                self.inv_scalerX = joblib.load(str(inv_scalerX))
            if inv_scalerY.exists():
                self.inv_scalerY = joblib.load(str(inv_scalerY))

class AICoreManager:
    """
    High-level wrapper. Instantiate once, call set_family() to switch.
    """
    def __init__(self):
        self.family_models = {}
        self.current = None

    def ensure_family(self, family):
        if family not in FAMILIES:
            raise ValueError("Unknown family: " + family)
        if family not in self.family_models:
            self.family_models[family] = FamilyModels(family)
        self.current = self.family_models[family]
        return self.current

    def predict_forward(self, family, params):
        """
        params: list/array of 5 floats: param_a, param_b, feed_width, substrate_h, eps_r
        returns: (Fr_GHz, BW_MHz)
        """
        fm = self.ensure_family(family)
        if fm.fwd_model is None or fm.fwd_scaler is None:
            raise RuntimeError(f"Forward model missing for {family}")
        X = np.array(params).reshape(1, -1)
        Xs = fm.fwd_scaler.transform(X)
        y = fm.fwd_model.predict(Xs)[0]
        return float(y[0]), float(y[1])

    def predict_inverse(self, family, Fr_GHz, BW_MHz):
        """
        returns: params vector in original units [param_a, param_b, feed_width, substrate_h, eps_r]
        """
        fm = self.ensure_family(family)
        if fm.inv_model is None or fm.inv_scalerX is None or fm.inv_scalerY is None:
            raise RuntimeError(f"Inverse model missing for {family}")
        X = np.array([[Fr_GHz, BW_MHz]])
        Xs = fm.inv_scalerX.transform(X)
        y_scaled = fm.inv_model.predict(Xs)[0]
        y = fm.inv_scalerY.inverse_transform(y_scaled.reshape(1, -1))[0]
        return [float(v) for v in y]

    def optimize_parameters(self, family, Fr_GHz, BW_MHz, bounds=None, x0=None):
        """
        Light-weight optimizer that refines inverse prediction using forward model.
        - bounds: list of (min,max) for the continuous optimization parameters (length <=5)
        - x0: initial guess (list)
        Returns dict: {'params': final_params, 'fun': value, 'success': bool}
        """
        fm = self.ensure_family(family)

        # initial guess from inverse model
        try:
            pred = self.predict_inverse(family, Fr_GHz, BW_MHz)
        except Exception:
            pred = [0]*5

        if x0 is None:
            x0 = pred

        # reduce to continuous variables only (we'll optimize the 5-vector directly)
        if bounds is None:
            # use generic bounds from ai_config
            if family.startswith("patch"):
                bounds = [PATCH_W_RANGE, PATCH_L_RANGE, FEED_W_RANGE, (0.0005, 0.003), (2.0, 10.0)]
            elif family == "monopole":
                bounds = [MONOPOLE_LENGTH_RANGE, MONOPOLE_WIDTH_RANGE, (0,0), (0.0005,0.003), (2,10)]
            elif family == "dipole":
                bounds = [DIPOLE_LENGTH_RANGE, DIPOLE_WIDTH_RANGE, (0,0), (0.0005,0.003), (2,10)]
            else:
                bounds = [(1e-4, 0.2)]*5

        def objective(x):
            # ensure length 5
            x_full = list(x) + [0]*(5-len(x))
            try:
                f_pred, bw_pred = self.predict_forward(family, x_full)
            except Exception:
                # penalize heavily if forward model missing
                return 1e6
            # Weighted error: freq error in GHz normalized by ~1 GHz, BW in MHz normalized by 100 MHz
            return (f_pred - Fr_GHz)**2 + 0.001*(bw_pred - BW_MHz)**2

        # only optimize continuous subset where bounds are not zero-length
        var_bounds = [b for b in bounds if b[0] != b[1]]
        x0_var = [x0[i] for i,b in enumerate(bounds) if b[0] != b[1]]
        try:
            res = opt.minimize(objective, x0_var, bounds=var_bounds, method='Powell', options={'maxiter':1000})
        except Exception as e:
            return {'success': False, 'error': str(e), 'params': x0}

        # reconstruct final vector
        final = []
        vi = 0
        for i,b in enumerate(bounds):
            if b[0] != b[1]:
                final.append(float(res.x[vi] if vi < len(res.x) else x0[i]))
                vi += 1
            else:
                final.append(float(b[0]))

        return {'success': res.success, 'fun': float(res.fun), 'params': final}
'''

from ai_core.ai_core_manager import AICoreManager
ai_mgr = AICoreManager()
params = ai_mgr.predict_inverse("patch_rect", 2.4, 100)          # inverse suggestion
fwd = ai_mgr.predict_forward("patch_rect", params)             # forward estimate
opt = ai_mgr.optimize_parameters("patch_rect", 2.4, 100)  
'''