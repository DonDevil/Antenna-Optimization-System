# auto_data_generator.py
import time
import random
import os
from datetime import datetime

from ai_core.ai_core_manager import AICoreManager
from cst_interface.cst_driver_mode2 import CSTDriverMode2
from feedback.feedback_logger import log_feedback
from feedback.ai_quick_retrain import quick_retrain
from ai_core.ai_config import FAMILIES, ANTENNA_PATH

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

ai_mgr = AICoreManager()
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
    """Run one full AI → CST → feedback → retrain cycle."""
    try:
        family = random_family()
        freq_target, bw_target = random_targets()
        substrate, conductor = random_materials()

        print(f"\n[{datetime.now()}] Starting cycle:")
        print(f"  Family     : {family}")
        print(f"  Target Fr  : {freq_target} GHz")
        print(f"  Target BW  : {bw_target} MHz")
        print(f"  Substrate  : {substrate}")
        print(f"  Conductor  : {conductor}")

        # -------------------------------
        # STEP 1: INVERSE PREDICTION
        # -------------------------------
        params = ai_mgr.predict_inverse(family, freq_target, bw_target)
        print("  AI inverse prediction params:", params)

        # -------------------------------
        # STEP 2: FAST OPTIMIZATION
        # -------------------------------
        opt = ai_mgr.optimize_parameters(family, freq_target, bw_target)
        if not isinstance(params, (list, tuple)) or len(params) < 5:
                print(f"Error: AI returned invalid params: {params}")
                return
        params = opt['params']
        # -------------------------------
        # STEP 3: PREP CST INPUT PARAMS
        # -------------------------------
        try:
            cst_params = {
                "patch_W": params[0],
                "patch_L": params[1],
                "eps_eff": 1.0,  # calculated from substrate
                "substrate_h": params[3],
                "eps_r": params[4],
                "feed_width": params[2],
                "substrate_W": params[0] + 6 * params[3],
                "substrate_L": params[1] + 6 * params[3],
                "feed_type": 0
            }
        except Exception as ex:
            print(f"Error building CST params: {ex}")
            print(params)
            return
        # -------------------------------
        # STEP 4: RUN CST
        # -------------------------------
        print("  Running CST...")
        cst.standard_antenna("Microstrip Patch", "Rectangular",freq_target, substrate, conductor, cst_params)
        
        # -------------------------------
        # STEP 5: EXTRACT RESULTS
        # -------------------------------
        temp_cst_path = ANTENNA_PATH

        Fr_actual, BW_actual, S11 = cst.extract_s11_results(temp_cst_path)
        print(f"  CST Results -> Fr={Fr_actual:.4f}, BW={BW_actual:.4f}, S11={S11:.2f} dB")

        # -------------------------------
        # STEP 6: LOG FEEDBACK
        # -------------------------------
        log_feedback(family, freq_target, bw_target, params, Fr_actual, BW_actual, S11)

        print("  Feedback logged ✔")

        # -------------------------------
        # STEP 7: QUICK RETRAIN
        # -------------------------------
        quick_retrain()
        print("  Quick retrain completed ✔")

        print("Cycle completed successfully.\n")

    except Exception as e:
        print("❌ Error during cycle:", e)


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
