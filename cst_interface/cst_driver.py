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
        
    def extract_s11_results(self,cst_path=ANTENNA_PATH):
        """
        Extract S11 from a CST .cst file and compute resonant frequency & bandwidth.
        Returns: (Fr_GHz, BW_GHz, S11_min_dB)
        """
        # Load CST project results
        project = cst.results.ProjectFile(cst_path, allow_interactive=True)
        

        # Access 3D results module and the S11 data
        s11_item = project.get_3d().get_result_item(r"1D Results\S-Parameters\S1,1")

        # Get frequency (GHz) and S11 data (complex values)
        freqs = np.array(s11_item.get_xdata())  # typically in GHz
        data = s11_item.get_data()
        
        # Extract S11 complex values from the data tuples
        s11_complex = np.array([d[1] for d in data])
        s11_db = 20 * np.log10(np.abs(s11_complex))
        
        # --- Find Resonant Frequency (minimum S11) ---
        min_idx = np.argmin(s11_db)
        Fr = freqs[min_idx]
        S11_min = s11_db[min_idx]

        # --- Find Bandwidth (-10 dB crossing points) ---
        below_10_mask = s11_db <= -10
        if np.any(below_10_mask):
            indices = np.where(below_10_mask)[0]
            f_low = freqs[indices[0]]
            f_high = freqs[indices[-1]]
            BW = f_high - f_low
        else:
            BW = 0.0  # no -10 dB crossings

        return Fr, BW, S11_min
        
    def standard_antenna(self, family, shape, freq, substrate, conductor, params, retry=False, firsttime=True):
        if retry and not firsttime:
            print("Retrying antenna creation with corrected parameters...", params)
            self.de.close()

        if family == "Microstrip Patch" and shape == "Rectangular":
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
            self.mws.save(path = ANTENNA_PATH, include_results = True, allow_overwrite = True)
            self.de.close()

