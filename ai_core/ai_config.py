# ai_config.py
"""
Global configuration flags and ranges.
Change these values to tune the project.
"""
from pathlib import Path

# -------------------------
# Simple flags
# -------------------------
PRINT_ERROR = True        # print eval losses
AUTO_RETRAIN = True       # permit retrain in feedback loop
RETRAIN_MIN_SAMPLES = 12
RETRAIN_EVERY = 8

# -------------------------
# Model training / dataset
# -------------------------
TRAIN_TEST_SPLIT = 0.2
FORWARD_EPOCHS = 40
INVERSE_EPOCHS = 60
BATCH_SIZE = 128
RANDOM_SEED = 42

# -------------------------
# Physical & dataset defaults
# -------------------------
C = 3e8  # speed of light
DEFAULT_SUBSTRATE_H = 1.6e-3  # 1.6 mm
DEFAULT_EPS_R = 4.4

# Family list (mode 2)
FAMILIES = [
    "patch_rect", "patch_circ", "patch_meander", "patch_u-slot", "patch_e-shape",
    "monopole", "dipole", "cpw_uwb", "slot", "vivaldi"
]

# Param ranges (meters)
PATCH_W_RANGE = (8e-3, 60e-3)
PATCH_L_RANGE = (8e-3, 60e-3)
CIRC_RADIUS_RANGE = (5e-3, 30e-3)
MEANDER_DEPTH_RANGE = (1e-3, 10e-3)
FEED_W_RANGE = (0.5e-3, 4e-3)
MONOPOLE_LENGTH_RANGE = (5e-3, 80e-3)
MONOPOLE_WIDTH_RANGE = (0.5e-3, 6e-3)
DIPOLE_LENGTH_RANGE = (10e-3, 160e-3)
DIPOLE_WIDTH_RANGE = (0.5e-3, 6e-3)
SAMPLES = 120000

# Paths
BASE_DIR = Path(".")
DATASET_PATH = BASE_DIR / "dataset_mode2.csv"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
ANTENNA_PATH = r"E:\Antenna Optimization System\cst_interface\output\antenna.cst"