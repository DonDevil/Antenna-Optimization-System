from pathlib import Path

# ===============================
# CANONICAL SETTINGS
# ===============================

FAMILIES = ["patch_rect"]

# Physical constants
C = 3e8  # speed of light (m/s)

# Default substrate
DEFAULT_SUBSTRATE_H = 1.6e-3  # meters
DEFAULT_EPS_R = 4.4

# ----pi---------------------------
# Parameter bounds (meters)
# params = [W, L, feed_w, h, eps_r]
# -------------------------------
PATCH_W_RANGE = (8e-3, 60e-3)
PATCH_L_RANGE = (8e-3, 60e-3)
FEED_W_RANGE  = (0.5e-3, 4e-3)
SUBSTRATE_H_RANGE = (0.5e-3, 5e-3)
EPS_R_RANGE = (2.0, 10.0)

# -------------------------------
# ML training
# -------------------------------
TRAIN_TEST_SPLIT = 0.2
FORWARD_EPOCHS = 40
INVERSE_EPOCHS = 60
BATCH_SIZE = 128
RANDOM_SEED = 42
PRINT_ERROR = True
SAMPLES = 5000

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = Path(".")
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

DATASET_PATH = BASE_DIR / "dataset.csv"
ANTENNA_PATH = r"E:\Antenna Optimization System\cst_interface\output\antenna.cst"
