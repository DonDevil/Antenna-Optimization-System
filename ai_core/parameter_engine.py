import numpy as np
from ai_core.ai_core_manager import AICoreManager
from ai_core.ai_config import *

class ParameterEngine:
    """
    Single responsibility:
    target specs -> valid antenna parameters
    """

    def __init__(self):
        self.ai = AICoreManager()

    def _clamp(self, p):
        p = np.array(p, dtype=float)

        p[0] = np.clip(p[0], *PATCH_W_RANGE)
        p[1] = np.clip(p[1], *PATCH_L_RANGE)
        p[2] = np.clip(p[2], *FEED_W_RANGE)
        p[3] = np.clip(p[3], *SUBSTRATE_H_RANGE)
        p[4] = np.clip(p[4], *EPS_R_RANGE)

        return p.tolist()

    def predict(self, family, target_Fr_GHz, target_BW_MHz):
        if family != "patch_rect":
            raise ValueError("Only 'patch_rect' is supported")

        params = self.ai.predict_inverse(
            float(target_Fr_GHz),
            float(target_BW_MHz)
        )

        return self._clamp(params)
