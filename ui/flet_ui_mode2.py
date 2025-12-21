# ui/flet_ui_mode2.py
import flet as ft
import threading
import os
import queue
import pandas as pd

from ai_core.parameter_engine import ParameterEngine
from cst_interface.cst_driver_mode2 import CSTDriverMode2
from feedback.feedback_logger import log_feedback
from feedback.ai_quick_retrain import quick_retrain
from ai_core.ai_config import FAMILIES, ANTENNA_PATH

engine = ParameterEngine()
cst = CSTDriverMode2()

FEEDBACK_CSV = r"feedback\ai_feedback_mode2.csv"
ANTENNA_PATH = ANTENNA_PATH

# Queue for thread-safe UI updates
_ui_queue = queue.Queue()

def enqueue_ui(fn):
    """Put a callable in the UI queue to be executed on the UI thread."""
    _ui_queue.put(fn)

def main(page: ft.Page):
    page.title = "AI Antenna Optimization — Mode 2"
    page.window_width = 1000
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = True

    # Process UI queue periodically
    def process_ui_queue():
        while not _ui_queue.empty():
            try:
                fn = _ui_queue.get_nowait()
                fn()
            except queue.Empty:
                break
        # Schedule next check
        threading.Timer(0.1, process_ui_queue).daemon = True
        threading.Timer(0.1, process_ui_queue).start()
    
    process_ui_queue()

    # ---------------- UI ELEMENTS ----------------
    family_dd = ft.Dropdown(label="Family", width=300,
                            options=[ft.dropdown.Option(x) for x in FAMILIES])

    freq_field = ft.TextField(label="Resonant Frequency (GHz)", width=200)
    bw_field = ft.TextField(label="Bandwidth (MHz)", width=200)

    substrate_dd = ft.Dropdown(label="Substrate", width=240,
                               options=[
                                   ft.dropdown.Option("FR-4 (lossy)"),
                                   ft.dropdown.Option("Rogers RT-duroid 5880 (lossy)"),
                                   ft.dropdown.Option("Taconic TLY-3 (lossy)")
                               ])

    conductor_dd = ft.Dropdown(label="Conductor", width=240,
                               options=[
                                   ft.dropdown.Option("Copper (annealed)"),
                                   ft.dropdown.Option("Aluminum"),
                                   ft.dropdown.Option("Silver")
                               ])

    advanced_chk = ft.Checkbox(label="Advanced (edit AI params)", value=False)

    pa = ft.TextField(label="patch_W", width=120)
    pb = ft.TextField(label="patch_L", width=120)
    fw = ft.TextField(label="feed_width", width=120)
    sh = ft.TextField(label="substrate_h", width=120)
    er = ft.TextField(label="eps_r", width=120)

    result_display = ft.Text("Results will appear here.", selectable=True, size=14)

    # Loading indicator - simple container, no overlay
    loading_text = ft.Text("Processing...", size=16, color=ft.colors.WHITE)
    
    loading_indicator = ft.Container(
        visible=False,
        width=330,
        padding=20,
        content=ft.Column(
            controls=[
                ft.ProgressRing(width=70, height=70),
                loading_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )
    )

    def show_loading(msg):
        append_result(msg)
        loading_indicator.visible = True
        loading_text.value = msg
        page.update()

    def hide_loading():
        loading_indicator.visible = False
        page.update()
    
    def append_result(msg):
        """Append message to result display (both overlay and main display)"""
        result_display.value += msg + "\n"
        page.update()

    def show_snack(msg):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            action="OK",
            open=True,
            duration=5000    # stays visible longer
        )
        page.update()

    # ---------------- BACKGROUND PIPELINE ----------------
    def pipeline(family, Fr_t, BW_t, substrate, conductor):
        try:
            # Clear previous results
            result_display.value = ""
            page.update()
            
            show_loading("AI: Inverse prediction...")
            params = engine.predict(family, Fr_t, BW_t)
            
            # Ensure params has exactly 5 elements: [param_a, param_b, feed_width, substrate_h, eps_r]
            if not isinstance(params, (list, tuple)) or len(params) < 5:
                show_snack(f"Error: AI returned invalid params: {params}")
                hide_loading()
                return

            # Update UI with AI params safely
            def fill():
                try:
                    pa.value = f"{params[0]:.6f}"        # param_a
                    pb.value = f"{params[1]:.6f}"        # param_b
                    fw.value = f"{params[2]:.6f}"        # feed_width
                    sh.value = f"{params[3]:.6f}"        # substrate_h
                    er.value = f"{params[4]:.6f}"        # eps_r
                    page.update()
                except Exception as ex:
                    print(f"Error filling UI: {ex}")
            enqueue_ui(fill)
            
            # Display initial inverse prediction
            enqueue_ui(lambda: append_result(f" Inverse prediction:\nParams: {[f'{p:.6f}' for p in params]}"))

            # Build CST params dict
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
                show_snack(f"Error building CST params: {ex}")
                hide_loading()
                return

            show_loading("CST: Building model...")
            cst.standard_antenna("Microstrip Patch", "Rectangular",
                                 Fr_t, substrate, conductor, cst_params)

            show_loading("CST: Extracting S11...")
            cst_path = ANTENNA_PATH
            Fr_a, BW_a, S11 = cst.extract_s11_results(cst_path)

            show_loading("Logging feedback...")
            # params should have exactly 5 elements: [param_a, param_b, feed_width, substrate_h, eps_r]
            params_for_log = list(params[:5]) if len(params) >= 5 else list(params) + [0] * (5 - len(params))
            log_feedback(family, Fr_t, BW_t, params_for_log, Fr_a, BW_a, S11)

            show_loading("Quick retrain...")
            quick_retrain()

            def update_results():
                final_msg = (
                    f"\n SIMULATION COMPLETE\n\n"
                    f"Target: Fr={Fr_t:.3f} GHz, BW={BW_t:.2f} MHz\n"
                    f"Actual: Fr={Fr_a:.3f} GHz, BW={BW_a:.2f} MHz, S11={S11:.2f} dB\n\n"
                    f"Final Params: {[f'{p:.6f}' for p in params]}"
                )
                result_display.value += final_msg
                page.update()

            enqueue_ui(update_results)
            enqueue_ui(hide_loading)  # Hide loading after results are displayed

        except Exception as ex:
            hide_loading()
            show_snack(f"Pipeline error: {str(ex)}")

    # ---------------- BUTTON EVENTS ----------------
    def on_generate(e):
        try:
            family = family_dd.value
            if not family:
                return show_snack("Select antenna family")

            Fr_t = float(freq_field.value)
            BW_t = float(bw_field.value)
        except:
            return show_snack("Enter valid frequency & bandwidth")

        substrate = substrate_dd.value or "FR-4 (lossy)"
        conductor = conductor_dd.value or "Copper (annealed)"

        threading.Thread(
            target=pipeline,
            args=(family, Fr_t, BW_t, substrate, conductor),
            daemon=True
        ).start()

    def on_dashboard(e):
        try:
            if not os.path.exists(FEEDBACK_CSV):
                return show_snack("No feedback file yet")

            df = pd.read_csv(FEEDBACK_CSV)
            if df.empty:
                return show_snack("Feedback file is empty")

            df["freq_err"] = df["actual_Fr_GHz"] - df["target_Fr_GHz"]
            df["bw_err"] = df["actual_BW_MHz"] - df["target_BW_MHz"]

            show_snack(
                f"Avg Freq Error: {df.freq_err.mean():.3f} GHz\n"
                f"Avg BW Error: {df.bw_err.mean():.2f} MHz"
            )
        except Exception as ex:
            show_snack(f"Dashboard error: {ex}")

    # ---------------- LAYOUT ----------------
    # Main layout - controls at top with padding, results at bottom
    page.add(
        ft.Column([
            # Top section: Input controls with padding
            ft.Container(
                content=ft.Column([
                    ft.Row([family_dd, freq_field, bw_field]),
                    ft.Row([substrate_dd, conductor_dd]),
                    ft.Row([
                        ft.ElevatedButton("Generate & Simulate", on_click=on_generate),
                        ft.ElevatedButton("Show Dashboard", on_click=on_dashboard),
                    ]),
                    advanced_chk,
                    ft.Row([pa, pb, fw, sh, er]),
                ], spacing=10),
                padding=ft.padding.only(top=100)
            ),
            
            ft.Divider(),
            
            # Bottom section: Results display (full width, stays at bottom)
            ft.Container(
                content=ft.Column([
                    ft.Text("Results:", size=14, weight="bold"),
                    ft.Container(
                        content=ft.Column([result_display], scroll=ft.ScrollMode.AUTO),
                        border=ft.border.all(1, ft.colors.GREY_700),
                        padding=10,
                        height=300,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([loading_indicator]),
                        padding=ft.padding.only(left=50),
                        height=300,
                        expand=True
                    ),
                ], expand=True, spacing=5),
                padding=ft.padding.only(left=20, right=20, bottom=20),
                expand=True
            )
        ], spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
    )

if __name__ == "__main__":
    ft.app(target=main)
