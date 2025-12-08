# dataset_generator_mode2.py
import numpy as np
import pandas as pd
from ai_core.ai_config import *
from utils import rect_patch_L_from_freq, bandwidth_estimate_patch, effective_eps

def generate_mode2_dataset(samples=SAMPLES, seed=RANDOM_SEED):
    np.random.seed(seed)
    rows = []
    families = np.random.choice(FAMILIES, samples)
    for fam in families:
        f = np.random.uniform(1.0e9, 6.0e9)  # Hz
        if fam == "patch_rect":
            W = np.random.uniform(*PATCH_W_RANGE)
            L, eps_eff = rect_patch_L_from_freq(f, DEFAULT_EPS_R, DEFAULT_SUBSTRATE_H, W)
            feed_w = np.random.uniform(*FEED_W_RANGE)
            feed_type = np.random.randint(0, 4)
            BW = bandwidth_estimate_patch(f, W, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_factor=1.0 + (feed_type-1)*0.05)
            rows.append([fam, f, BW, W, L, eps_eff, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_w, feed_type])
        elif fam == "patch_circ":
            r = np.random.uniform(*CIRC_RADIUS_RANGE)
            # quick circular patch heuristic — map radius to f roughly
            # Use W ≈ 2r for bandwidth heuristics
            BW = bandwidth_estimate_patch(f, 2*r, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_factor=1.02)
            rows.append([fam, f, BW, r, 0.0, effective_eps(DEFAULT_EPS_R, 2*r, DEFAULT_SUBSTRATE_H), DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, np.random.uniform(*FEED_W_RANGE), 0])
        elif fam == "patch_meander":
            W = np.random.uniform(*PATCH_W_RANGE)
            L, eps_eff = rect_patch_L_from_freq(f, DEFAULT_EPS_R, DEFAULT_SUBSTRATE_H, W)
            meander = np.random.uniform(*MEANDER_DEPTH_RANGE)
            feed_w = np.random.uniform(*FEED_W_RANGE)
            BW = bandwidth_estimate_patch(f, W, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_factor=1.08)
            rows.append([fam, f, BW, W, L, eps_eff, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_w, meander])
        elif fam == "patch_u-slot" or fam == "patch_e-shape":
            W = np.random.uniform(*PATCH_W_RANGE)
            L, eps_eff = rect_patch_L_from_freq(f, DEFAULT_EPS_R, DEFAULT_SUBSTRATE_H, W)
            slot_depth = np.random.uniform(1e-3, 8e-3)
            feed_w = np.random.uniform(*FEED_W_RANGE)
            BW = bandwidth_estimate_patch(f, W, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_factor=1.1)
            rows.append([fam, f, BW, W, L, eps_eff, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_w, slot_depth])
        elif fam == "monopole":
            L = np.random.uniform(*MONOPOLE_LENGTH_RANGE)
            W = np.random.uniform(*MONOPOLE_WIDTH_RANGE)
            BW = 0.03 * f
            rows.append([fam, f, BW, L, W, 0.0, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, 0.0, 0])
        elif fam == "dipole":
            L = np.random.uniform(*DIPOLE_LENGTH_RANGE)
            W = np.random.uniform(*DIPOLE_WIDTH_RANGE)
            BW = 0.02 * f
            rows.append([fam, f, BW, L, W, 0.0, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, 0.0, 0])
        elif fam == "cpw_uwb":
            W = np.random.uniform(10e-3, 80e-3)
            BW = 0.25 * f  # UWB wide BW heuristic
            rows.append([fam, f, BW, W, 0.0, 0.0, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, 0.0, 0])
        elif fam == "slot":
            slot_w = np.random.uniform(1e-3, 20e-3)
            BW = 0.08 * f
            rows.append([fam, f, BW, slot_w, 0.0, 0.0, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, 0.0, 0])
        elif fam == "vivaldi":
            mouth = np.random.uniform(10e-3, 120e-3)
            BW = 0.4 * f
            rows.append([fam, f, BW, mouth, 0.0, 0.0, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, 0.0, 0])
        else:
            # placeholder generic row
            rows.append([fam, f, 0.01*f, 0.02, 0.02, 0.0, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, 0.001, 0])

    cols = [
        "family", "freq_Hz", "bandwidth_Hz",
        "param_a", "param_b", "eps_eff",
        "substrate_h", "eps_r", "feed_width_m", "extra"
    ]
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(DATASET_PATH, index=False)
    print("Saved dataset to:", DATASET_PATH, "rows:", len(df))
    return df

if __name__ == "__main__":
    generate_mode2_dataset()
