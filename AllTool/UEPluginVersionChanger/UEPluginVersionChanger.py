# Author:Glax3210
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import platform
import subprocess
import logging
from pathlib import Path
import winreg
import glob
import re
import threading
import signal
import json

class ToolTip:
    """Create tooltip for widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0", 
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class UnrealPluginRebuilder:
    def __init__(self, root):
        """Initialize the Unreal Plugin Rebuilder GUI application."""
        self.root = root
        self.root.title("🔧 Unreal Plugin Rebuilder")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Set minimum window size
        self.root.minsize(800, 600)

        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename="unreal_plugin_rebuilder.log"
        )
        self.logger = logging.getLogger(__name__)

        # Variables to store file and folder paths
        self.uplugin_path = tk.StringVar()
        self.runuat_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.engine_version = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        # Platform-specific settings
        self.is_windows = platform.system() == "Windows"
        self.runuat_extension = ".bat" if self.is_windows else ".sh"
        self.runuat_filetype = [("Batch Files", "*.bat")] if self.is_windows else [("Shell Scripts", "*.sh")]

        # Process control
        self.process = None
        self.is_rebuilding = False
        self.start_button = None
        self.progress_bar = None
        self.output_text = None  # Initialize to None
        self.open_folder_btn = None
        self.last_output_folder = None

        # Config file for remembering paths
        self.config_file = "rebuilder_config.json"
        self.recent_paths = self._load_config()

        # Get available Unreal Engine versions
        self.engine_versions = self._get_engine_versions()
        if not self.engine_versions:
            self.engine_versions = ["No Unreal Engine versions found"]

        # Setup GUI first
        self._setup_gui()
        
        # Then set default engine version (after GUI is ready)
        self._set_default_engine()
        
        # Load previous paths if available
        self._load_recent_paths()

    def _load_config(self):
        """Load recent paths from config file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
        return {}

    def _save_config(self):
        """Save recent paths to config file."""
        try:
            config = {
                'last_uplugin': self.uplugin_path.get(),
                'last_output': self.output_path.get(),
                'last_engine': self.engine_version.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def _load_recent_paths(self):
        """Load recent paths into GUI."""
        if self.recent_paths.get('last_uplugin') and os.path.exists(self.recent_paths.get('last_uplugin', '')):
            self.uplugin_path.set(self.recent_paths['last_uplugin'])
            self._update_selection_indicator(self.uplugin_indicator, True)
        
        if self.recent_paths.get('last_output') and os.path.exists(self.recent_paths.get('last_output', '')):
            self.output_path.set(self.recent_paths['last_output'])
            self._update_selection_indicator(self.output_indicator, True)
        
        if self.recent_paths.get('last_engine') in self.engine_versions:
            self.engine_version.set(self.recent_paths['last_engine'])
            self._on_engine_select(None)

    def _set_default_engine(self):
        """Set default engine version to the latest one."""
        if self.engine_versions and self.engine_versions[0] != "No Unreal Engine versions found":
            # Set to the latest version (last in sorted list)
            default_version = self.engine_versions[-1]
            self.engine_version.set(default_version)
            self._on_engine_select(None)
            self.logger.info(f"Default engine version set to: {default_version}")

    def _get_engine_versions(self):
        """Retrieve installed Unreal Engine versions."""
        versions = []
        try:
            if self.is_windows:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EpicGames\Unreal Engine") as key:
                        i = 0
                        while True:
                            try:
                                version = winreg.EnumKey(key, i)
                                if re.match(r"^\d+\.\d+$", version):
                                    with winreg.OpenKey(key, version) as subkey:
                                        install_dir = winreg.QueryValueEx(subkey, "InstalledDirectory")[0]
                                        runuat_path = os.path.join(install_dir, "Engine", "Build", "BatchFiles", f"RunUAT{self.runuat_extension}")
                                        if os.path.isfile(runuat_path):
                                            versions.append(version)
                                i += 1
                            except OSError:
                                break
                except FileNotFoundError:
                    self.logger.warning("Unreal Engine registry key not found")
            else:
                base_path = "/Users/Shared/Epic Games" if platform.system() == "Darwin" else os.path.expanduser("~/Epic Games")
                if os.path.exists(base_path):
                    for folder in glob.glob(os.path.join(base_path, "UE_*")):
                        version = os.path.basename(folder).replace("UE_", "")
                        if re.match(r"^\d+\.\d+$", version):
                            runuat_path = os.path.join(folder, "Engine", "Build", "BatchFiles", f"RunUAT{self.runuat_extension}")
                            if os.path.isfile(runuat_path):
                                versions.append(version)
            versions.sort()
            return versions if versions else []
        except Exception as e:
            self.logger.error(f"Error retrieving engine versions: {str(e)}")
            return []

    def _setup_gui(self):
        """Set up the main GUI components with improved layout."""
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main container - CENTERED
        main_container = tk.Frame(self.root, bg="#f0f0f0")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # ===== HEADER =====
        header_frame = tk.Frame(main_container, bg="#2c3e50", height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        title_label = tk.Label(header_frame, text="🔧 Unreal Plugin Rebuilder", 
                               font=("Arial", 20, "bold"), bg="#2c3e50", fg="white")
        title_label.pack(pady=20)

        # ===== SCROLLABLE CONTENT AREA =====
        # Create a canvas with scrollbar for content
        canvas_frame = tk.Frame(main_container, bg="#f0f0f0")
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Content container - CENTERED with max width
        content_container = tk.Frame(canvas_frame, bg="#f0f0f0")
        content_container.grid(row=0, column=0)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Center the content
        content_frame = tk.Frame(content_container, bg="#f0f0f0")
        content_frame.pack(padx=40, pady=20, expand=True)
        
        # Instructions Frame
        instructions_frame = tk.LabelFrame(content_frame, text="📖 Instructions", 
                                          font=("Arial", 11, "bold"), bg="#f0f0f0", 
                                          fg="#2c3e50", padx=15, pady=10)
        instructions_frame.pack(fill="x", pady=(0, 15))
        
        instructions = (
            "1️⃣  Select your plugin file (.uplugin)\n"
            "2️⃣  Choose your Unreal Engine version (optional - latest selected by default)\n"
            "3️⃣  Select where to save the rebuilt plugin\n"
            "4️⃣  Click 'Start Rebuild' and monitor progress below"
        )
        tk.Label(instructions_frame, text=instructions, justify="left", 
                font=("Arial", 10), bg="#f0f0f0", fg="#34495e").pack(anchor="w")

        # ===== FILE SELECTION FRAME =====
        file_frame = tk.LabelFrame(content_frame, text="📁 File Selection", 
                                   font=("Arial", 11, "bold"), bg="#f0f0f0", 
                                   fg="#2c3e50", padx=15, pady=10)
        file_frame.pack(fill="x", pady=(0, 15))

        # UPlugin File
        uplugin_frame = tk.Frame(file_frame, bg="#f0f0f0")
        uplugin_frame.pack(fill="x", pady=5)
        
        tk.Label(uplugin_frame, text="Plugin File:", font=("Arial", 10, "bold"), 
                bg="#f0f0f0", width=15, anchor="w").pack(side="left", padx=(0, 10))
        
        uplugin_btn = tk.Button(uplugin_frame, text="Browse .uplugin", 
                               command=self._select_uplugin, bg="#3498db", 
                               fg="white", font=("Arial", 9), width=15, cursor="hand2")
        uplugin_btn.pack(side="left", padx=5)
        ToolTip(uplugin_btn, "Select the .uplugin file you want to rebuild")
        
        self.uplugin_indicator = tk.Label(uplugin_frame, text="○", font=("Arial", 12), 
                                         bg="#f0f0f0", fg="gray")
        self.uplugin_indicator.pack(side="left", padx=5)
        
        uplugin_path_label = tk.Label(file_frame, textvariable=self.uplugin_path, 
                                      font=("Arial", 9), bg="#f0f0f0", 
                                      fg="#7f8c8d", wraplength=700, anchor="w")
        uplugin_path_label.pack(fill="x", padx=(20, 0), pady=(0, 10))

        # Engine Version
        engine_frame = tk.Frame(file_frame, bg="#f0f0f0")
        engine_frame.pack(fill="x", pady=5)
        
        tk.Label(engine_frame, text="Engine Version:", font=("Arial", 10, "bold"), 
                bg="#f0f0f0", width=15, anchor="w").pack(side="left", padx=(0, 10))
        
        engine_dropdown = ttk.Combobox(engine_frame, textvariable=self.engine_version, 
                                      values=self.engine_versions, state="readonly", 
                                      width=25, font=("Arial", 9))
        engine_dropdown.pack(side="left", padx=5)
        engine_dropdown.bind("<<ComboboxSelected>>", self._on_engine_select)
        ToolTip(engine_dropdown, "Select the Unreal Engine version (latest by default)")
        
        self.engine_indicator = tk.Label(engine_frame, text="✓", font=("Arial", 12), 
                                        bg="#f0f0f0", fg="#27ae60")
        self.engine_indicator.pack(side="left", padx=5)

        # Output Folder
        output_frame = tk.Frame(file_frame, bg="#f0f0f0")
        output_frame.pack(fill="x", pady=5)
        
        tk.Label(output_frame, text="Output Folder:", font=("Arial", 10, "bold"), 
                bg="#f0f0f0", width=15, anchor="w").pack(side="left", padx=(0, 10))
        
        output_btn = tk.Button(output_frame, text="Browse Folder", 
                              command=self._select_output, bg="#3498db", 
                              fg="white", font=("Arial", 9), width=15, cursor="hand2")
        output_btn.pack(side="left", padx=5)
        ToolTip(output_btn, "Select where to save the rebuilt plugin")
        
        self.output_indicator = tk.Label(output_frame, text="○", font=("Arial", 12), 
                                        bg="#f0f0f0", fg="gray")
        self.output_indicator.pack(side="left", padx=5)
        
        output_path_label = tk.Label(file_frame, textvariable=self.output_path, 
                                     font=("Arial", 9), bg="#f0f0f0", 
                                     fg="#7f8c8d", wraplength=700, anchor="w")
        output_path_label.pack(fill="x", padx=(20, 0), pady=(0, 5))

        # ===== BUILD CONTROL FRAME =====
        control_frame = tk.LabelFrame(content_frame, text="⚙️ Build Control", 
                                     font=("Arial", 11, "bold"), bg="#f0f0f0", 
                                     fg="#2c3e50", padx=15, pady=10)
        control_frame.pack(fill="x", pady=(0, 15))

        # Progress Bar
        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar", 
                       troughcolor="#ecf0f1", background="#27ae60", 
                       thickness=25)
        
        self.progress_bar = ttk.Progressbar(control_frame, mode="indeterminate", 
                                           length=600, 
                                           style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Buttons Frame
        btn_frame = tk.Frame(control_frame, bg="#f0f0f0")
        btn_frame.pack()

        self.start_button = tk.Button(btn_frame, text="▶ Start Rebuild", 
                                      command=self._toggle_rebuild, bg="#27ae60", 
                                      fg="white", font=("Arial", 11, "bold"), 
                                      width=20, height=2, cursor="hand2")
        self.start_button.grid(row=0, column=0, padx=5)
        ToolTip(self.start_button, "Start the plugin rebuild process")

        self.open_folder_btn = tk.Button(btn_frame, text="📁 Open Output Folder", 
                                        command=self._open_output_folder, 
                                        bg="#95a5a6", fg="white", 
                                        font=("Arial", 10), width=20, 
                                        state="disabled", cursor="hand2")
        self.open_folder_btn.grid(row=0, column=1, padx=5)
        ToolTip(self.open_folder_btn, "Open the output folder after successful build")

        # ===== BUILD OUTPUT FRAME =====
        output_frame = tk.LabelFrame(content_frame, text="📋 Build Output", 
                                    font=("Arial", 11, "bold"), bg="#f0f0f0", 
                                    fg="#2c3e50", padx=10, pady=10)
        output_frame.pack(fill="both", expand=True)

        # Scrollable text widget for output
        output_scroll = tk.Scrollbar(output_frame)
        output_scroll.pack(side="right", fill="y")

        self.output_text = tk.Text(output_frame, height=12, wrap="word", 
                                   bg="#2c3e50", fg="#ecf0f1", 
                                   font=("Consolas", 9), 
                                   yscrollcommand=output_scroll.set)
        self.output_text.pack(fill="both", expand=True)
        output_scroll.config(command=self.output_text.yview)
        
        # Configure tags for colored output
        self.output_text.tag_config("error", foreground="#e74c3c")
        self.output_text.tag_config("success", foreground="#2ecc71")
        self.output_text.tag_config("info", foreground="#3498db")
        
        self._log_output("Ready to build. Select your plugin file and click 'Start Rebuild'.", "info")

        # ===== STATUS BAR =====
        status_frame = tk.Frame(main_container, bg="#34495e", height=30)
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.grid_propagate(False)
        
        status_label = tk.Label(status_frame, textvariable=self.status_text, 
                               bg="#34495e", fg="white", font=("Arial", 9), 
                               anchor="w", padx=10)
        status_label.pack(fill="both", expand=True)

    def _update_selection_indicator(self, indicator, is_valid):
        """Update the selection indicator (checkmark or circle)."""
        if is_valid:
            indicator.config(text="✓", fg="#27ae60")
        else:
            indicator.config(text="○", fg="gray")

    def _log_output(self, message, tag=""):
        """Add message to output text widget."""
        if self.output_text:  # Check if output_text exists
            self.output_text.insert("end", f"{message}\n", tag)
            self.output_text.see("end")
            self.root.update_idletasks()

    def _update_status(self, message):
        """Update status bar message."""
        self.status_text.set(message)
        self.root.update_idletasks()

    def _select_uplugin(self):
        """Open file dialog to select a .uplugin file."""
        try:
            initial_dir = os.path.dirname(self.uplugin_path.get()) if self.uplugin_path.get() else ""
            file_path = filedialog.askopenfilename(
                title="Select .uplugin File",
                filetypes=[("UPlugin Files", "*.uplugin"), ("All Files", "*.*")],
                initialdir=initial_dir
            )
            if file_path and self._validate_file(file_path, ".uplugin"):
                self.uplugin_path.set(file_path)
                self._update_selection_indicator(self.uplugin_indicator, True)
                self._update_status(f"Selected plugin: {os.path.basename(file_path)}")
                self._log_output(f"✓ Plugin file selected: {file_path}", "success")
                self.logger.info(f"Selected .uplugin file: {file_path}")
            elif file_path:
                self._update_selection_indicator(self.uplugin_indicator, False)
                messagebox.showerror("Invalid File", "Please select a valid .uplugin file.")
                self.logger.warning(f"Invalid .uplugin file selected: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select .uplugin file:\n{str(e)}")
            self.logger.error(f"Error selecting .uplugin file: {str(e)}")

    def _select_output(self):
        """Open folder dialog to select output folder."""
        try:
            initial_dir = self.output_path.get() if self.output_path.get() else ""
            folder_path = filedialog.askdirectory(
                title="Select Output Folder",
                initialdir=initial_dir
            )
            if folder_path and self._validate_directory(folder_path):
                self.output_path.set(folder_path)
                self._update_selection_indicator(self.output_indicator, True)
                self._update_status(f"Output folder: {folder_path}")
                self._log_output(f"✓ Output folder selected: {folder_path}", "success")
                self.logger.info(f"Selected output folder: {folder_path}")
            elif folder_path:
                self._update_selection_indicator(self.output_indicator, False)
                messagebox.showerror("Invalid Folder", "Please select a valid, writable folder.")
                self.logger.warning(f"Invalid output folder selected: {folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select output folder:\n{str(e)}")
            self.logger.error(f"Error selecting output folder: {str(e)}")

    def _on_engine_select(self, event):
        """Handle engine version selection and set RunUAT path."""
        selected_version = self.engine_version.get()
        
        # If no version selected or invalid, return without error
        if not selected_version or selected_version in ["No Unreal Engine versions found", "Error retrieving engine versions"]:
            self.runuat_path.set("")
            self.logger.warning("No valid engine version selected.")
            return

        try:
            if self.is_windows:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\EpicGames\\Unreal Engine\\{selected_version}") as key:
                    install_dir = winreg.QueryValueEx(key, "InstalledDirectory")[0]
                    runuat_path = os.path.join(install_dir, "Engine", "Build", "BatchFiles", f"RunUAT{self.runuat_extension}")
            else:
                base_path = "/Users/Shared/Epic Games" if platform.system() == "Darwin" else os.path.expanduser("~/Epic Games")
                runuat_path = os.path.join(base_path, f"UE_{selected_version}", "Engine", "Build", "BatchFiles", f"RunUAT{self.runuat_extension}")

            if self._validate_file(runuat_path, self.runuat_extension):
                self.runuat_path.set(runuat_path)
                self._update_status(f"Engine version: UE {selected_version}")
                self._log_output(f"✓ Engine version set: UE {selected_version}", "info")
                self.logger.info(f"Selected RunUAT path for UE {selected_version}: {runuat_path}")
            else:
                self.runuat_path.set("")
                messagebox.showerror("Engine Not Found", 
                                   f"RunUAT{self.runuat_extension} not found for Unreal Engine {selected_version}.\n\n"
                                   f"Expected location:\n{runuat_path}")
                self.logger.warning(f"RunUAT{self.runuat_extension} not found for UE {selected_version}")
        except Exception as e:
            self.runuat_path.set("")
            error_msg = f"Failed to locate RunUAT for Unreal Engine {selected_version}:\n{str(e)}"
            messagebox.showerror("Error", error_msg)
            self.logger.error(f"Error locating RunUAT for UE {selected_version}: {str(e)}")

    def _validate_file(self, file_path: str, extension: str) -> bool:
        """Validate if the file exists and has the correct extension."""
        return os.path.isfile(file_path) and Path(file_path).suffix.lower() == extension.lower()

    def _validate_directory(self, folder_path: str) -> bool:
        """Validate if the directory exists and is writable."""
        return os.path.isdir(folder_path) and os.access(folder_path, os.W_OK)

    def _check_output_exists(self, output: str) -> bool:
        """Check if the output folder contains a .uplugin file."""
        return any(Path(output).glob("*.uplugin"))

    def _toggle_rebuild(self):
        """Toggle between starting and stopping the rebuild process."""
        if not self.is_rebuilding:
            self._start_rebuild()
        else:
            self._stop_rebuild()

    def _start_rebuild(self):
        """Start the plugin rebuild process."""
        uplugin = self.uplugin_path.get()
        runuat = self.runuat_path.get()
        base_output = self.output_path.get()

        # Validate inputs - engine is optional (default is set)
        if not uplugin:
            messagebox.showerror("Missing Plugin File", 
                               "Please select a .uplugin file to rebuild.")
            self.logger.warning("Rebuild attempt without plugin file.")
            return

        if not base_output:
            messagebox.showerror("Missing Output Folder", 
                               "Please select an output folder.")
            self.logger.warning("Rebuild attempt without output folder.")
            return

        if not runuat:
            messagebox.showerror("Missing Engine", 
                               "No valid Unreal Engine version selected.\n\n"
                               "Please select an engine version from the dropdown.")
            self.logger.warning("Rebuild attempt without valid engine.")
            return

        if not self._validate_file(uplugin, ".uplugin"):
            messagebox.showerror("Invalid Plugin", "The selected .uplugin file is invalid or doesn't exist.")
            return

        if not self._validate_file(runuat, self.runuat_extension):
            messagebox.showerror("Invalid Engine", f"RunUAT{self.runuat_extension} not found for the selected engine.")
            return

        # Create output folder
        try:
            plugin_folder_name = os.path.basename(os.path.dirname(uplugin))
            output = os.path.join(base_output, plugin_folder_name)
            os.makedirs(output, exist_ok=True)
            if not self._validate_directory(output):
                messagebox.showerror("Invalid Output", f"Cannot write to output folder:\n{output}")
                return
            self.last_output_folder = output
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create output folder:\n{str(e)}")
            return

        # Check if output exists
        if self._check_output_exists(output):
            if not messagebox.askyesno("Overwrite?", 
                                      f"Output folder already contains a plugin:\n{output}\n\nOverwrite?",
                                      icon="warning"):
                self.logger.info("Rebuild cancelled by user.")
                return

        # Save config
        self._save_config()

        # Update UI
        self.is_rebuilding = True
        self.start_button.config(text="⏹ Stop Build", bg="#e74c3c")
        self.progress_bar.start(10)
        self.root.config(cursor="wait")
        self.output_text.delete("1.0", "end")
        self._log_output(f"{'='*60}", "info")
        self._log_output(f"Starting build process...", "info")
        self._log_output(f"Plugin: {os.path.basename(uplugin)}", "info")
        self._log_output(f"Engine: UE {self.engine_version.get()}", "info")
        self._log_output(f"Output: {output}", "info")
        self._log_output(f"{'='*60}\n", "info")
        self._update_status("Building plugin... Please wait")

        # Run rebuild in separate thread
        threading.Thread(target=self._run_rebuild_process, args=(uplugin, runuat, output), daemon=True).start()

    def _run_rebuild_process(self, uplugin: str, runuat: str, output: str):
        """Run the rebuild process in a separate thread."""
        try:
            # Construct command
            if self.is_windows:
                command = f'"{runuat}" BuildPlugin -Plugin="{uplugin}" -Package="{output}"'
            else:
                command = f'sh "{runuat}" BuildPlugin -Plugin="{uplugin}" -Package="{output}"'

            self.logger.info(f"Executing command: {command}")

            # Run command with real-time output
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output in real-time
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    tag = "error" if "error" in line.lower() or "fail" in line.lower() else ""
                    self.root.after(0, lambda l=line, t=tag: self._log_output(l.rstrip(), t))

            self.process.wait()

            # Check result
            if self.process.returncode == 0:
                self.root.after(0, self._on_build_success)
            else:
                self.root.after(0, lambda: self._on_build_failure("Build process failed. Check output above."))

        except Exception as e:
            self.root.after(0, lambda: self._on_build_failure(f"Error during build: {str(e)}"))
        finally:
            self.root.after(0, self._reset_ui)

    def _on_build_success(self):
        """Handle successful build."""
        self._log_output("\n" + "="*60, "success")
        self._log_output("✓ BUILD SUCCESSFUL!", "success")
        self._log_output("="*60, "success")
        self._update_status("✓ Build completed successfully!")
        messagebox.showinfo("Success! 🎉", 
                          f"Plugin rebuilt successfully!\n\nOutput location:\n{self.last_output_folder}")
        self.open_folder_btn.config(state="normal", bg="#3498db")
        self.logger.info("Plugin rebuild completed successfully.")

    def _on_build_failure(self, message):
        """Handle build failure."""
        self._log_output("\n" + "="*60, "error")
        self._log_output("✗ BUILD FAILED", "error")
        self._log_output("="*60, "error")
        self._update_status("✗ Build failed")
        messagebox.showerror("Build Failed", f"{message}\n\nCheck the build output for details.")
        self.logger.error(f"Build failed: {message}")

    def _stop_rebuild(self):
        """Stop the running rebuild process."""
        if self.process and self.is_rebuilding:
            self._terminate_process()
            self._log_output("\n⚠ Build stopped by user", "error")
            self._update_status("Build stopped")
            messagebox.showinfo("Stopped", "Build process has been stopped.")
            self.logger.info("Rebuild process stopped by user.")
        self._reset_ui()

    def _terminate_process(self):
        """Safely terminate the running process."""
        if self.process:
            try:
                if self.is_windows:
                    subprocess.run(f"taskkill /PID {self.process.pid} /T /F", shell=True)
                else:
                    self.process.send_signal(signal.SIGTERM)
                self.process.wait(timeout=5)
            except Exception as e:
                self.logger.error(f"Error terminating process: {str(e)}")
            finally:
                self.process = None

    def _reset_ui(self):
        """Reset the UI after rebuild."""
        self.progress_bar.stop()
        self.start_button.config(text="▶ Start Rebuild", bg="#27ae60")
        self.root.config(cursor="")
        self.is_rebuilding = False
        self.process = None
        if not self.last_output_folder or not self._check_output_exists(self.last_output_folder):
            self._update_status("Ready")

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.last_output_folder and os.path.exists(self.last_output_folder):
            try:
                if self.is_windows:
                    os.startfile(self.last_output_folder)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", self.last_output_folder])
                else:
                    subprocess.run(["xdg-open", self.last_output_folder])
                self.logger.info(f"Opened output folder: {self.last_output_folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder:\n{str(e)}")
                self.logger.error(f"Error opening folder: {str(e)}")


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = UnrealPluginRebuilder(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Application startup failed: {str(e)}")
        messagebox.showerror("Fatal Error", f"Failed to start application:\n{str(e)}")