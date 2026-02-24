#!/usr/bin/env python3
"""
Quick Diagnostic Script - Run this to verify extraction fixes
Usage: python diagnostic.py
"""

import pandas as pd
import os

print("\n" + "="*70)
print("ANTENNA OPTIMIZATION SYSTEM - DIAGNOSTIC REPORT")
print("="*70 + "\n")

# 1. Check feedback CSV
feedback_file = "feedback/ai_feedback.csv"
if os.path.exists(feedback_file):
    df = pd.read_csv(feedback_file)
    print(f"✓ Feedback CSV found: {len(df)} records")
    print(f"\n  Columns: {list(df.columns)}")
    
    if 'actual_BW_MHz' in df.columns:
        bw_values = df['actual_BW_MHz'].dropna()
        print(f"\n  Bandwidth Statistics (actual_BW_MHz):")
        print(f"    - Count: {len(bw_values)}")
        print(f"    - Min: {bw_values.min():.3f} MHz")
        print(f"    - Max: {bw_values.max():.3f} MHz")
        print(f"    - Mean: {bw_values.mean():.3f} MHz")
        print(f"    - Median: {bw_values.median():.3f} MHz")
        
        # Check for anomalies
        anomalies = bw_values[(bw_values < 0.5) | (bw_values > 300)]
        if len(anomalies) > 0:
            print(f"\n  ⚠ {len(anomalies)} ANOMALIES DETECTED:")
            for idx, val in anomalies.items():
                print(f"      Row {idx}: {val:.6f} MHz (likely unit error)")
        else:
            print(f"\n  ✓ No bandwidth anomalies detected")
    
    if 'actual_Fr_GHz' in df.columns:
        fr_values = df['actual_Fr_GHz'].dropna()
        print(f"\n  Resonant Frequency Statistics (actual_Fr_GHz):")
        print(f"    - Min: {fr_values.min():.6f} GHz")
        print(f"    - Max: {fr_values.max():.6f} GHz")
        print(f"    - Mean: {fr_values.mean():.6f} GHz")
        
        # Check for reasonable range (0.1 - 20 GHz)
        out_of_range = fr_values[(fr_values < 0.1) | (fr_values > 20)]
        if len(out_of_range) > 0:
            print(f"\n  ⚠ {len(out_of_range)} FREQUENCY OUT OF RANGE:")
            for idx, val in out_of_range.items():
                print(f"      Row {idx}: {val:.6f} GHz (expected 0.5-20 GHz)")
        else:
            print(f"\n  ✓ All frequencies in reasonable range")
    
    if 'S11_dB' in df.columns:
        s11_values = df['S11_dB'].dropna()
        print(f"\n  S11 Statistics (S11_dB):")
        print(f"    - Min (best): {s11_values.min():.2f} dB")
        print(f"    - Max (worst): {s11_values.max():.2f} dB")
        print(f"    - Mean: {s11_values.mean():.2f} dB")
        
        # Check improvement over iterations
        if len(df) >= 2:
            first_s11 = df['S11_dB'].iloc[0]
            last_s11 = df['S11_dB'].iloc[-1]
            improvement = first_s11 - last_s11  # More negative = better
            if improvement > 0:
                print(f"\n  ✓ S11 improving ({improvement:.2f} dB better)")
            else:
                print(f"\n  ⚠ S11 not improving ({improvement:.2f} dB)")
else:
    print(f"✗ Feedback file not found: {feedback_file}")

print("\n" + "="*70)
print("Retraining Metadata")
print("="*70 + "\n")

meta_file = ".ai_retrain_meta"
if os.path.exists(meta_file):
    with open(meta_file, 'r') as f:
        last_trained = int(f.read().strip())
    print(f"✓ Last retrained at sample: {last_trained}")
    if os.path.exists(feedback_file):
        total = len(df)
        print(f"  Current samples: {total}")
        print(f"  Samples since retrain: {total - last_trained}")
        if (total - last_trained) >= 10:
            print(f"  → Next retrain available!")
else:
    print(f"ℹ No retraining yet (needs 30+ samples first)")

print("\n" + "="*70)
print("Model Files")
print("="*70 + "\n")

models_to_check = [
    "models/forward_patch_rect.keras",
    "models/inverse_patch_rect.keras",
    "feedback/ai_quick_retrain.save"
]

for model_path in models_to_check:
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024*1024)
        print(f"✓ {model_path} ({size_mb:.2f} MB)")
    else:
        print(f"✗ Missing: {model_path}")

print("\n" + "="*70)
print("Next Steps")
print("="*70)
print("""
1. Run optimization with Persistent Mode enabled
2. Monitor the console output for [DEBUG] and [RESULT] lines
3. Verify BW printed matches CST plot bandwidth visually
4. Once 30 total samples logged, model retraining triggers
5. Future runs will use improved AI predictions

Expected Output Example:
  [RESULT] Fr=2.344000 GHz, BW=59.53 MHz, S11=-42.41 dB
  
If you see BW=1.22 MHz while CST shows 59 MHz, it's still broken.
""")
print("="*70 + "\n")
