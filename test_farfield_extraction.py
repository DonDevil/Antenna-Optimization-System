"""
Test script to extract and display all farfield parameters from CST
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from cst_interface.cst_driver import CSTDriver
from ai_core.ai_config import ANTENNA_PATH
import json

def test_farfield_extraction():
    """Test extraction of farfield parameters from CST project"""
    
    print("=" * 80)
    print("CST FARFIELD PARAMETER EXTRACTION TEST")
    print("=" * 80)
    
    # Check if CST project exists
    if not os.path.exists(ANTENNA_PATH):
        print(f"[ERROR] CST project not found at: {ANTENNA_PATH}")
        print("Creating a simple test antenna first...")
        
        # Try to create and run a test antenna
        try:
            driver = CSTDriver()
            
            # Test parameters for a simple patch antenna
            test_params = {
                'patch_W': 0.020,      # 20 mm width
                'patch_L': 0.025,      # 25 mm length  
                'substrate_h': 0.0016, # 1.6 mm height
                'substrate_W': 0.046,  # 46 mm (patch + 6*h)
                'substrate_L': 0.051,  # 51 mm (patch + 6*h)
                'feed_width': 0.002,   # 2 mm feed
                'feed_type': 0,
            }
            
            print("\nBuilding test antenna at 2.5 GHz...")
            driver.standard_antenna(
                family="Microstrip Patch",
                shape="Rectangular",
                freq=2.5,
                substrate="substrate_material",
                conductor="PEC",
                params=test_params,
                close_design=True,
                file_location=ANTENNA_PATH
            )
            print("Test antenna created successfully!")
            
        except Exception as e:
            print(f"[ERROR] Could not create test antenna: {e}")
            return
    
    # Now extract and display all parameters
    print(f"\nLoading CST project: {ANTENNA_PATH}")
    
    try:
        driver = CSTDriver()
        
        # Extract S11 parameters
        print("\n" + "-" * 80)
        print("S11 PARAMETERS")
        print("-" * 80)
        
        fr, bw, s11_min = driver.extract_s11_results(ANTENNA_PATH)
        print(f"Resonant Frequency (Fr): {fr:.6f} GHz")
        print(f"Bandwidth (BW @ -10dB): {bw:.2f} MHz")
        print(f"S11 Minimum: {s11_min:.2f} dB")
        
        # Extract Farfield parameters
        print("\n" + "-" * 80)
        print("FARFIELD PARAMETERS")
        print("-" * 80)
        
        farfield_results = driver.extract_farfield_results(ANTENNA_PATH, freq_GHz=fr)
        
        print("\nExtracted Farfield Parameters:")
        print(f"  Frequency:        {farfield_results['frequency_GHz']:.6f} GHz")
        print(f"  Gain:             {farfield_results['gain_dBi']:.2f} dBi")
        print(f"  Directivity:      {farfield_results['directivity_dBi']:.2f} dBi")
        print(f"  Main Lobe Mag:    {farfield_results['main_lobe_mag_dB']:.2f} dB")
        print(f"  Side Lobe Level:  {farfield_results['side_lobe_level_dB']}")
        print(f"  3dB Beamwidth:    {farfield_results['beamwidth_3db_deg']}")
        print(f"  Efficiency (%):   {farfield_results['efficiency_pct']:.2f}%")
        print(f"  Efficiency (dB):  {farfield_results['efficiency_dB']:.2f} dB")
        
        # Combine all results
        print("\n" + "-" * 80)
        print("COMBINED ANTENNA CHARACTERISTICS")
        print("-" * 80)
        
        all_results = {
            'S11_results': {
                'Fr_GHz': fr,
                'BW_MHz': bw,
                'S11_min_dB': s11_min,
            },
            'Farfield_results': farfield_results
        }
        
        print("\nComplete parameter set (JSON):")
        print(json.dumps(all_results, indent=2))
        
        # Save to file for reference
        output_file = os.path.join(os.path.dirname(__file__), "farfield_extraction_results.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        
        return all_results
        
    except Exception as e:
        print(f"[ERROR] Failed to extract parameters: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = test_farfield_extraction()
    sys.exit(0 if results is not None else 1)
