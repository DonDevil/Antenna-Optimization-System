# utils.py
import numpy as np
import math
from ai_core.ai_config import C

def effective_eps(eps_r, W, h):
    return (eps_r + 1)/2 + (eps_r - 1)/2 * (1 + 12*h/W)**-0.5

def rect_patch_L_from_freq(f, eps_r, h, W):
    eps_eff = effective_eps(eps_r, W, h)
    delta_L = 0.412 * h * ((eps_eff + 0.3)*(W/h + 0.264)) / ((eps_eff - 0.258)*(W/h + 0.8))
    L = (C / (2 * f * math.sqrt(eps_eff))) - 2*delta_L
    return L, eps_eff

def bandwidth_estimate_patch(f, W, h, eps_r, feed_factor=1.0):
    BW_frac = (1.5 * h / W) * np.sqrt(eps_r)
    return BW_frac * f * feed_factor

def hz_to_ghz(hz): return hz/1e9
def hz_to_mhz(hz): return hz/1e6
def ghz_to_hz(ghz): return ghz*1e9
def mhz_to_hz(mhz): return mhz*1e6
