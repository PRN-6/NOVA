import tkinter as tk
import queue
import threading
import time

class FloatingHUD:
    """
    A modern, frameless, semi-transparent floating HUD overlay for NOVA.
    Runs on a dedicated Tkinter loop and provides real-time visual feedback for
    Wake Word, Audio Energy, Speech Transcription, and Action Execution.
    """
    def __init__(self, on_close_callback=None):
        self.on_close_callback = on_close_callback
        self.queue = queue.Queue()
        self.root = None
        self.canvas = None
        self.current_state = "idle"
        self.visible = True
        
        # Dimensions & appearance
        self.width = 380
        self.height = 70
        self.corner_radius = 24
        
        # Color palette
        self.bg_color = "#0B0F19"
        self.pill_bg = "#111827"
        self.text_primary = "#F9FAFB"
        self.text_secondary = "#9CA3AF"
        self.border_idle = "#1F2937"
        self.border_listening = "#06B6D4"
        self.border_processing = "#8B5CF6"
        self.border_success = "#10B981"
        self.border_error = "#EF4444"
        
        # Animation & pulse variables
        self.pulse_phase = 0.0
        self.audio_level = 0.0
        self.current_border_color = self.border_idle
        self.status_title = "NOVA ASSISTANT"
        self.status_subtitle = "Say'Nova' to begin"
        self.status_icon = "🎙️"
        
        # Dragging state
        self._drag_start_x = 0
        self._drag_start_y = 0

    def start_ui(self):
        """Initializes the Tkinter window and starts its main loop."""
        self.root = tk.Tk()
        self.root.title("NOVA HUD")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.94)
        
        # Configure transparency on Windows
        self.root.config(bg=self.bg_color)
        self.root.wm_attributes("-transparentcolor", self.bg_color)
        
        # Initial position: Top-Center of Screen
        screen_width = self.root.winfo_screenwidth()
        pos_x = (screen_width - self.width) // 2
        pos_y = 30
        self.root.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")
        
        # Canvas for rich rounded styling
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Mouse dragging bindings
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        
        # Redraw loop and queue polling
        self._draw_hud()
        self._poll_events()
        self._animate_pulse()
        
        self.root.mainloop()

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        x = self.root.winfo_x() - self._drag_start_x + event.x
        y = self.root.winfo_y() - self._drag_start_y + event.y
        self.root.geometry(f"+{x}+{y}")

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draws a smooth rounded pill rectangle on the canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _draw_hud(self):
        """Redraws the entire HUD widget based on current state."""
        self.canvas.delete("all")
        
        # 1. Background Pill Container
        margin = 4
        self._draw_rounded_rect(
            margin, margin,
            self.width - margin, self.height - margin,
            radius=self.corner_radius,
            fill=self.pill_bg,
            outline=self.current_border_color,
            width=2
        )
        
        # 2. Status Icon Pill / Orb (Left)
        icon_cx = 38
        icon_cy = self.height // 2
        
        orb_color = self.current_border_color
        self.canvas.create_oval(
            icon_cx - 16, icon_cy - 16,
            icon_cx + 16, icon_cy + 16,
            fill="#1E293B",
            outline=orb_color,
            width=1.5
        )
        self.canvas.create_text(
            icon_cx, icon_cy,
            text=self.status_icon,
            font=("Segoe UI Emoji", 12)
        )
        
        # 3. Waveform / Audio energy bars when listening
        if self.current_state == "listening":
            bar_x = self.width - 45
            for i in range(4):
                amp = max(4, int(min(22, (self.audio_level * 180) * (0.8 + (i % 2) * 0.4))))
                self.canvas.create_line(
                    bar_x + (i * 6), icon_cy - amp // 2,
                    bar_x + (i * 6), icon_cy + amp // 2,
                    fill=self.border_listening,
                    width=2.5,
                    capstyle=tk.ROUND
                )
        
        # 4. Text Labels (Title & Subtitle)
        self.canvas.create_text(
            68, icon_cy - 10,
            anchor="w",
            text=self.status_title,
            fill=self.text_primary,
            font=("Segoe UI", 10, "bold")
        )
        
        # Truncate subtitle if too long
        sub = self.status_subtitle
        if len(sub) > 36:
            sub = sub[:33] + "..."
            
        self.canvas.create_text(
            68, icon_cy + 11,
            anchor="w",
            text=sub,
            fill=self.text_secondary,
            font=("Segoe UI", 8)
        )

    def _animate_pulse(self):
        """Micro-animation loop for glowing borders and wave movements."""
        if not self.root:
            return
            
        if self.current_state == "listening":
            self.pulse_phase += 0.15
            self._draw_hud()
        elif self.current_state == "processing":
            self.pulse_phase += 0.2
            self._draw_hud()
            
        self.root.after(40, self._animate_pulse)

    def _poll_events(self):
        """Polls thread-safe messages from background audio and executor threads."""
        try:
            while True:
                action, data = self.queue.get_nowait()
                if action == "state":
                    self._set_state_internal(data)
                elif action == "energy":
                    self.audio_level = data
                elif action == "text":
                    self.status_subtitle = data
                    self._draw_hud()
                elif action == "toggle_visibility":
                    self._toggle_visibility_internal()
                elif action == "open_plugins":
                    self._open_plugins_internal()
                elif action == "quit":
                    if self.root:
                        self.root.destroy()
                    return
        except queue.Empty:
            pass
            
        if self.root:
            self.root.after(30, self._poll_events)

    def _open_plugins_internal(self):
        from ui.plugin_window import PluginManagerWindow
        if not hasattr(self, "_plugin_win") or self._plugin_win is None:
            self._plugin_win = PluginManagerWindow(parent_root=self.root)
        self._plugin_win.open()

    def _set_state_internal(self, state_data):
        """Applies state changes within the GUI thread."""
        state = state_data.get("name", "idle")
        self.current_state = state
        
        if state == "idle":
            self.status_icon = "🎙️"
            self.status_title = "NOVA READY"
            self.status_subtitle = state_data.get("text", "Say'Nova'")
            self.current_border_color = self.border_idle
            self.audio_level = 0.0
            
        elif state == "listening":
            self.status_icon = "👂"
            self.status_title = "LISTENING..."
            self.status_subtitle = state_data.get("text", "Listening for your command")
            self.current_border_color = self.border_listening
            
        elif state == "processing":
            self.status_icon = "⚡"
            self.status_title = "PROCESSING"
            self.status_subtitle = state_data.get("text", "Analyzing intent...")
            self.current_border_color = self.border_processing
            
        elif state == "success":
            self.status_icon = "🚀"
            self.status_title = state_data.get("title", "ACTION EXECUTED")
            self.status_subtitle = state_data.get("text", "Success")
            self.current_border_color = self.border_success
            # Auto-reset to idle after 2.5 seconds
            if self.root:
                self.root.after(2500, lambda: self._set_state_internal({"name": "idle"}))
                
        elif state == "error":
            self.status_icon = "⚠️"
            self.status_title = "UNKNOWN COMMAND"
            self.status_subtitle = state_data.get("text", "Could not match intent")
            self.current_border_color = self.border_error
            if self.root:
                self.root.after(2500, lambda: self._set_state_internal({"name": "idle"}))
                
        self._draw_hud()

    def _toggle_visibility_internal(self):
        if not self.root:
            return
        if self.visible:
            self.root.withdraw()
            self.visible = False
        else:
            self.root.deiconify()
            self.visible = True

    # ---------------- Thread-Safe Public API ---------------- #

    def set_state(self, name: str, text: str = None, title: str = None):
        """Thread-safe state update."""
        payload = {"name": name}
        if text:
            payload["text"] = text
        if title:
            payload["title"] = title
        self.queue.put(("state", payload))

    def update_audio_energy(self, level: float):
        """Thread-safe audio energy update for waveform visualization."""
        self.queue.put(("energy", level))

    def set_subtitle_text(self, text: str):
        """Thread-safe subtitle/transcript update."""
        self.queue.put(("text", text))

    def toggle_visibility(self):
        """Thread-safe toggle HUD visibility."""
        self.queue.put(("toggle_visibility", None))

    def open_plugin_manager(self):
        """Thread-safe open Plugin Manager Window."""
        self.queue.put(("open_plugins", None))

    def close(self):
        """Thread-safe window shutdown."""
        self.queue.put(("quit", None))

