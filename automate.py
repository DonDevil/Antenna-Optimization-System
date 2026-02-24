# auto_data_generator.py
"""
AUTONOMOUS DATA GENERATOR
Generates random antenna specifications and logs results for AI learning.
Uses fixed CST simulations (1 run per spec, no iterations).
Suitable for building diverse training data and automatic model retraining.

The AI model retrains automatically every 30 new samples (after 30 initial samples).
"""

import time
import random
import os
from datetime import datetime

from ai_core.parameter_engine import ParameterEngine
from cst_interface.cst_driver import CSTDriver
from cst_interface.param_adapter import patch_rect_to_cst_params
from feedback.feedback_logger import log_feedback
from feedback.ai_quick_retrain import quick_retrain
from ai_core.ai_config import ANTENNA_PATH
from pipeline import run_iterative

# ----------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------
FEEDBACK_CSV = r"feedback\ai_feedback.csv"
# CHOOSE MODE: 'single' for quick single runs, 'iterative' for optimized learning
MODE = 'iterative'  # ← Change to 'single' for quick cycles
# define a frequency sweep range (GHz)
FREQ_MIN = 2
FREQ_MAX = 7

# define bandwidth sweep range (MHz)
BW_MIN = 50
BW_MAX = 125

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
cst = CSTDriver()

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
    """
    Single automated generation cycle:
    1. Generate random frequency/bandwidth targets
    2. AI predicts antenna parameters
    3. Run CST simulation
    4. Extract and validate results
    5. Log feedback for learning
    6. Trigger retraining if eligible
    """
    try:
        family = random_family()
        target_Fr, target_BW = random_targets()
        substrate, conductor = random_materials()

        print(f"\n[{datetime.now()}] Cycle start")
        print(f"Target: Fr={target_Fr} GHz, BW={target_BW} MHz | Substrate={substrate}, Conductor={conductor}")

        # 1. AI inverse design
        params = engine.predict(
            family=family,
            target_Fr_GHz=target_Fr,
            target_BW_MHz=target_BW
        )
        print(f"AI Params: W={params[0]*1e3:.2f}mm, L={params[1]*1e3:.2f}mm, feed_w={params[2]*1e3:.2f}mm, h={params[3]*1e3:.2f}mm")

        # 2. Convert to CST parameters (uses corrected mapping)
        cst_params = patch_rect_to_cst_params(params)

        # 3. Run CST simulation (close after each run in batch mode)
        print("Running CST simulation...")
        cst.standard_antenna(
            family="Microstrip Patch",
            shape="Rectangular",
            freq=target_Fr,
            substrate=substrate,
            conductor=conductor,
            params=cst_params,
            close_design=True,
            file_location=ANTENNA_PATH
        )

        # 4. Extract results (now with corrected bandwidth calculation)
        Fr_actual, BW_actual, S11 = cst.extract_s11_results(ANTENNA_PATH)

        # 5. VALIDATE extracted results
        print(f"\n[VALIDATION] Checking extraction results...")
        print(f"  Fr_actual: {Fr_actual:.6f} GHz (target: {target_Fr:.4f} GHz)")
        print(f"  BW_actual: {BW_actual:.2f} MHz (target: {target_BW:.2f} MHz)")
        print(f"  S11: {S11:.2f} dB")
        
        # Check for anomalies
        validation_pass = True
        if Fr_actual < 0.5 * target_Fr or Fr_actual > 1.5 * target_Fr:
            print(f"  [⚠ WARNING] Frequency deviates > 50% from target")
            validation_pass = False
        if BW_actual < 0.5:
            print(f"  [⚠ WARNING] Bandwidth unusually small (< 0.5 MHz) - possible extraction error")
            validation_pass = False
        if S11 > -3:
            print(f"  [⚠ WARNING] S11 not sufficiently negative (poor antenna match)")
            validation_pass = False
        
        if validation_pass:
            print(f"  ✓ Validation PASS")
        else:
            print(f"  ⚠ Validation WARNINGS - data may be anomalous")
        print()

        # 6. Log feedback (training data for AI)
        log_feedback(
            family="patch_rect",
            target_Fr=target_Fr,
            target_BW=target_BW,
            params=params[:5],
            actual_Fr=Fr_actual,
            actual_BW=BW_actual,
            S11=S11
        )

        # 7. Attempt model retraining
        retrain_triggered = quick_retrain()
        if retrain_triggered:
            print(f"✓ Model retrained on accumulated feedback!")
        else:
            print(f"⚠ Retraining not yet triggered (need 30 samples or 10 new samples)")

        print(f"Cycle complete ✔\n")

    except Exception as e:
        print(f" [ERROR] Cycle failed: {str(e)}")
        import traceback
        traceback.print_exc()


