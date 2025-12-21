# cst_interface/cst_driver_mode2.py
from cst_interface.cst_driver import CSTDriver as BaseCSTDriver
from ai_core.ai_config import DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R

class CSTDriverMode2(BaseCSTDriver):
    def __init__(self, cst_project=None):
        super().__init__(cst_project=cst_project)

    def _mm(self, meters):
        return float(meters * 1e3)

    def _lambda_mm(self, freq_GHz):
        return 300.0 / float(freq_GHz)

    # ------------------------
    # Microstrip patches
    # ------------------------
    def build_patch_rect(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [W, L, feed_width, substrate_h, eps_r]
        W, L, feed_w, sub_h, eps_r = params
        S_h = sub_h if sub_h > 0 else DEFAULT_SUBSTRATE_H
        lam = self._lambda_mm(freq_GHz)
        margin = lam/4.0
        S_W = self._mm(W) + margin
        S_L = self._mm(L) + margin

        self.run_command("define brick", solid_name="substrate",
                         component_name="component1", material=substrate_name,
                         x1=f"-{S_W/2:.4f}", x2=f"{S_W/2:.4f}",
                         y1=f"-{S_L/2:.4f}", y2=f"{S_L/2:.4f}",
                         z1="0", z2=f"{self._mm(S_h):.4f}")
        self.run_command("define brick", solid_name="patch",
                         component_name="component1", material=conductor_name,
                         x1=f"-{self._mm(W)/2:.4f}", x2=f"{self._mm(W)/2:.4f}",
                         y1=f"-{self._mm(L)/2:.4f}", y2=f"{self._mm(L)/2:.4f}",
                         z1=f"{self._mm(S_h):.4f}", z2=f"{self._mm(S_h + 0.035):.4f}")
        self.run_command("define brick", solid_name="feed",
                         component_name="component1", material=conductor_name,
                         x1=f"-{self._mm(feed_w)/2:.4f}", x2=f"{self._mm(feed_w)/2:.4f}",
                         y1=f"-{self._mm(L)/2:.4f}", y2=f"{self._mm(L)/2:.4f}",
                         z1=f"{self._mm(S_h):.4f}", z2=f"{self._mm(S_h + 0.035):.4f}")
        self.run_command("define boundary")
        self.run_command("set solver freq range", resonant_frequency1=float(freq_GHz)-1.0, resonant_frequency2=float(freq_GHz)+1.0)
        self.run_command("pick face", component_name="component1", solid_name="feed")
        self.run_command("select port", Xrange=f"-{self._mm(feed_w)/2:.4f}", XrangeEnd=f"{self._mm(feed_w)/2:.4f}",
                         Yrange="0", YrangeEnd="0", Zrange=f"{self._mm(S_h):.4f}", ZrangeEnd=f"{(self._mm(S_h)+0.035):.4f}")
        #self.run_command("run Solver")

    def build_patch_circ(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [radius, feed_width, substrate_h, eps_r, extra]
        r, feed_w, sub_h, eps_r, extra = params
        S_h = sub_h if sub_h>0 else DEFAULT_SUBSTRATE_H
        lam = self._lambda_mm(freq_GHz)
        margin = lam/4.0
        S_W = self._mm(2*r) + margin
        S_L = self._mm(2*r) + margin
        # approximate circular patch with a square brick for initial tests
        self.run_command("define brick", solid_name="substrate", component_name="component1", material=substrate_name,
                         x1=f"-{S_W/2:.4f}", x2=f"{S_W/2:.4f}", y1=f"-{S_L/2:.4f}", y2=f"{S_L/2:.4f}",
                         z1="0", z2=f"{self._mm(S_h):.4f}")
        self.run_command("define brick", solid_name="patch", component_name="component1", material=conductor_name,
                         x1=f"-{self._mm(2*r)/2:.4f}", x2=f"{self._mm(2*r)/2:.4f}",
                         y1=f"-{self._mm(2*r)/2:.4f}", y2=f"{self._mm(2*r)/2:.4f}",
                         z1=f"{self._mm(S_h):.4f}", z2=f"{self._mm(S_h + 0.035):.4f}")
        self.run_command("define boundary")
        self.run_command("run Solver")

    def build_patch_meander(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [W,L,meander_depth,feed_w,eps_r]
        W, L, meander_depth, feed_w, eps_r = params
        # simplified: create rectangle patch and flag a future operation to apply meander cuts
        self.build_patch_rect(freq_GHz, [W,L,feed_w,DEFAULT_SUBSTRATE_H,eps_r], substrate_name, conductor_name)
        # placeholder: future: apply boolean cuts using meander parameter
        # self.run_command("apply meander cut", depth=meander_depth)

    def build_patch_u_slot(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [W,L,slot_depth,feed_w,eps_r]
        W,L,slot_depth,feed_w,eps_r = params
        self.build_patch_rect(freq_GHz, [W,L,feed_w,DEFAULT_SUBSTRATE_H,eps_r], substrate_name, conductor_name)
        # placeholder: create U-slot geometry with slot_depth
        # self.run_command("create USlot", ...)

    def build_patch_e_shape(self, freq_GHz, params, substrate_name, conductor_name):
        W,L,slot_depth,feed_w,eps_r = params
        self.build_patch_rect(freq_GHz, [W,L,feed_w,DEFAULT_SUBSTRATE_H,eps_r], substrate_name, conductor_name)
        # placeholder for E-shape cuts

    # ------------------------
    # Monopole / Dipole / CPW / Slot / Vivaldi
    # ------------------------
    def build_monopole(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [length, width, _, substrate_h, eps_r]
        L, W, _, sub_h, eps_r = params
        S_h = sub_h if sub_h>0 else DEFAULT_SUBSTRATE_H
        S_W = max(self._mm(L)*2, 60.0)
        S_L = max(self._mm(L)*2, 60.0)
        self.run_command("define brick", solid_name="substrate", component_name="component1", material=substrate_name,
                         x1=f"-{S_W/2:.4f}", x2=f"{S_W/2:.4f}", y1=f"-{S_L/2:.4f}", y2=f"{S_L/2:.4f}",
                         z1="0", z2=f"{self._mm(S_h):.4f}")
        self.run_command("define brick", solid_name="monopole", component_name="component1", material=conductor_name,
                         x1=f"-{self._mm(W)/2:.4f}", x2=f"{self._mm(W)/2:.4f}",
                         y1=f"-{self._mm(W)/2:.4f}", y2=f"{self._mm(W)/2:.4f}",
                         z1=f"{self._mm(S_h):.4f}", z2=f"{self._mm(S_h+L):.4f}")
        self.run_command("define boundary")
        self.run_command("run Solver")

    def build_dipole(self, freq_GHz, params, substrate_name, conductor_name):
        L, W, _, sub_h, eps_r = params
        S_W = max(self._mm(L)*2, 60.0)
        S_L = max(self._mm(L)*2, 60.0)
        self.run_command("define brick", solid_name="substrate", component_name="component1", material=substrate_name,
                         x1=f"-{S_W/2:.4f}", x2=f"{S_W/2:.4f}", y1=f"-{S_L/2:.4f}", y2=f"{S_L/2:.4f}",
                         z1="0", z2=f"{0.1:.4f}")
        arm_len = L/2.0
        self.run_command("define brick", solid_name="dipole_left", component_name="component1", material=conductor_name,
                         x1=f"-{self._mm(W)/2:.4f}", x2=f"{self._mm(W)/2:.4f}", y1=f"-{self._mm(arm_len):.4f}", y2="0.0",
                         z1="0.0", z2=f"{0.035:.4f}")
        self.run_command("define brick", solid_name="dipole_right", component_name="component1", material=conductor_name,
                         x1=f"-{self._mm(W)/2:.4f}", x2=f"{self._mm(W)/2:.4f}", y1="0.0", y2=f"{self._mm(arm_len):.4f}",
                         z1="0.0", z2=f"{0.035:.4f}")
        self.run_command("define boundary")
        self.run_command("run Solver")

    def build_cpw_uwb(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [W, _, _, sub_h, eps_r]
        W, *_ = params
        # placeholder: CPW generalized geometry, create substrate & CPW center conductor
        self.build_patch_rect(freq_GHz, [W, W/4.0, 0.002, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R], substrate_name, conductor_name)
        # more elaborate CPW geometry to be added

    def build_slot(self, freq_GHz, params, substrate_name, conductor_name):
        # params: [slot_w, _, _, sub_h, eps_r]
        slot_w = params[0]
        self.build_patch_rect(freq_GHz, [slot_w*4, slot_w*4, 0.002, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R], substrate_name, conductor_name)
        # placeholder: create slot cutout

    def build_vivaldi(self, freq_GHz, params, substrate_name, conductor_name):
        mouth, *_ = params
        self.build_patch_rect(freq_GHz, [mouth, mouth*0.6, 0.002, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R], substrate_name, conductor_name)
        # placeholder: exponential taper generation to be added

    # ------------------------
    # Dispatcher
    # ------------------------
    def create_and_run(self, family, freq_GHz, params, substrate_name, conductor_name):
        """
        family: string in FAMILIES
        params: list of length >=5 (param_a,param_b,feed_w,substrate_h,eps_r)
        """
        if family == "patch_rect":
            return self.build_patch_rect(freq_GHz, params, substrate_name, conductor_name)
        if family == "patch_circ":
            return self.build_patch_circ(freq_GHz, params, substrate_name, conductor_name)
        if family == "patch_meander":
            return self.build_patch_meander(freq_GHz, params, substrate_name, conductor_name)
        if family == "patch_u-slot":
            return self.build_patch_u_slot(freq_GHz, params, substrate_name, conductor_name)
        if family == "patch_e-shape":
            return self.build_patch_e_shape(freq_GHz, params, substrate_name, conductor_name)
        if family == "monopole":
            return self.build_monopole(freq_GHz, params, substrate_name, conductor_name)
        if family == "dipole":
            return self.build_dipole(freq_GHz, params, substrate_name, conductor_name)
        if family == "cpw_uwb":
            return self.build_cpw_uwb(freq_GHz, params, substrate_name, conductor_name)
        if family == "slot":
            return self.build_slot(freq_GHz, params, substrate_name, conductor_name)
        if family == "vivaldi":
            return self.build_vivaldi(freq_GHz, params, substrate_name, conductor_name)
        # fallback
        raise ValueError("Unsupported family: " + family)
