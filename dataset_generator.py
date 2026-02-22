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
            rows.append([fam, f, BW, W, L, feed_w, DEFAULT_SUBSTRATE_H, DEFAULT_EPS_R, feed_type])
        
    cols = [
        "family", "freq_Hz", "bandwidth_Hz",
        "param_a", "param_b", "feed_width_m",
        "substrate_h", "eps_r", "extra"
    ]
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(DATASET_PATH, index=False)
    print("Saved dataset to:", DATASET_PATH, "rows:", len(df))
    return df

if __name__ == "__main__":
    generate_mode2_dataset()
