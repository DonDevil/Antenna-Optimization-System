from ai_core.parameter_engine import ParameterEngine
from ai_core.ai_config import ANTENNA_PATH, PATCH_L_RANGE, PATCH_W_RANGE, FEED_W_RANGE, SUBSTRATE_H_RANGE, EPS_R_RANGE
from cst_interface.cst_driver import CSTDriver
from cst_interface.param_adapter import patch_rect_to_cst_params
from feedback.feedback_logger import log_feedback
from feedback.ai_quick_retrain import quick_retrain
from ai_core.ai_core_manager import AICoreManager
import math
import numpy as np
import pandas as pd
import time

engine = ParameterEngine()
cst = CSTDriver()
ai_core = AICoreManager()

# Convergence tolerances
FR_TOLERANCE_GHZ = 0.01  # ±10 MHz
BW_TOLERANCE_MHZ = 10     # ±10 MHz
MAX_ITERATIONS = 10

def run_once(
    target_Fr_GHz,
    target_BW_MHz,
    substrate="FR-4 (lossy)",
    conductor="Copper (annealed)",
    file_location=ANTENNA_PATH
):
    # 1. AI inverse design
    params = engine.predict(
        family="patch_rect",
        target_Fr_GHz=target_Fr_GHz,
        target_BW_MHz=target_BW_MHz
    )

    # 2. Adapt params → CST schema
    cst_params = patch_rect_to_cst_params(params)

    # 3. Run CST (close after single run)
    cst.standard_antenna(
        family="Microstrip Patch",
        shape="Rectangular",
        freq=target_Fr_GHz,
        substrate=substrate,
        conductor=conductor,
        params=cst_params,
        close_design=True,
        file_location=file_location
    )

    # 4. Extract results
    Fr_a, BW_a, S11 = cst.extract_s11_results(file_location)
    
    # 5. Validate extracted results
    print(f"\n[VALIDATION] Checking extracted results...")
    print(f"  Fr_a: {Fr_a:.6f} GHz (expected ~{target_Fr_GHz:.4f} GHz)")
    print(f"  BW_a: {BW_a:.2f} MHz (expected ~{target_BW_MHz:.2f} MHz)")
    print(f"  S11: {S11:.2f} dB (target: better is more negative)")
    
    # Validate frequency is within 50% of target
    if Fr_a < 0.5 * target_Fr_GHz or Fr_a > 1.5 * target_Fr_GHz:
        print(f"[WARNING] Resonant frequency {Fr_a:.4f} GHz deviates > 50% from target {target_Fr_GHz:.4f} GHz")
    
    # Validate bandwidth is reasonable (should not be < 0.5 MHz or > target*3)
    if BW_a < 0.5:
        print(f"[WARNING] Bandwidth {BW_a:.2f} MHz is suspiciously small (< 0.5 MHz)")
    elif BW_a > target_BW_MHz * 3:
        print(f"[WARNING] Bandwidth {BW_a:.2f} MHz exceeds 3x target ({target_BW_MHz*3:.2f} MHz)")
    
    # Validate S11 is negative (should be < 0 for good match)
    if S11 > -3:
        print(f"[WARNING] S11 {S11:.2f} dB is not sufficiently negative (poor match)")
    
    print()  # newline for clarity

    # 6. Log feedback
    log_feedback(
        family="patch_rect",
        target_Fr=target_Fr_GHz,
        target_BW=target_BW_MHz,
        params=params,
        actual_Fr=Fr_a,
        actual_BW=BW_a,
        S11=S11
    )

    return params, Fr_a, BW_a, S11


