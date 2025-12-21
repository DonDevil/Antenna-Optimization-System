# auto_data_generator.py
import time
import random
import os
from datetime import datetime

from ai_core.parameter_engine import ParameterEngine
from cst_interface.cst_driver_mode2 import CSTDriverMode2
from feedback.feedback_logger import log_feedback
from feedback.ai_quick_retrain import quick_retrain
from ai_core.ai_config import ANTENNA_PATH

# ----------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------
FEEDBACK_CSV = r"feedback\ai_feedback_mode2.csv"

# define a frequency sweep range (GHz)
FREQ_MIN = 1.0
FREQ_MAX = 10.0

# define bandwidth sweep range (MHz)
BW_MIN = 50
BW_MAX = 800

# number of runs (None for infinite loop)
RUNS = None  # set to integer if you want a fixed number

# delay between runs (so you don’t overload CST)
DELAY_SECONDS = 3

# substrate and conductor pool
SUBSTRATES = [
    "FR-4 (lossy)",
    "Rogers RT-duroid 5880 (lossy)",
    "Taconic TLY-3 (lossy)"
]

CONDUCTORS = [
    "Copper (annealed)",
    "Aluminum",
    "Silver"
]

# ----------------------------------------------------------
# INITIALIZE
# ----------------------------------------------------------

engine = ParameterEngine()
cst = CSTDriverMode2()

print("\n==============================================================")
print("   AUTONOMOUS DATA GENERATOR (CST + AI FEEDBACK LOOP)")
print("==============================================================")
print(" Running with real CST simulations. Press CTRL+C to stop.\n")


# ----------------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------------

def random_targets():
    """Generate random frequency and bandwidth."""
    f = random.uniform(FREQ_MIN, FREQ_MAX)
    bw = random.uniform(BW_MIN, BW_MAX)
    return round(f, 4), round(bw, 3)


def random_family():
    """Pick a random antenna family."""
    return 'patch_rect'


def random_materials():
    """Random substrate and conductor."""
    return random.choice(SUBSTRATES), random.choice(CONDUCTORS)

# ----------------------------------------------------------
# MAIN LOOP EXECUTION
# ----------------------------------------------------------

def run_cycle():
    try:
        family = random_family()
        target_Fr, target_BW = random_targets()
        substrate, conductor = random_materials()

        print(f"\n[{datetime.now()}] Cycle start")
        print(f"Family={family}, Target Fr={target_Fr} GHz, BW={target_BW} MHz")

        # Unified parameter prediction (inverse + correction + exploration)
        params = engine.predict(
            family=family,
            target_Fr=target_Fr,
            target_BW=target_BW,
            explore=True
        )

        # CST parameter mapping
        cst_params = {
            "patch_W": params[0],
            "patch_L": params[1],
            "eps_eff": 1.0,
            "substrate_h": params[3],
            "eps_r": params[4],
            "feed_width": params[2],
            "substrate_W": params[0] + 6 * params[3],
            "substrate_L": params[1] + 6 * params[3],
            "feed_type": 0
        }

        print("Running CST...")
        cst.standard_antenna(
            "Microstrip Patch",
            "Rectangular",
            target_Fr,
            substrate,
            conductor,
            cst_params
        )

        Fr_actual, BW_actual, S11 = cst.extract_s11_results(ANTENNA_PATH)

        print(f"CST → Fr={Fr_actual:.4f} GHz, BW={BW_actual:.2f} MHz, S11={S11:.2f} dB")

        # Log consistent feedback (params actually used)
        log_feedback(
            family,
            target_Fr,
            target_BW,
            params[:5],
            Fr_actual,
            BW_actual,
            S11
        )

        # Incremental correction learning
        quick_retrain()

        print("Cycle complete ✔")

    except Exception as e:
        print(" Cycle failed:", str(e))

# ----------------------------------------------------------
# START EXECUTION LOOP
# ----------------------------------------------------------

def main():
    count = 0
    while True:
        run_cycle()
        count += 1

        if RUNS is not None and count >= RUNS:
            break

        print(f"Sleeping {DELAY_SECONDS} seconds before next cycle...\n")
        time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    main()
