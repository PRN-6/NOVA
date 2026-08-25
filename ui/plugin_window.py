import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import os
import subprocess
import shutil
import platform
import sounddevice as sd
from plugins.manager import plugin_manager
from plugins.profile_manager import profile_manager

logger = logging.getLogger("NOVA.DashboardWindow")

class PluginManagerWindow:
    """
    NOVA Control Center & Plugin Hub:
    - User Profile & Assistant Configuration
    - Installed Plugins Manager with Hot-Reload
    - Custom Plugin Creator Wizard & File Installer
    - Live Diagnostics & Activity Log
    """
    def __init__(self, parent_root=None):
        self.parent_root = parent_root
        self.window = None

    def open(self):
        """Opens or brings the Control Center to the foreground."""
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent_root) if self.parent_root else tk.Tk()
        self.window.title("NOVA Control Center — Settings & Plugin Hub")
        self.window.geometry("780x760")
        self.window.minsize(680, 640)
        self.window.config(bg="#0B0F19")

        # Bring to front initially
        self.window.attributes("-topmost", True)
        self.window.after(400, lambda: self.window.attributes("-topmost", False))

        self._build_ui()

    def _build_ui(self):
        # 1. Top Brand Header
        header = tk.Frame(self.window, bg="#111827", padx=24, pady=16)
        header.pack(fill="x", side="top")

        brand_row = tk.Frame(header, bg="#111827")
        brand_row.pack(fill="x")

        logo_title = tk.Label(
            brand_row,
            text="⚡ NOVA Control Center",
            font=("Segoe UI", 16, "bold"),
            fg="#F9FAFB",
            bg="#111827"
        )
        logo_title.pack(side="left")

        user_badge = tk.Label(
            brand_row,
            text=f"👤 {profile_manager.get('user_name', 'User')}",
            font=("Segoe UI", 10, "bold"),
            fg="#06B6D4",
            bg="#1E293B",
            padx=10,
            pady=3
        )
        user_badge.pack(side="right")

        # 2. Modern Tabbed Notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#0B0F19", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1E293B", foreground="#94A3B8", font=("Segoe UI", 10, "bold"), padding=[16, 8])
        style.map("TNotebook.Tab", background=[("selected", "#06B6D4")], foreground=[("selected", "#0B0F19")])

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=20, pady=16)

        # Tab 1: Profile & Assistant Settings
        self.tab_profile = tk.Frame(notebook, bg="#0B0F19", padx=16, pady=16)
        notebook.add(self.tab_profile, text=" 👤 User & Settings ")
        self._build_profile_tab(self.tab_profile)

        # Tab 2: Installed Plugins
        self.tab_plugins = tk.Frame(notebook, bg="#0B0F19", padx=16, pady=16)
        notebook.add(self.tab_plugins, text=" 🧩 Installed Plugins ")
        self._build_plugins_tab(self.tab_plugins)

        # Tab 3: Plugin Creator & Store
        self.tab_creator = tk.Frame(notebook, bg="#0B0F19", padx=16, pady=16)
        notebook.add(self.tab_creator, text=" 🛠️ Create / Install Plugin ")
        self._build_creator_tab(self.tab_creator)

        # Tab 4: System Requirements & Diagnostics
        self.tab_diagnostics = tk.Frame(notebook, bg="#0B0F19", padx=16, pady=16)
        notebook.add(self.tab_diagnostics, text=" 🖥️ System & Requirements ")
        self._build_diagnostics_tab(self.tab_diagnostics)

        # 3. Footer Bar
        footer = tk.Frame(self.window, bg="#111827", padx=24, pady=12)
        footer.pack(fill="x", side="bottom")

        self.status_lbl = tk.Label(
            footer,
            text="🟢 Engine: Online • Changes apply instantly without restart",
            font=("Segoe UI", 9),
            fg="#10B981",
            bg="#111827"
        )
        self.status_lbl.pack(side="left")

        close_btn = tk.Button(
            footer,
            text="Close Panel",
            command=self.window.destroy,
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#F9FAFB",
            activebackground="#334155",
            relief="flat",
            padx=16,
            pady=4,
            cursor="hand2"
        )
        close_btn.pack(side="right")

    # ==========================================
    # TAB 1: User Profile & Preferences
    # ==========================================
    def _build_profile_tab(self, parent):
        container = tk.Frame(parent, bg="#111827", padx=20, pady=20, bd=1, relief="solid", highlightbackground="#1F2937")
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Personalization & Assistant Preferences", font=("Segoe UI", 12, "bold"), fg="#F9FAFB", bg="#111827").pack(anchor="w", pady=(0, 16))

        # User Name
        row1 = tk.Frame(container, bg="#111827")
        row1.pack(fill="x", pady=6)
        tk.Label(row1, text="Your Name / Call Sign:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.entry_user_name = tk.Entry(row1, font=("Segoe UI", 10), bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.entry_user_name.insert(0, profile_manager.get("user_name", "User"))
        self.entry_user_name.pack(side="left", fill="x", expand=True, ipady=4, padx=(8, 0))

        # Assistant Name
        row2 = tk.Frame(container, bg="#111827")
        row2.pack(fill="x", pady=6)
        tk.Label(row2, text="Assistant Name:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.entry_ast_name = tk.Entry(row2, font=("Segoe UI", 10), bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.entry_ast_name.insert(0, profile_manager.get("assistant_name", "Nova"))
        self.entry_ast_name.pack(side="left", fill="x", expand=True, ipady=4, padx=(8, 0))

        # Wake Word Selection
        row3 = tk.Frame(container, bg="#111827")
        row3.pack(fill="x", pady=6)
        tk.Label(row3, text="Wake Word Trigger:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.var_wakeword = tk.StringVar(value=profile_manager.get("wake_word", "alexa"))
        ww_combo = ttk.Combobox(row3, textvariable=self.var_wakeword, values=["alexa", "hey_jarvis", "timer", "weather"], state="readonly", font=("Segoe UI", 9))
        ww_combo.pack(side="left", fill="x", expand=True, ipady=3, padx=(8, 0))

        # Wake Word Sensitivity Slider
        row4 = tk.Frame(container, bg="#111827")
        row4.pack(fill="x", pady=10)
        tk.Label(row4, text="Wake Sensitivity (0-1):", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.scale_sens = tk.Scale(row4, from_=0.20, to=0.85, resolution=0.05, orient="horizontal", bg="#111827", fg="#06B6D4", highlightthickness=0, troughcolor="#1E293B")
        self.scale_sens.set(profile_manager.get("wake_threshold", 0.50))
        self.scale_sens.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Whisper Hardware Model
        row5 = tk.Frame(container, bg="#111827")
        row5.pack(fill="x", pady=6)
        tk.Label(row5, text="Whisper Model Size:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.var_model = tk.StringVar(value=profile_manager.get("whisper_model", "base.en"))
        model_combo = ttk.Combobox(row5, textvariable=self.var_model, values=["tiny.en", "base.en", "small"], state="readonly", font=("Segoe UI", 9))
        model_combo.pack(side="left", fill="x", expand=True, ipady=3, padx=(8, 0))

        # Save Button
        save_btn = tk.Button(
            container,
            text="💾 Save Preferences",
            command=self._save_profile,
            font=("Segoe UI", 10, "bold"),
            bg="#06B6D4",
            fg="#08090D",
            activebackground="#0891B2",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        save_btn.pack(anchor="e", pady=(24, 0))

    def _save_profile(self):
        new_data = {
            "user_name": self.entry_user_name.get().strip() or "User",
            "assistant_name": self.entry_ast_name.get().strip() or "Nova",
            "wake_word": self.var_wakeword.get(),
            "wake_threshold": float(self.scale_sens.get()),
            "whisper_model": self.var_model.get()
        }
        profile_manager.update_multiple(new_data)
        messagebox.showinfo("NOVA Settings", "Preferences saved successfully!")

    # ==========================================
    # TAB 2: Installed Plugins
    # ==========================================
    def _build_plugins_tab(self, parent):
        # Search / Filter Bar
        search_frame = tk.Frame(parent, bg="#0B0F19")
        search_frame.pack(fill="x", pady=(0, 10))

        tk.Label(search_frame, text="🔍", font=("Segoe UI", 10), fg="#94A3B8", bg="#0B0F19").pack(side="left", padx=(0, 6))
        self.search_entry = tk.Entry(search_frame, font=("Segoe UI", 10), bg="#111827", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_plugins())

        # Scrollable Cards Container
        canvas = tk.Canvas(parent, bg="#0B0F19", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.plugin_cards_frame = tk.Frame(canvas, bg="#0B0F19")

        self.plugin_cards_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.plugin_cards_frame, anchor="nw", width=700)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._render_plugin_cards()

    def _render_plugin_cards(self, query=""):
        for widget in self.plugin_cards_frame.winfo_children():
            widget.destroy()

        plugins = plugin_manager.get_all_plugins()
        filtered = [p for p in plugins if query.lower() in p.name.lower() or query.lower() in p.description.lower()]

        for p in filtered:
            self._create_plugin_card(self.plugin_cards_frame, p)

    def _filter_plugins(self):
        q = self.search_entry.get().strip()
        self._render_plugin_cards(q)

    def _create_plugin_card(self, parent, plugin):
        card = tk.Frame(parent, bg="#111827", bd=1, relief="solid", highlightbackground="#1F2937", padx=16, pady=12)
        card.pack(fill="x", pady=6)

        top_row = tk.Frame(card, bg="#111827")
        top_row.pack(fill="x")

        # Icon
        tk.Label(top_row, text=plugin.icon, font=("Segoe UI Emoji", 20), bg="#111827").pack(side="left", padx=(0, 12))

        # Title & Description
        info = tk.Frame(top_row, bg="#111827")
        info.pack(side="left", fill="x", expand=True)

        header_box = tk.Frame(info, bg="#111827")
        header_box.pack(anchor="w")

        tk.Label(header_box, text=plugin.name, font=("Segoe UI", 11, "bold"), fg="#F9FAFB", bg="#111827").pack(side="left")
        tk.Label(header_box, text=f"v{plugin.version}", font=("Segoe UI", 8), fg="#64748B", bg="#111827", padx=4).pack(side="left")
        
        # Badge for Core vs Custom
        is_builtin = getattr(plugin, "is_builtin", False)
        badge_text = "Core" if is_builtin else "Custom"
        badge_color = "#38BDF8" if is_builtin else "#F59E0B"
        badge_bg = "#0C4A6E" if is_builtin else "#78350F"
        tk.Label(header_box, text=badge_text, font=("Segoe UI", 7, "bold"), fg=badge_color, bg=badge_bg, padx=6, pady=1).pack(side="left", padx=4)

        tk.Label(info, text=plugin.description, font=("Segoe UI", 8), fg="#94A3B8", bg="#111827", wraplength=380, justify="left").pack(anchor="w", pady=(2, 0))

        # Actions & Toggle
        action_box = tk.Frame(top_row, bg="#111827")
        action_box.pack(side="right")

        if not is_builtin:
            del_btn = tk.Button(
                action_box,
                text="🗑️",
                command=lambda p=plugin: self._on_uninstall(p),
                font=("Segoe UI Emoji", 9),
                bg="#1E293B",
                fg="#EF4444",
                activebackground="#7F1D1D",
                relief="flat",
                padx=6,
                pady=2,
                cursor="hand2"
            )
            del_btn.pack(side="right", padx=(6, 0))

        var = tk.BooleanVar(value=plugin.is_enabled)
        toggle = tk.Checkbutton(
            action_box,
            text="Active",
            variable=var,
            font=("Segoe UI", 9, "bold"),
            fg="#10B981" if plugin.is_enabled else "#64748B",
            bg="#111827",
            selectcolor="#1E293B",
            command=lambda p=plugin, v=var: self._on_toggle(p, v)
        )
        toggle.pack(side="right", padx=(4, 0))

        # Commands cheatsheet
        cmd_box = tk.Frame(card, bg="#0F172A", padx=12, pady=6)
        cmd_box.pack(fill="x", pady=(8, 0))

        samples = []
        for phrases in plugin.fast_intents.values():
            if phrases:
                samples.append(f'• "{phrases[0]}"')
        cmd_str = "   ".join(samples[:3])
        if len(samples) > 3:
            cmd_str += f"  (+{len(samples)-3} more)"

        tk.Label(cmd_box, text=f"Voice Triggers: {cmd_str}", font=("Segoe UI", 8), fg="#38BDF8", bg="#0F172A").pack(anchor="w")

    def _on_toggle(self, plugin, var):
        plugin_manager.set_plugin_enabled(plugin.id, var.get())

    def _on_uninstall(self, plugin):
        confirm = messagebox.askyesno("Uninstall Plugin", f"Are you sure you want to uninstall and delete the custom plugin '{plugin.name}'?")
        if confirm:
            success = plugin_manager.uninstall_plugin(plugin.id)
            if success:
                self._render_plugin_cards()
                messagebox.showinfo("Uninstalled", f"Plugin '{plugin.name}' was removed from your User Plugins folder.")
            else:
                messagebox.showerror("Error", f"Could not uninstall '{plugin.name}'. Built-in plugins cannot be deleted.")

    # ==========================================
    # TAB 3: Plugin Creator Wizard & File Installer
    # ==========================================
    def _build_creator_tab(self, parent):
        canvas = tk.Canvas(parent, bg="#0B0F19", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#0B0F19")

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=700)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Section 1: Template Creator Wizard
        box1 = tk.Frame(scrollable, bg="#111827", padx=20, pady=18, bd=1, relief="solid", highlightbackground="#1F2937")
        box1.pack(fill="x", pady=(0, 16))

        tk.Label(box1, text="✨ Plugin Creation Wizard (Generate Code)", font=("Segoe UI", 12, "bold"), fg="#F9FAFB", bg="#111827").pack(anchor="w", pady=(0, 12))

        # Inputs
        f_id = tk.Frame(box1, bg="#111827")
        f_id.pack(fill="x", pady=4)
        tk.Label(f_id, text="Plugin ID (e.g. spotify):", font=("Segoe UI", 9), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.in_id = tk.Entry(f_id, bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.in_id.pack(side="left", fill="x", expand=True, ipady=3)

        f_name = tk.Frame(box1, bg="#111827")
        f_name.pack(fill="x", pady=4)
        tk.Label(f_name, text="Display Name (e.g. Spotify):", font=("Segoe UI", 9), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.in_name = tk.Entry(f_name, bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.in_name.pack(side="left", fill="x", expand=True, ipady=3)

        f_icon = tk.Frame(box1, bg="#111827")
        f_icon.pack(fill="x", pady=4)
        tk.Label(f_icon, text="Emoji Icon (e.g. 🎵):", font=("Segoe UI", 9), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.in_icon = tk.Entry(f_icon, bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.in_icon.insert(0, "🔌")
        self.in_icon.pack(side="left", fill="x", expand=True, ipady=3)

        f_desc = tk.Frame(box1, bg="#111827")
        f_desc.pack(fill="x", pady=4)
        tk.Label(f_desc, text="Description:", font=("Segoe UI", 9), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.in_desc = tk.Entry(f_desc, bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.in_desc.pack(side="left", fill="x", expand=True, ipady=3)

        f_cmd = tk.Frame(box1, bg="#111827")
        f_cmd.pack(fill="x", pady=4)
        tk.Label(f_cmd, text="Sample Voice Command:", font=("Segoe UI", 9), fg="#94A3B8", bg="#111827", width=22, anchor="w").pack(side="left")
        self.in_cmd = tk.Entry(f_cmd, bg="#1E293B", fg="#F9FAFB", insertbackground="#F9FAFB", relief="flat")
        self.in_cmd.pack(side="left", fill="x", expand=True, ipady=3)

        gen_btn = tk.Button(
            box1,
            text="🚀 Generate & Load Plugin",
            command=self._generate_plugin,
            font=("Segoe UI", 9, "bold"),
            bg="#10B981",
            fg="#08090D",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2"
        )
        gen_btn.pack(anchor="e", pady=(12, 0))

        # Section 2: Install from External File
        box2 = tk.Frame(scrollable, bg="#111827", padx=20, pady=18, bd=1, relief="solid", highlightbackground="#1F2937")
        box2.pack(fill="x")

        tk.Label(box2, text="📦 Install Plugin from File (.py or .zip)", font=("Segoe UI", 12, "bold"), fg="#F9FAFB", bg="#111827").pack(anchor="w", pady=(0, 6))
        tk.Label(box2, text="Import a community plugin or standalone script directly into NOVA.", font=("Segoe UI", 8), fg="#94A3B8", bg="#111827").pack(anchor="w", pady=(0, 12))

        inst_btn = tk.Button(
            box2,
            text="📁 Browse & Install Plugin File...",
            command=self._browse_install_plugin,
            font=("Segoe UI", 9, "bold"),
            bg="#38BDF8",
            fg="#08090D",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2"
        )
        inst_btn.pack(anchor="w")

    def _generate_plugin(self):
        pid = self.in_id.get().strip()
        pname = self.in_name.get().strip()
        picon = self.in_icon.get().strip() or "🔌"
        pdesc = self.in_desc.get().strip() or f"Control {pname} application"
        pcmd = self.in_cmd.get().strip() or f"open {pname}"

        if not pid or not pname:
            messagebox.showerror("Error", "Please provide at least a Plugin ID and Name.")
            return

        file_created = plugin_manager.create_plugin_template(pid, pname, picon, pdesc, pcmd)
        self._render_plugin_cards()
        messagebox.showinfo("Success", f"Plugin '{pname}' created and activated!\nFile: {os.path.basename(file_created)}")

    def _browse_install_plugin(self):
        file_path = filedialog.askopenfilename(
            title="Select Plugin File",
            filetypes=[("NOVA Plugin Files", "*.py *.zip"), ("All Files", "*.*")]
        )
        if file_path:
            success = plugin_manager.install_plugin_from_file(file_path)
            if success:
                self._render_plugin_cards()
                messagebox.showinfo("Success", f"Plugin installed successfully from:\n{os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "Failed to install plugin from selected file.")

    # ==========================================
    # TAB 4: System Requirements & Diagnostics
    # ==========================================
    def _build_diagnostics_tab(self, parent):
        canvas = tk.Canvas(parent, bg="#0B0F19", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#0B0F19")

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=700)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Header
        tk.Label(scrollable, text="System Requirements & Health Check", font=("Segoe UI", 13, "bold"), fg="#F9FAFB", bg="#0B0F19").pack(anchor="w", pady=(0, 4))
        tk.Label(scrollable, text="Live detection of required tools, drivers, and hardware on this PC.", font=("Segoe UI", 9), fg="#94A3B8", bg="#0B0F19").pack(anchor="w", pady=(0, 16))

        # Run all checks
        checks = self._run_all_checks()

        for section_title, items in checks:
            # Section Header
            sec_frame = tk.Frame(scrollable, bg="#111827", padx=16, pady=12, bd=1, relief="solid", highlightbackground="#1F2937")
            sec_frame.pack(fill="x", pady=6)

            tk.Label(sec_frame, text=section_title, font=("Segoe UI", 11, "bold"), fg="#F9FAFB", bg="#111827").pack(anchor="w", pady=(0, 8))

            for name, status, detail, link in items:
                row = tk.Frame(sec_frame, bg="#111827")
                row.pack(fill="x", pady=3)

                if status == "ok":
                    indicator = "✅"
                    color = "#10B981"
                elif status == "warn":
                    indicator = "⚠️"
                    color = "#F59E0B"
                else:
                    indicator = "❌"
                    color = "#EF4444"

                tk.Label(row, text=indicator, font=("Segoe UI Emoji", 10), bg="#111827").pack(side="left", padx=(0, 8))
                tk.Label(row, text=name, font=("Segoe UI", 9, "bold"), fg="#F9FAFB", bg="#111827", width=28, anchor="w").pack(side="left")
                tk.Label(row, text=detail, font=("Segoe UI", 8), fg=color, bg="#111827", wraplength=350, justify="left").pack(side="left", padx=(8, 0))

                if link and status != "ok":
                    link_btn = tk.Button(
                        row,
                        text="Download",
                        command=lambda url=link: os.startfile(url) if url.startswith("http") else None,
                        font=("Segoe UI", 8, "bold"),
                        bg="#1E293B",
                        fg="#38BDF8",
                        activebackground="#334155",
                        relief="flat",
                        padx=8,
                        cursor="hand2"
                    )
                    link_btn.pack(side="right", padx=(8, 0))

        # Refresh Button
        refresh_btn = tk.Button(
            scrollable,
            text="🔄 Re-Scan System",
            command=lambda: self._refresh_diagnostics(parent),
            font=("Segoe UI", 9, "bold"),
            bg="#06B6D4",
            fg="#08090D",
            activebackground="#0891B2",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2"
        )
        refresh_btn.pack(anchor="e", pady=(16, 0))

    def _refresh_diagnostics(self, parent):
        """Destroys and re-renders the diagnostics tab."""
        for widget in parent.winfo_children():
            widget.destroy()
        self._build_diagnostics_tab(parent)

    def _run_all_checks(self):
        """Runs all system requirement checks and returns structured results."""
        results = []

        # ── Section 1: Core AI & Speech ──
        ai_checks = []

        # Ollama
        ollama_path = shutil.which("ollama")
        if ollama_path:
            # Check if ollama is serving
            try:
                r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
                models = [l.split()[0] for l in r.stdout.strip().split("\n")[1:] if l.strip()]
                if models:
                    ai_checks.append(("Ollama Server", "ok", f"Installed at {ollama_path} | Models: {', '.join(models[:3])}", None))
                else:
                    ai_checks.append(("Ollama Server", "warn", f"Installed but no models found. Run: ollama pull qwen2.5:0.5b", None))
            except Exception:
                ai_checks.append(("Ollama Server", "warn", f"Installed at {ollama_path} but not responding.", None))
        else:
            ai_checks.append(("Ollama Server", "fail", "Not found. Required for AI voice reasoning.", "https://ollama.com/download"))

        # Ollama Model
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            has_qwen = any("qwen" in line.lower() for line in r.stdout.split("\n"))
            if has_qwen:
                ai_checks.append(("AI Model (Qwen 2.5)", "ok", "Qwen model detected and ready.", None))
            else:
                ai_checks.append(("AI Model (Qwen 2.5)", "warn", "No Qwen model. Run: ollama pull qwen2.5:0.5b", None))
        except Exception:
            ai_checks.append(("AI Model (Qwen 2.5)", "fail", "Cannot check models — Ollama not running.", None))

        # faster-whisper
        try:
            import faster_whisper
            ai_checks.append(("faster-whisper (ASR)", "ok", "Speech recognition engine loaded.", None))
        except ImportError:
            ai_checks.append(("faster-whisper (ASR)", "fail", "Not installed. Required for voice transcription.", None))

        # openwakeword
        try:
            import openwakeword
            ai_checks.append(("openWakeWord", "ok", "Wake word detection engine loaded.", None))
        except ImportError:
            ai_checks.append(("openWakeWord", "fail", "Not installed. Required for wake word.", None))

        results.append(("🧠 Core AI & Speech Engines", ai_checks))

        # ── Section 2: NVIDIA GPU & CUDA ──
        gpu_checks = []

        # NVIDIA GPU detection
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split(", ")
                gpu_name = parts[0] if len(parts) > 0 else "Unknown"
                gpu_mem = parts[1] if len(parts) > 1 else "?"
                driver = parts[2] if len(parts) > 2 else "?"
                gpu_checks.append(("NVIDIA GPU", "ok", f"{gpu_name} | {gpu_mem} | Driver {driver}", None))
            else:
                gpu_checks.append(("NVIDIA GPU", "warn", "nvidia-smi returned no data. Whisper will use CPU.", None))
        except FileNotFoundError:
            gpu_checks.append(("NVIDIA GPU", "warn", "No NVIDIA GPU detected. Whisper will use CPU (slower).", "https://www.nvidia.com/download/index.aspx"))
        except Exception:
            gpu_checks.append(("NVIDIA GPU", "warn", "Could not query GPU status.", None))

        # CUDA Toolkit (cuBLAS)
        try:
            import ctranslate2
            gpu_checks.append(("CUDA / CTranslate2", "ok", "GPU acceleration runtime available.", None))
        except Exception:
            gpu_checks.append(("CUDA / CTranslate2", "warn", "CTranslate2 not loaded. GPU acceleration unavailable.", None))

        # cuBLAS DLL check
        cublas_found = False
        for search_dir in [os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv", "Lib", "site-packages", "nvidia", "cublas", "bin")]:
            if os.path.isdir(search_dir):
                dlls = [f for f in os.listdir(search_dir) if f.endswith(".dll")]
                if dlls:
                    cublas_found = True
                    gpu_checks.append(("cuBLAS DLL", "ok", f"Found {len(dlls)} DLLs in nvidia/cublas/bin", None))
        if not cublas_found:
            gpu_checks.append(("cuBLAS DLL", "warn", "Not found. GPU Whisper may fail. pip install nvidia-cublas-cu12", None))

        results.append(("🎮 NVIDIA GPU & CUDA Acceleration", gpu_checks))

        # ── Section 3: Audio & Hardware ──
        hw_checks = []

        # Microphone detection
        try:
            devices = sd.query_devices()
            input_devs = [d for d in devices if d['max_input_channels'] > 0]
            if input_devs:
                default_in = sd.query_devices(kind='input')
                hw_checks.append(("Microphone", "ok", f"{len(input_devs)} input device(s). Default: {default_in['name'][:40]}", None))
            else:
                hw_checks.append(("Microphone", "fail", "No audio input devices detected!", None))
        except Exception as e:
            hw_checks.append(("Microphone", "fail", f"Audio query failed: {e}", None))

        # OS Info
        hw_checks.append(("Operating System", "ok", f"{platform.system()} {platform.release()} ({platform.architecture()[0]})", None))

        # Python version
        hw_checks.append(("Python Runtime", "ok", f"Python {platform.python_version()}", None))

        results.append(("🎧 Audio & System Hardware", hw_checks))

        return results
