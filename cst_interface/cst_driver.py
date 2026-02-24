import json
import os
from cst.interface import DesignEnvironment
import cst.results
import time
import numpy as np
from ai_core.ai_config import ANTENNA_PATH

class CSTDriver:
    def __init__(self, cst_project=None):
        self.material_library = r"cst_interface\database\material_library.json"
        self.cst_project = cst_project

        # Load macro commands
        json_path = os.path.join(os.path.dirname(__file__), r"database\commands.json")
        with open(json_path, "r") as f:
            self.commands = json.load(f)


    def add_material(self,m_name):
        def json_to_macro(material_json, material_name):
            if material_name not in material_json:
                raise ValueError("Material not found in JSON")
            props = material_json[material_name]
            lines = ['With Material']
            no_value_flags = {'create', 'reset', 'resethblist', 'generatenonlinearcurve'}  # add flag-only keys here

            for key, value in props.items():
                capital_key = key.capitalize()
                if key == 'name':
                    lines.append(f'    .Name "{value}"')
                elif key in no_value_flags:
                    # No quotes, just the flag
                    lines.append(f'    .{capital_key}')
                else:
                    if value == "" or value is None:
                        lines.append(f'    .{capital_key} ""')
                    elif isinstance(value, list):
                        joined = ', '.join([f'"{v}"' for v in value])
                        lines.append(f'    .{capital_key} {joined}')
                    else:
                        lines.append(f'    .{capital_key} "{value}"')
            lines.append('End With')
            return '\n'.join(lines)
        with open(self.material_library, "r") as f:
            loaded_json = json.load(f)

        macro_reproduced = json_to_macro(loaded_json, m_name)
        self.mws.model3d.add_to_history(m_name, macro_reproduced)

    def run_command(self, name: str, **kwargs):
        """
        Run a predefined CST VBA macro by name with optional parameters.
        Example:
            driver.run_command("export_s11", filename="C:\\temp\\s11.txt")
        """
        if name not in self.commands:
            raise ValueError(f"Unknown command: {name}")
        

        macro = self.commands[name]
        if kwargs:
            macro = macro.format(**kwargs)

        self.mws.model3d.add_to_history(name, macro)
    
    def _mm(self, meters):
        return float(meters * 1e3)

    def _lambda_mm(self, freq_GHz):
        return 300.0 / float(freq_GHz)

  
    def standard_antenna(self, family, shape, freq, substrate, conductor, params, close_design=True, file_location=ANTENNA_PATH):
        """
        Build and run a standard antenna in CST.
        
        Args:
            family: Antenna family (e.g., "Microstrip Patch")
            shape: Antenna shape (e.g., "Rectangular")
            freq: Target frequency in GHz
            substrate: Substrate material name
            conductor: Conductor material name
            params: Dictionary with antenna parameters
            close_design: Whether to close the CST design after running (default: True)
                         - Set to False when running multiple iterations (persistent mode)
                         - Set to True for single runs or batch automation
            file_location: Path where to save the CST project
        """
        if family == "Microstrip Patch" and shape == "Rectangular":
            # Create or open design environment
            self.de = DesignEnvironment()
            self.mws = self.de.new_mws() if self.cst_project is None else self.de.open_mws(self.cst_project)
            self.add_material(substrate)
            self.add_material(conductor)
            time.sleep(2)
            P_W = params['patch_W'] * 1e3  # m to mm
            P_L = params['patch_L'] * 1e3  # m to mm
            S_h = params['substrate_h'] * 1e3  # m to mm
            S_W = params['substrate_W'] * 1e3  # m to mm
            S_L = params['substrate_L'] * 1e3  # m to mm
            F_W = params['feed_width'] * 1e3  # m to mm
            F_type = params['feed_type']
            P_W = params['patch_W'] * 1e3  # m to mm
            freq = float(freq)  # GHz
            print(P_W, P_L, S_h, S_W, S_L, F_W, F_type, freq)

            lambda_0 = 300.0 / freq  # approx wavelength in mm
            k_val = lambda_0 / 4


            self.run_command("define brick",solid_name="substrate",
                             component_name="component1",
                             material=substrate,
                             x1="-{:.4f}".format(S_W/2),
                             x2="{:.4f}".format(S_W/2),
                             y1="-{:.4f}".format(S_L/2),
                             y2="{:.4f}".format(S_L/2),
                             z1="0",
                             z2="{:.4f}".format(S_h))
            
            self.run_command("define brick",solid_name="ground",
                             component_name="component1",
                             material=conductor,
                             x1="-{:.4f}".format(S_W/2),
                             x2="{:.4f}".format(S_W/2),
                             y1="-{:.4f}".format(S_L/2),
                             y2="{:.4f}".format(S_L/2),
                             z1="0",
                             z2="-0.035")
            
            self.run_command("define brick",solid_name="patch",
                             component_name="component1",
                             material=conductor,
                             x1="-{:.4f}".format(P_W/2),
                             x2="{:.4f}".format(P_W/2),
                             y1="-{:.4f}".format(P_L/2),
                             y2="{:.4f}".format(P_L/2),
                             z1="{:.4f}".format(S_h),
                             z2="{:.4f}".format(0.035+S_h))

            self.run_command("define brick",solid_name="feed",
                             component_name="component1",
                             material=conductor,
                             x1="-{:.4f}".format(F_W/2),
                             x2="{:.4f}".format(F_W/2),
                             y1="-{:.4f}".format(P_L/2),
                             y2="-{:.4f}".format(S_L/2),
                             z1="{sh:.4f}".format(sh=S_h),
                             z2="{:.4f}".format(S_h+0.035),)
            self.run_command("define boundary")
            self.run_command("set solver freq range",resonant_frequency1=float(freq)-1.0, resonant_frequency2=float(freq)+1.0)
            self.run_command("pick face",component_name="component1",solid_name="feed")
            self.run_command("select port",
                            Xrange=f"-{F_W/2:.4f}",    # start X
                            XrangeEnd=f"{F_W/2:.4f}",  # end X
                            XrangeAdd=f"{7.92}*{S_h:.4f}",  # as string (no evaluation)
                            XrangeAddEnd=f"{7.92}*{S_h:.4f}",

                            Yrange="0",    # start Y (single plane)
                            YrangeEnd="0", # end Y same as start
                            YrangeAdd="{7.92}*{S_h:.4f}",
                            YrangeAddEnd="{7.92}*{S_h:.4f}",

                            Zrange=f"{S_h:.4f}",       # start Z
                            ZrangeEnd=f"{(S_h + 0.035):.4f}",  # end Z small thickness (e.g., 0.035 mm)
                            ZrangeAdd="0.0",
                            ZrangeAddEnd=f"{7.92}*{S_h:.4f}")
            self.run_command("run Solver")
            self.mws.save(path = file_location, include_results = True, allow_overwrite = True)
            
            # Close design if requested (default behavior)
            if close_design:
                self.de.close()

    # ------------------------
    # Dispatcher
    # ------------------------
    def create_and_run(self, family, freq_GHz, params, substrate_name, conductor_name):
        """
        family: string in FAMILIES
        params: list of length >=5 (param_a,param_b,feed_w,substrate_h,eps_r)
        """
        if family == "patch_rect":
            return self.build_patch_rect(freq_GHz, params, substrate_name, conductor_name)
        
        raise ValueError("Unsupported family: " + family)

    def extract_s11_results(self, cst_path=ANTENNA_PATH):
        """
        Extract S11 from a CST .cst file and compute resonant frequency & bandwidth with validation.
        Returns: (Fr_GHz, BW_MHz, S11_min_dB)
        
        Bandwidth is computed as the frequency span where S11 <= -10 dB (standard definition).
        All output frequencies are in GHz, bandwidth in MHz.
        """
        import sys
        
        # Load CST project results
        project = cst.results.ProjectFile(cst_path, allow_interactive=True)
        
        # Access 3D results module and the S11 data
        s11_item = project.get_3d().get_result_item(r"1D Results\S-Parameters\S1,1")

        # Get frequency and S11 data with validation
        freqs_raw = np.array(s11_item.get_xdata())  # frequency axis
        data = s11_item.get_data()
        
        # Validate frequency data
        if len(freqs_raw) == 0:
            print("[ERROR] No frequency data extracted from CST!", file=sys.stderr)
            return 0.0, 0.0, 0.0
        
        # Determine frequency unit based on range
        # Typical antenna frequencies: 0.5-10 GHz or 500-10000 MHz
        freq_min = np.min(freqs_raw)
        freq_max = np.max(freqs_raw)
        
        print(f"[DEBUG] Raw freq range: {freq_min:.6f} to {freq_max:.6f}")
        
        # If min > 100, likely in MHz; convert to GHz
        if freq_min > 100:
            freqs = freqs_raw / 1000.0  # MHz to GHz
            print(f"[DEBUG] Frequencies detected in MHz, converting to GHz")
        else:
            freqs = freqs_raw  # Already in GHz
            print(f"[DEBUG] Frequencies already in GHz")
        
        print(f"[DEBUG] Frequency range (GHz): {freqs.min():.6f} to {freqs.max():.6f}")
        
        # Extract S11 complex values from data tuples
        try:
            s11_complex = np.array([d[1] for d in data], dtype=complex)
        except (IndexError, TypeError) as e:
            print(f"[ERROR] Failed to extract S11 complex data: {e}", file=sys.stderr)
            print(f"[DEBUG] Data sample: {data[0] if len(data) > 0 else 'empty'}", file=sys.stderr)
            return 0.0, 0.0, 0.0
        
        # Convert to dB: S11_dB = 20*log10(|S11|)
        s11_magnitude = np.abs(s11_complex)
        
        # Validate S11 magnitude is in [0, 1] range (reflection coefficient)
        if np.any(s11_magnitude > 1.1):  # Allow small numerical errors
            print(f"[WARNING] S11 magnitudes exceed 1.0 (max: {np.max(s11_magnitude):.4f})")
            print(f"[DEBUG] This may indicate data extraction error or different S-parameter format")
        
        s11_db = 20 * np.log10(s11_magnitude + 1e-12)  # Add small offset to avoid log(0)
        
        print(f"[DEBUG] S11 dB range: {np.min(s11_db):.2f} to {np.max(s11_db):.2f} dB")
        
        # --- Find Resonant Frequency (minimum S11) ---
        min_idx = np.argmin(s11_db)
        Fr = freqs[min_idx]
        S11_min = s11_db[min_idx]
        
        print(f"[DEBUG] Resonant frequency: {Fr:.6f} GHz, S11_min: {S11_min:.2f} dB")

        # --- Find Bandwidth using -10 dB crossing points (STANDARD DEFINITION) ---
        # This finds the frequency span where S11 <= -10 dB
        below_10_mask = s11_db <= -10.0
        
        if np.any(below_10_mask):
            # Find continuous regions where S11 <= -10 dB
            indices = np.where(below_10_mask)[0]
            
            # Find the main resonance region (around minimum S11)
            # by finding the largest contiguous region
            if len(indices) > 1:
                # Group consecutive indices
                diff = np.diff(indices)
                jumps = np.where(diff > 1)[0]
                
                if len(jumps) > 0:
                    # Multiple disjoint regions - find the one with minimum S11
                    regions = []
                    start = 0
                    for jump in jumps:
                        regions.append(indices[start:jump+1])
                        start = jump + 1
                    regions.append(indices[start:])
                    
                    # Select region containing the minimum S11
                    region_with_min = None
                    for region in regions:
                        if min_idx in region:
                            region_with_min = region
                            break
                    
                    if region_with_min is not None:
                        indices = region_with_min
                
                f_low = freqs[indices[0]]
                f_high = freqs[indices[-1]]
                BW_GHz = f_high - f_low
                BW_MHz = BW_GHz * 1000  # Convert GHz to MHz
                
                print(f"[DEBUG] -10dB BW: {f_low:.6f} to {f_high:.6f} GHz = {BW_MHz:.2f} MHz")
            else:
                # Single point below -10 dB
                BW_MHz = 0.0
                print(f"[DEBUG] Only single frequency point below -10 dB")
        else:
            # No -10 dB crossing - check what's the best we can achieve
            BW_MHz = 0.0
            best_idx = np.argmin(np.abs(s11_db + 10))
            print(f"[WARNING] No frequencies reach -10 dB level")
            print(f"[DEBUG] Closest point: {freqs[best_idx]:.6f} GHz with S11={s11_db[best_idx]:.2f} dB")

        # Validate results
        if Fr < 0.1 or Fr > 20:
            print(f"[WARNING] Resonant frequency {Fr} GHz seems out of range for typical antenna", file=sys.stderr)
        
        if BW_MHz < 0:
            print(f"[WARNING] Negative bandwidth calculated: {BW_MHz} MHz", file=sys.stderr)
            BW_MHz = abs(BW_MHz)

        print(f"[RESULT] Fr={Fr:.6f} GHz, BW={BW_MHz:.2f} MHz, S11={S11_min:.2f} dB\n")
        
        return Fr, BW_MHz, S11_min
