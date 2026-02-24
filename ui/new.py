import flet as f
import queue
import threading
from pipeline import run_once, run_iterative
import os
from ai_core import ai_config

_ui_queue = queue.Queue()
_shutdown_flag = False
_timer_ref = None

def enqueue_ui(fn):
    """Put a callable in the UI queue to be executed on the UI thread."""
    _ui_queue.put(fn)



def main(page : f.Page):
    global _shutdown_flag, _timer_ref
    
    # Reset shutdown flag on startup
    _shutdown_flag = False
    
    def run_in_thread(fn):
        threading.Thread(target=fn, daemon=True).start()
    
    def on_close(e):
        global _shutdown_flag
        _shutdown_flag = True
        if _timer_ref:
            _timer_ref.cancel()
    
    page.on_close = on_close

    def process_ui_queue():
        global _shutdown_flag, _timer_ref
        
        if _shutdown_flag:
            return
        
        while not _ui_queue.empty():
            try:
                fn = _ui_queue.get_nowait()
                fn()
            except queue.Empty:
                break
        
        # Schedule next check only if not shutting down
        if not _shutdown_flag:
            _timer_ref = threading.Timer(0.1, process_ui_queue)
            _timer_ref.daemon = True
            _timer_ref.start()
    
    process_ui_queue()

    def route_change(route):
        print(route)
        page.views.clear()
        if route.data=='/':
            page.views.append(home_view)
            home_nav_bar.selected_index=0
        elif route.data=="/settings":
            page.views.append(settings_view)
            setting_nav_bar.selected_index=1
        elif route.data=="/information":
            page.views.append(information_view)
            information_nav_bar.selected_index=2
        elif route.data=="/create/antenna":
            page.views.append(create_antenna_view)
        elif route.data=="/create/dataset":
            page.views.append(create_dataset_view)
        elif route.data=="/learn/model":
            page.views.append(model_view)
        elif route.data=="/learn/train":
            page.views.append(auto_train_view)
        elif route.data=="/optimize/antenna":
            page.views.append(optimize_antenna_view)
        elif route.data=="/history":
            page.views.append(history_view)
        
        page.update()

    def route_revert(view):
        pass

    def nav_change(event):
        if event.data == '1':
            page.go(settings_view.route)
        elif event.data == '2':
            page.go(information_view.route)
        else:
            page.go(home_view.route)

    home_nav_bar = f.NavigationBar(
        destinations=[
            f.NavigationBarDestination(icon=f.Icons.HOME_OUTLINED, selected_icon=f.Icons.HOME, label="Home"),
            f.NavigationBarDestination(icon=f.Icons.SETTINGS_OUTLINED, selected_icon=f.Icons.SETTINGS, label="Settings"),
            f.NavigationBarDestination(icon=f.Icons.INFO_OUTLINED, selected_icon=f.Icons.INFO, label="Information"),
        ],
        selected_index=0,
        on_change=nav_change,
        elevation=10,
    )
    home_view = f.View(
        route="/",
        appbar=home_nav_bar,
        controls=[
            f.ResponsiveRow(
                col=1,
                spacing=20,
                controls=[
                    f.Card(
                        content = f.Container(
                            content=f.Text(
                                    value="Antenna Optimization System", 
                                    theme_style=f.TextThemeStyle.HEADLINE_MEDIUM, 
                                    color=f.Colors.BLACK, 
                                    text_align=f.TextAlign.CENTER, 
                                    weight=f.FontWeight.BOLD
                            ),
                            padding=f.padding.symmetric(vertical=10, horizontal=10)
                        ),
                        elevation=5,
                        shape=f.RoundedRectangleBorder(radius=5),
                        color=f.Colors.PINK,
                        width=page.width,
                        margin=f.margin.only(top=10),
                    ),
                    f.Card(
                        content=f.Container(
                            content=f.Column(
                                controls=[
                                    f.Text(value="Create", theme_style=f.TextThemeStyle.TITLE_MEDIUM),
                                    f.Row(
                                        controls=[
                                            f.FilledTonalButton(text="Antenna", icon=f.Icons.AUTO_AWESOME, on_click=lambda x: page.go("/create/antenna"), on_hover=None, style=f.ButtonStyle(shape=f.BeveledRectangleBorder(radius=5),padding=f.padding.symmetric(horizontal=10))),
                                            f.FilledTonalButton(text="Dataset", icon=f.Icons.AUTO_GRAPH, on_click=lambda x: page.go("/create/dataset"), on_hover=None, style=f.ButtonStyle(shape=f.BeveledRectangleBorder(radius=5),padding=f.padding.symmetric(horizontal=10))),
                                        ],
                                    ),
                                ],
                            ),
                            padding=10,
                        ),
                    ),
                    f.Card(
                        content=f.Container(
                            content=f.Column(
                                controls=[
                                    f.Text(value="Learning", theme_style=f.TextThemeStyle.TITLE_MEDIUM),
                                    f.Row(
                                        controls=[
                                            f.FilledTonalButton(text="Models", icon=f.Icons.AUTO_AWESOME_MOSAIC, on_click=lambda x: page.go("/learn/model"), on_hover=None, style=f.ButtonStyle(shape=f.BeveledRectangleBorder(radius=5),padding=f.padding.symmetric(horizontal=10))),
                                            f.FilledTonalButton(text="Auto-Train", icon=f.Icons.AUTO_MODE, on_click=lambda x: page.go("/learn/train"), on_hover=None, style=f.ButtonStyle(shape=f.BeveledRectangleBorder(radius=5),padding=f.padding.symmetric(horizontal=10))),
                                        ],
                                    ),
                                ],
                            ),
                            padding=10,
                        ),
                    ),
                    

                    f.FilledTonalButton(text="Optimize Antenna", icon=f.Icons.AUTO_FIX_NORMAL, on_click=lambda x: page.go("/optimize/antenna"), on_hover=None, style=f.ButtonStyle(shape=f.BeveledRectangleBorder(radius=5),padding=f.padding.symmetric(horizontal=10))),
                    f.FilledTonalButton(text="View History", icon=f.Icons.HISTORY, on_click=lambda x: page.go("/history"), on_hover=None, style=f.ButtonStyle(shape=f.BeveledRectangleBorder(radius=5),padding=f.padding.symmetric(horizontal=10))),
                ],
            ),
        ],
    )

    setting_nav_bar = f.NavigationBar(
        destinations=[
            f.NavigationBarDestination(icon=f.Icons.HOME_OUTLINED, selected_icon=f.Icons.HOME, label="Home"),
            f.NavigationBarDestination(icon=f.Icons.SETTINGS_OUTLINED, selected_icon=f.Icons.SETTINGS, label="Settings"),
            f.NavigationBarDestination(icon=f.Icons.INFO_OUTLINED, selected_icon=f.Icons.INFO, label="Information"),
        ],
        selected_index=1,
        on_change=nav_change,
        elevation=10,
    )
    settings_view = f.View(
        "/settings",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Settings"),
            center_title=True
        ),
        controls=[
            setting_nav_bar,
        ],
    )

    information_nav_bar = f.NavigationBar(
        destinations=[
            f.NavigationBarDestination(icon=f.Icons.HOME_OUTLINED, selected_icon=f.Icons.HOME, label="Home"),
            f.NavigationBarDestination(icon=f.Icons.SETTINGS_OUTLINED, selected_icon=f.Icons.SETTINGS, label="Settings"),
            f.NavigationBarDestination(icon=f.Icons.INFO_OUTLINED, selected_icon=f.Icons.INFO, label="Information"),
        ],
        selected_index=2,
        on_change=nav_change,
        elevation=10,
    )
    information_view = f.View(
        "/information",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Information"),
            center_title=True
        ),
        controls=[
            information_nav_bar,
        ],
    )

    def update_path(e: f.FilePickerResultEvent):
        print(e)
        project_location.value = e.path + "\\" + project_name.value
        page.update(project_location)
    def open_file_picker(e):
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()

    def get_shapes(event):
        opt = []
        shp=[]
        if antenna_family.value == "Microstrip Patch":
            shp = ["Rectangle"]
        elif antenna_family.value == "AMC Cell":
            shp = ["Square"]
        for i in shp:
            opt.append(f.DropdownOption(key=i, content=f.Text(value=i)))
        antenna_shape.options = opt
        antenna_shape.value = "  "
        page.update(antenna_shape)
    
    def confirm(event):
        text = f"This design targets a {antenna_family.value} antenna in {antenna_shape.value} shape for resonant frequency of {target_freq.value} and Bandwidth of {target_bandwidth.value}.\n{substrate.value} for substrate and {conductor.value} for conductor."
        create_dialog.content = f.Text(value=text)
        
        page.open(create_dialog)
    
    def continue_fn(event):
        try:
            target_Fr = float(target_freq.value)
            target_BW = float(target_bandwidth.value)
            file_location = project_location.value
            os.mkdir(file_location)
            file_location = file_location + "\\" + f"{project_name.value}.cst"
            print(file_location)
            
            substrate_name = substrate.value
            conductor_name = conductor.value

        except Exception:
            print("Invalid input")
            return

        def task():
            try:
                page.close(create_dialog)
                
                # Check if persistent mode is enabled
                use_iterative = persistent_mode.value
                
                if use_iterative:
                    result = run_iterative(
                        target_Fr_GHz=target_Fr,
                        target_BW_MHz=target_BW,
                        substrate=substrate_name,
                        conductor=conductor_name,
                        file_location=file_location,
                        verbose=True,
                        close_final_design=False  # Keep design open for persistent mode
                    )
                    params, Fr_a, BW_a, S11, iterations, history, best_iter = result
                    
                    def update_ui():
                        print("\n" + "="*70)
                        print("ITERATIVE MODE COMPLETE - DETAILED RESULTS")
                        print("="*70)
                        print(f"Total Iterations: {iterations}")
                        print(f"Best Result from Iteration: {best_iter}")
                        print(f"\nFinal AI Params: W={params[0]*1e3:.2f}mm, L={params[1]*1e3:.2f}mm, feed_w={params[2]*1e3:.2f}mm, h={params[3]*1e3:.2f}mm")
                        print(f"Final Result: Fr={Fr_a:.4f} GHz, BW={BW_a:.2f} MHz, S11={S11:.2f} dB")
                        
                        print(f"\n{'='*70}")
                        print("S11 IMPROVEMENT THROUGHOUT ITERATIONS")
                        print(f"{'='*70}")
                        for h in history:
                            is_final = " [FINAL OUTPUT]" if h.get('is_final', False) else ""
                            is_best = " ← BEST FROM ITERATIONS" if h['iteration'] == best_iter else ""
                            print(f"  Iter {h['iteration']:2d}: Fr={h['Fr']:.4f} GHz (err {h['Fr_error']*1000:6.2f}MHz) | "
                                  f"BW={h['BW']:6.2f} MHz (err {h['BW_error']:6.2f}MHz) | S11={h['S11']:7.2f} dB{is_best}{is_final}")
                        
                        print(f"\n{'='*70}")
                        print("LEARNING SYSTEM STATUS")
                        print(f"{'='*70}")
                        print("✓ All iterations logged to feedback system")
                        print("✓ Quick retraining triggered (if sufficient samples)")
                        print("  The AI model will learn from this optimization run")
                        print(f"{'='*70}\n")
                    
                    enqueue_ui(update_ui)
                else:
                    params, Fr_a, BW_a, S11 = run_once(
                        target_Fr_GHz=target_Fr,
                        target_BW_MHz=target_BW,
                        substrate=substrate_name,
                        conductor=conductor_name,
                        file_location=file_location
                    )

                    def update_ui():
                        print("AI Params:", params)
                        print(f"Actual Fr={Fr_a:.3f} GHz")
                        print(f"Actual BW={BW_a:.2f} MHz")
                        print(f"S11={S11:.2f} dB")

                    enqueue_ui(update_ui)

            except Exception as e:
                print("Pipeline error:", e)

        run_in_thread(task)

    project_name = f.TextField(label="Project Name")
    project_location = f.TextField(label="Project Directory")
    target_freq = f.TextField(label="Target Frequency", width=163)
    target_bandwidth = f.TextField(label="Target Bandwidth", width=163)
    antenna_family = f.Dropdown(
        options=[
            f.DropdownOption(key="Microstrip Patch", content=f.Text(value="Microstrip Patch")),
            f.DropdownOption(key="AMC Cell", content=f.Text(value="AMC Cell")),
        ],
        on_change=get_shapes,
        label="Family",
        width=184,
    )
    antenna_shape = f.Dropdown(editable=True, label="Shape", width=140,)
    substrate = f.Dropdown(
        options=[
            f.DropdownOption(key="FR-4 (lossy)", content=f.Text(value="FR-4 (lossy)")),
            f.DropdownOption(key="Rogers", content=f.Text(value="Rogers")),
            f.DropdownOption(key="Denim", content=f.Text(value="Denim")),
        ],
        label="Substrate",
        width=163,
    )
    conductor = f.Dropdown(
        options=[
            f.DropdownOption(key="Copper (annealed)", content=f.Text(value="Copper (annealed)")),
            f.DropdownOption(key="Silver", content=f.Text(value="Silver")),
            f.DropdownOption(key="Gold", content=f.Text(value="Gold")),
        ],
        label="Conductor",
        width=163,
    )
    persistent_mode = f.Checkbox(label="Persistent Mode")
    show_output = f.Checkbox(label="Show Output")
    create_dialog = f.AlertDialog(
        modal=True,
        title="Please Confirm",
        actions=[
            f.TextButton(text="Continue", on_click=continue_fn),
            f.TextButton(text="Cancel", on_click=lambda x: page.close(create_dialog)),
        ],
        alignment=f.alignment.center,
    )
    file_picker = f.FilePicker(on_result=update_path)

    create_antenna_view = f.View(
        "/create/antenna",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Generate New Antenna"),
            center_title=True
        ),
        controls=[
            f.Column(
                scroll=f.ScrollMode.AUTO,
                expand=True,
                controls=[
                    f.Card(
                        content=f.Container(
                            content=f.Column(
                                controls=[
                                    f.Text(value="Project Details : "),
                                    project_name,
                                    f.Row(
                                        controls=[
                                        project_location,
                                        f.IconButton(icon=f.Icons.DRIVE_FILE_MOVE_RTL, on_click=open_file_picker)
                                        ],
                                    ),
                                ]
                            ),
                            padding=20,
                        ),
                    ),
                    f.Card(
                        content=f.Container(
                            content=f.Column(
                                controls=[
                                    f.Text(value="Physical Properties : "),
                                    f.Row(
                                        controls=[
                                            antenna_family,
                                            antenna_shape,
                                        ],
                                    ),
                                    f.Row(
                                        controls=[
                                            substrate,
                                            conductor,
                                        ],
                                        col=2,
                                    ),
                                ]
                            ),
                            padding=20,
                        ),
                    ),
                    f.Card(
                        content=f.Container(
                            content=f.Column(
                                controls=[
                                    f.Text(value="Elerctrical Properties : "),
                                    f.Row(
                                        controls=[
                                            target_freq,
                                            target_bandwidth,
                                        ],
                                    ),
                                ],
                            ),
                            padding=20,
                        ),
                    ),
                    f.Card(
                        content=f.Container(
                            content=f.Column(
                                controls=[
                                    f.Text(value="Advanced Options : "),
                                    persistent_mode,
                                    show_output,
                                ],
                            ),
                            padding=20,
                        ),
                    ),
                    f.Container(
                        content=f.Row(
                            controls=[
                                f.IconButton(icon=f.Icons.ARROW_BACK_IOS, on_click=lambda x:page.go("/")),
                                f.FilledTonalButton(
                                    text="Start", 
                                    icon=f.Icons.AUTO_AWESOME,
                                    style=f.ButtonStyle(
                                        shape=f.RoundedRectangleBorder(radius=10),
                                        padding={
                                            f.ControlState.DEFAULT: f.padding.symmetric(horizontal=40, vertical=15),
                                            f.ControlState.HOVERED: f.padding.symmetric(horizontal=50,vertical=20),
                                        },
                                    ),
                                    on_click=confirm
                                ),
                            ],
                        ),
                        alignment=f.alignment.center,
                        padding=f.padding.only(left=100)
                    ),
                ]
            )
        ],
    )
    
    create_dataset_view = f.View(
        "/create/dataset",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Generate New Dataset"),
            center_title=True
        ),
    )
    
    model_view = f.View(
        "/learn/model",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Model Configuration"),
            center_title=True
        ),
    )
    
    auto_train_view = f.View(
        "/learn/train",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Auto-Train Mode"),
            center_title=True
        ),
    )

    optimize_antenna_view = f.View(
        "/optimze/antenna",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("Optimize Antenna"),
            center_title=True
        ),
    )
    
    history_view = f.View(
        "/history",
        appbar=f.AppBar(
            leading=f.IconButton(icon=f.Icons.ARROW_BACK, on_click=lambda x:page.go("/")),
            title=f.Text("History"),
            center_title=True
        ),
    )

    #page.window.width = 430
    #page.window.height = 892
    #page.window.resizable = True
    page.title = "AI Antenna Design"
    page.theme = f.Theme(color_scheme_seed=f.Colors.YELLOW)
    page.on_route_change = route_change
    page.on_view_pop = route_revert
    page.navigation_bar = f.NavigationBar(
        destinations=[
            f.NavigationBarDestination(icon=f.Icons.INFO_OUTLINED, selected_icon=f.Icons.INFO, label="Information"),
            f.NavigationBarDestination(icon=f.Icons.SETTINGS_OUTLINED, selected_icon=f.Icons.SETTINGS, label="Settings")
        ],
        on_change=nav_change,
        elevation=10,
    )
    page.go(page.route)

if __name__ == "__main__":
    f.app(target=main)