def run_cycle_iterative():
    """
    Iterative automated cycle with optimization:
    1. Generate random frequency/bandwidth targets
    2. Run iterative optimization (10 iterations + 1 final)
    3. Collect feedback from all 11 simulations
    4. Trigger retraining
    
    *** MUCH BETTER FOR LEARNING ***
    This produces 11 data points per cycle vs 1 data point with run_cycle()
    Each cycle optimizes toward the target, teaching the AI correction patterns
    """
    try:
        target_Fr = round(random.uniform(FREQ_MIN, FREQ_MAX), 4)
        target_BW = round(random.uniform(BW_MIN, BW_MAX), 3)
        substrate = random.choice(SUBSTRATES)
        conductor = random.choice(CONDUCTORS)

        print(f"\n[{datetime.now()}] ITERATIVE CYCLE START")
        print(f"Target: Fr={target_Fr} GHz, BW={target_BW} MHz")
        print(f"Substrate: {substrate}, Conductor: {conductor}")
        print(f"Running 10 optimization iterations + 1 final review...\n")

        # Run iterative optimization (includes feedback logging)
        best_params, best_Fr_a, best_BW_a, best_S11, iters, history, best_iter = run_iterative(
            target_Fr_GHz=target_Fr,
            target_BW_MHz=target_BW,
            substrate=substrate,
            conductor=conductor,
            file_location=ANTENNA_PATH,
            verbose=True
        )

        print(f"\n{'='*70}")
        print(f"ITERATIVE CYCLE RESULTS")
        print(f"{'='*70}")
        print(f"Best iteration: {best_iter}")
        print(f"Final Fr: {best_Fr_a:.4f} GHz (target: {target_Fr:.4f})")
        print(f"Final BW: {best_BW_a:.2f} MHz (target: {target_BW:.2f})")
        print(f"Final S11: {best_S11:.2f} dB")
        print(f"Total feedback entries logged: {len(history)}")
        
        # Attempt model retraining on accumulated feedback
        print(f"\nAttempting model retraining...")
        retrain_triggered = quick_retrain()
        if retrain_triggered:
            print(f"✓ Model retrained on accumulated feedback!")
        else:
            print(f"⚠ Retraining not yet triggered (accumulating samples)")

        print(f"{'='*70}")
        print(f"Iterative cycle complete ✔")
        print(f"All designs closed. Ready for next cycle.\n")

    except Exception as e:
        print(f"\n [ERROR] Iterative cycle failed: {str(e)}")
        import traceback
        traceback.print_exc()

# ----------------------------------------------------------
# START EXECUTION LOOP
# ----------------------------------------------------------

def main():
    """Main loop: continuously generate data until interrupted."""
    count = 0
    print("\n" + "="*70)
    print("AUTONOMOUS DATA GENERATOR - ACTIVE")
    print(f"MODE: {MODE.upper()}")
    print("="*70)
    print(f"Frequency range: {FREQ_MIN} - {FREQ_MAX} GHz")
    print(f"Bandwidth range: {BW_MIN} - {BW_MAX} MHz")
    print(f"Delay between runs: {DELAY_SECONDS} seconds")
    if RUNS:
        print(f"Target runs: {RUNS}")
    else:
        print(f"Target runs: INFINITE (press Ctrl+C to stop)")
    
    if MODE == 'iterative':
        print(f"\nMODE: ITERATIVE (Optimized Learning)")
        print(f"  - Each cycle runs 10 optimization iterations + 1 final")
        print(f"  - Generates 11 feedback entries per cycle")
        print(f"  - Better for teaching AI correction patterns")
    else:
        print(f"\nMODE: SINGLE (Quick Testing)")
        print(f"  - Each cycle runs single CST simulation")
        print(f"  - Generates 1 feedback entry per cycle")
        print(f"  - Faster but less training data")
    
    print("="*70 + "\n")
    print("Press CTRL+C to stop gracefully.\n")
    
    # Choose which function to call
    cycle_function = run_cycle_iterative if MODE == 'iterative' else run_cycle
    
    try:
        while True:
            count += 1
            print(f"\n{'='*70}")
            print(f"CYCLE #{count} - Starting autonomous {MODE} mode")
            print(f"{'='*70}")
            
            cycle_function()

            if RUNS is not None and count >= RUNS:
                print(f"\n{'='*70}")
                print(f"TARGET CYCLES COMPLETED: {count}/{RUNS}")
                print(f"{'='*70}\n")
                break

            print(f"Sleeping {DELAY_SECONDS} seconds before next cycle...")
            time.sleep(DELAY_SECONDS)
    
    except KeyboardInterrupt:
        print(f"\n\n{'='*70}")
        print(f"STOPPED BY USER after {count} cycles")
        print(f"MODE: {MODE.upper()}")
        if MODE == 'iterative':
            print(f"Total iterations run: ~{count * 11}")
            print(f"Feedback entries generated: ~{count * 11}")
        else:
            print(f"Feedback entries generated: {count}")
        print(f"{'='*70}")
        print(f"Data logged to: {FEEDBACK_CSV}")
        print(f"Run 'python diagnostic.py' to check data quality\n")
        
if __name__ == "__main__":
    main()
