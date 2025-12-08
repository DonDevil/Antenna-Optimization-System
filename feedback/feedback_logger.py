# feedback/feedback_logger.py
import csv
import os
import time
from ai_core.ai_config import *

FEEDBACK_FILE = r"feedback\ai_feedback_mode2.csv"
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

def ensure_header(num_params=5):
    if not os.path.exists(FEEDBACK_FILE):
        header = ["timestamp", "family", "target_Fr_GHz", "target_BW_MHz"]
        header += [f"param_{i}" for i in range(num_params)]
        header += ["substrate_h", "eps_r", "actual_Fr_GHz", "actual_BW_MHz", "S11_dB"]
        with open(FEEDBACK_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

def log_feedback(family, target_Fr, target_BW, params, actual_Fr, actual_BW, S11):
    """
    params: list length >=5 (param_a,param_b,feed_width,substrate_h,eps_r)
    """
    ensure_header(num_params=5)
    row = [time.time(), family, float(target_Fr), float(target_BW)]
    row += [float(params[i]) for i in range(5)]
    row += [float(params[3]), float(params[4]), float(actual_Fr), float(actual_BW), float(S11)]
    with open(FEEDBACK_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)