def run_iterative(
    target_Fr_GHz,
    target_BW_MHz,
    substrate="FR-4 (lossy)",
    conductor="Copper (annealed)",
    file_location=ANTENNA_PATH,
    verbose=True,
    close_final_design=True
):
    """
    Iteratively run AI prediction and adaptive parameter correction until target is achieved.
    Uses intelligent parameter adjustments based on error feedback.
    After 10 iterations, runs an 11th iteration with the best result found.
    Triggers model retraining via feedback learning system.
    
    Args:
        target_Fr_GHz: Target resonant frequency in GHz
        target_BW_MHz: Target bandwidth in MHz
        substrate: Substrate material name
        conductor: Conductor material name
        file_location: Path where CST design file will be saved
        verbose: Print detailed iteration information
        close_final_design: Whether to close the design after the 11th iteration (False for persistent mode)
    
    Returns: (best_params, best_Fr_a, best_BW_a, best_S11, iteration_count, convergence_history, best_iteration)
    """
    convergence_history = []
    
    # Tracking for adaptive learning
    params = None
    prev_Fr_error = float('inf')
    prev_BW_error = float('inf')
    
    # Track BEST result (by S11)
    best_S11 = float('inf')
    best_params = None
    best_Fr_a = None
    best_BW_a = None
    best_iteration = 0
    
    # Step sizes for parameter adjustments (meters)
    step_L = 1e-3    # Initial step for length: 1mm
    step_W = 0.5e-3  # Initial step for width: 0.5mm
    step_feed = 0.2e-3  # Initial step for feed width: 0.2mm
    step_h = 0.5e-3  # Initial step for height: 0.5mm
    
    # Adaptive step scaling
    step_scaling = 1.5
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        if verbose:
            print(f"\n=== ITERATION {iteration}/{MAX_ITERATIONS} ===")
        
        if iteration == 1:
            # First iteration: use AI prediction
            params = engine.predict(
                family="patch_rect",
                target_Fr_GHz=target_Fr_GHz,
                target_BW_MHz=target_BW_MHz
            )
            if verbose:
                print(f"AI Prediction: W={params[0]*1e3:.2f}mm, L={params[1]*1e3:.2f}mm, feed_w={params[2]*1e3:.2f}mm, h={params[3]*1e3:.2f}mm")
        else:
            # Subsequent iterations: adaptive parameter correction
            if verbose:
                print(f"Adaptive Correction - Applying intelligent adjustments...")
            
            # Extract current parameters
            W, L, feed_w, h, eps_r = params
            
            # FREQUENCY ADJUSTMENT LOGIC
            # Patch length primarily controls resonant frequency
            Fr_error = Fr_a - target_Fr_GHz
            
            if abs(Fr_error) > 1e-6:  # Not at target
                if Fr_error > 0:  # Frequency too high, need to lower it
                    # Increase patch length to decrease frequency
                    direction_L = 1
                else:  # Frequency too low, need to increase it
                    # Decrease patch length to increase frequency
                    direction_L = -1
                
                # Adaptive step: if error reduced, increase step; if increased, reduce step
                if abs(Fr_error) < prev_Fr_error:
                    step_L = min(step_L * step_scaling, 5e-3)  # Max 5mm
                    if verbose:
                        print(f"  Fr error improved: increasing adjustment step")
                else:
                    step_L = max(step_L / step_scaling, 0.1e-3)  # Min 0.1mm
                    if verbose:
                        print(f"  Fr error worsened: decreasing adjustment step")
                
                L_new = L + direction_L * step_L
                L = np.clip(L_new, PATCH_L_RANGE[0], PATCH_L_RANGE[1])
                if verbose:
                    print(f"  Freq Correction: L {L*1e3 - params[1]*1e3+0:.3f}mm adjustment (L={L*1e3:.2f}mm)")
            
            # BANDWIDTH ADJUSTMENT LOGIC
            # Multiple factors affect bandwidth:
            # - Feed width: affects impedance matching (narrower = higher BW in some cases)
            # - Substrate height: taller substrate = higher BW
            # - Patch width: can affect resonance sharpness
            
            BW_error = BW_a - target_BW_MHz
            
            if abs(BW_error) > 1e-2:  # Not at target
                if BW_error > 0:  # Bandwidth too high, need to reduce it
                    # Reduce feed width (sharper match = lower BW)
                    direction_feed = -1
                    # Could also reduce substrate height
                    direction_h = -1
                else:  # Bandwidth too low, need to increase it
                    # Increase feed width (broader match = higher BW)
                    direction_feed = 1
                    # Increase substrate height for higher BW
                    direction_h = 1
                
                # Adaptive step for feed width
                if abs(BW_error) < prev_BW_error:
                    step_feed = min(step_feed * step_scaling, 1e-3)  # Max 1mm
                    step_h = min(step_h * step_scaling, 2e-3)  # Max 2mm
                    if verbose:
                        print(f"  BW error improved: increasing adjustment step")
                else:
                    step_feed = max(step_feed / step_scaling, 0.05e-3)  # Min 0.05mm
                    step_h = max(step_h / step_scaling, 0.1e-3)  # Min 0.1mm
                    if verbose:
                        print(f"  BW error worsened: decreasing adjustment step")
                
                feed_w_new = feed_w + direction_feed * step_feed
                h_new = h + direction_h * step_h
                
                feed_w = np.clip(feed_w_new, FEED_W_RANGE[0], FEED_W_RANGE[1])
                h = np.clip(h_new, SUBSTRATE_H_RANGE[0], SUBSTRATE_H_RANGE[1])
                
                if verbose:
                    print(f"  BW Correction: feed_w {direction_feed*step_feed*1e3:.3f}mm, h {direction_h*step_h*1e3:.3f}mm adjustment")
            
            # Update params
            params = [W, L, feed_w, h, eps_r]
            
            if verbose:
                print(f"Corrected Params: W={params[0]*1e3:.2f}mm, L={params[1]*1e3:.2f}mm, feed_w={params[2]*1e3:.2f}mm, h={params[3]*1e3:.2f}mm")

        # 2. Adapt params → CST schema
        cst_params = patch_rect_to_cst_params(params)

        # 3. Run CST (close after each iteration to save resources)
        cst.standard_antenna(
            family="Microstrip Patch",
            shape="Rectangular",
            freq=target_Fr_GHz,
            substrate=substrate,
            conductor=conductor,
            params=cst_params,
            close_design=True,
            file_location=file_location
        )

        # 4. Extract results
        Fr_a, BW_a, S11 = cst.extract_s11_results(file_location)
        
        # 5. Validate extracted results
        if verbose:
            if Fr_a < 0.5 * target_Fr_GHz or Fr_a > 1.5 * target_Fr_GHz:
                print(f"  [⚠ WARNING] Frequency {Fr_a:.4f} GHz deviates > 50% from target {target_Fr_GHz:.4f} GHz")
            if BW_a < 0.5:
                print(f"  [⚠ WARNING] Bandwidth {BW_a:.2f} MHz is suspiciously small (anomaly risk)")
            if S11 > -3:
                print(f"  [⚠ WARNING] S11 {S11:.2f} dB is poor (not negative enough)")
        
        if verbose:
            print(f"CST Result: Fr={Fr_a:.4f} GHz (target: {target_Fr_GHz:.4f}), BW={BW_a:.2f} MHz (target: {target_BW_MHz:.2f}), S11={S11:.2f} dB")

        # 6. Log feedback
        log_feedback(
            family="patch_rect",
            target_Fr=target_Fr_GHz,
            target_BW=target_BW_MHz,
            params=params,
            actual_Fr=Fr_a,
            actual_BW=BW_a,
            S11=S11
        )
        
        # 7. Check convergence
        Fr_error = abs(Fr_a - target_Fr_GHz)
        BW_error = abs(BW_a - target_BW_MHz)
        converged = Fr_error <= FR_TOLERANCE_GHZ and BW_error <= BW_TOLERANCE_MHZ
        
        convergence_history.append({
            'iteration': iteration,
            'Fr': Fr_a,
            'BW': BW_a,
            'S11': S11,
            'Fr_error': Fr_error,
            'BW_error': BW_error,
            'params': params.copy()
        })
        
        # Track best result by S11 (lower = better, S11 is negative)
        if S11 < best_S11:
            best_S11 = S11
            best_params = params.copy()
            best_Fr_a = Fr_a
            best_BW_a = BW_a
            best_iteration = iteration
            if verbose:
                print(f"✓ NEW BEST: S11={S11:.2f} dB")
        
        if verbose:
            print(f"Error: Fr={Fr_error*1000:.2f} MHz, BW={BW_error:.2f} MHz, S11={S11:.2f} dB")
            if converged:
                print(f"\n✓ CONVERGED at iteration {iteration}")
        
        # Update tracking for next iteration
        prev_Fr_error = Fr_error
        prev_BW_error = BW_error
        
        if converged:
            break
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"BEST RESULT ACHIEVED AT ITERATION {best_iteration}")
        print(f"S11={best_S11:.2f} dB, Fr={best_Fr_a:.4f} GHz, BW={best_BW_a:.2f} MHz")
        print(f"RUNNING 11TH ITERATION WITH BEST PARAMETERS...")
        print(f"{'='*60}")
    
    # ===== ITERATION 11: Run with BEST parameters =====
    # NOTE: Control whether to close the design based on mode:
    # - BATCH MODE (automate.py): close_final_design=True
    #   * Closes the design cleanly after saving
    #   * Fresh data extracted from disk
    #   * No file handle accumulation
    # - INTERACTIVE/PERSISTENT MODE (ui/new.py): close_final_design=False  
    #   * Design stays open for user review
    #   * User can manually close or configure for next run
    #
    best_params_cst = patch_rect_to_cst_params(best_params)
    
    cst.standard_antenna(
        family="Microstrip Patch",
        shape="Rectangular",
        freq=target_Fr_GHz,
        substrate=substrate,
        conductor=conductor,
        params=best_params_cst,
        close_design=close_final_design,  # Use parameter to control behavior
        file_location=file_location
    )
    
    # Wait a moment to ensure file I/O completes
    time.sleep(0.5)
    
    # Extract final results (reading fresh data from closed/saved file)
    Fr_final, BW_final, S11_final = cst.extract_s11_results(file_location)
    
    # Validate final results
    if verbose:
        print(f"\n[FINAL VALIDATION]")
        if Fr_final < 0.5 * target_Fr_GHz or Fr_final > 1.5 * target_Fr_GHz:
            print(f"  [⚠ WARNING] Final frequency {Fr_final:.4f} GHz deviates > 50% from target")
        if BW_final < 0.5:
            print(f"  [⚠ WARNING] Final bandwidth {BW_final:.2f} MHz is suspiciously small")
        if S11_final > -3:
            print(f"  [⚠ WARNING] Final S11 {S11_final:.2f} dB is poor")
    
    if verbose:
        print(f"\n=== ITERATION 11/11 (FINAL - BEST RESULT) ===")
        print(f"AI Params Used: W={best_params[0]*1e3:.2f}mm, L={best_params[1]*1e3:.2f}mm, feed_w={best_params[2]*1e3:.2f}mm, h={best_params[3]*1e3:.2f}mm")
        print(f"CST Result: Fr={Fr_final:.4f} GHz (target: {target_Fr_GHz:.4f}), BW={BW_final:.2f} MHz (target: {target_BW_MHz:.2f}), S11={S11_final:.2f} dB")
        print(f"Final Error: Fr={abs(Fr_final - target_Fr_GHz)*1000:.2f} MHz, BW={abs(BW_final - target_BW_MHz):.2f} MHz")
    
    # Log final iteration
    log_feedback(
        family="patch_rect",
        target_Fr=target_Fr_GHz,
        target_BW=target_BW_MHz,
        params=best_params,
        actual_Fr=Fr_final,
        actual_BW=BW_final,
        S11=S11_final
    )
    
    convergence_history.append({
        'iteration': 11,
        'Fr': Fr_final,
        'BW': BW_final,
        'S11': S11_final,
        'Fr_error': abs(Fr_final - target_Fr_GHz),
        'BW_error': abs(BW_final - target_BW_MHz),
        'params': best_params.copy(),
        'is_final': True,
        'best_from_iteration': best_iteration
    })
    
    # ===== TRIGGER MODEL RETRAINING =====
    if verbose:
        print(f"\n{'='*60}")
        print(f"TRIGGERING FEEDBACK LEARNING SYSTEM...")
        print(f"{'='*60}")
    
    retrain_triggered = quick_retrain()
    if verbose:
        if retrain_triggered:
            print(f"✓ Model retraining triggered successfully!")
            print(f"  The system has learned from this optimization run.")
        else:
            print(f"⚠ Model retraining not yet triggered (may need more samples)")
            print(f"  [Requires 30+ total feedback samples, then every 30 new samples]")
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"OPTIMIZATION COMPLETE!")
        print(f"Best S11: {best_S11:.2f} dB (from iteration {best_iteration})")
        print(f"Final Output: Fr={Fr_final:.4f} GHz, BW={BW_final:.2f} MHz, S11={S11_final:.2f} dB")
        print(f"{'='*60}")
    
    return best_params, best_Fr_a, best_BW_a, best_S11, 11, convergence_history, best_iteration

