# feedback/feedback_logger.py
import csv
import os
import time
from ai_core.ai_config import *

FEEDBACK_FILE = r"feedback\ai_feedback.csv"
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

def ensure_header(num_params=5):
    if not os.path.exists(FEEDBACK_FILE):
        header = ["timestamp", "family", "target_Fr_GHz", "target_BW_MHz"]
        header += [f"param_{i}" for i in range(num_params)]
        header += ["actual_Fr_GHz", "actual_BW_MHz", "S11_dB"]
        with open(FEEDBACK_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

def log_feedback(family, target_Fr, target_BW, params, actual_Fr, actual_BW, S11):
    """
    params: list length >=5 (param_a,param_b,feed_width,substrate_h,eps_r)
    
    Validates that measurements are physically reasonable before logging.
    Returns True if logged, False if validation failed.
    """
    ensure_header(num_params=5)
    
    # Validate actual measurements
    if actual_Fr <= 0:
        print(f"[feedback_logger] ERROR: Invalid actual_Fr={actual_Fr} (must be > 0), skipping feedback")
        return False
    if actual_BW <= 0:
        print(f"[feedback_logger] ERROR: Invalid actual_BW={actual_BW} (must be > 0), skipping feedback")
        return False
    if S11 >= 0:
        print(f"[feedback_logger] WARNING: S11={S11} dB (typically negative), logging anyway")
    
    # Sanity check on ranges (optional, adjust as needed)
    if actual_Fr < 0.1 or actual_Fr > 100:  # 100 MHz to 100 GHz range
        print(f"[feedback_logger] WARNING: actual_Fr={actual_Fr} GHz is outside typical range (0.1-100)")
    if actual_BW < 1 or actual_BW > 5000:  # 1 MHz to 5 GHz range
        print(f"[feedback_logger] WARNING: actual_BW={actual_BW} MHz is outside typical range (1-5000)")
    
    # Log the feedback row
    row = [time.time(), family, float(target_Fr), float(target_BW)]
    row += [float(params[i]) for i in range(5)]
    row += [float(actual_Fr), float(actual_BW), float(S11)]
    with open(FEEDBACK_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)
    
    return True

