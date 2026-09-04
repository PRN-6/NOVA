import logging
import os
import sys
from ui.hud import FloatingHUD
from ui.tray import SystemTray

logger = logging.getLogger("NOVA.UIManager")

class UIManager:
    """
    Central coordinator managing the Floating HUD and Windows System Tray.
    Thread-safe event bridge between audio pipeline, LLM actions, and UI visuals.
    """
    def __init__(self):
        self.hud = FloatingHUD()
        self.tray = SystemTray(ui_manager=self)
        self.is_muted = False

    def start_tray(self):
        """Starts the tray in a background thread."""
        try:
            self.tray.start()
        except Exception as e:
            logger.warning(f"Could not start system tray: {e}")

    def run_hud_loop(self):
        """Runs the main HUD Tkinter loop on the main thread."""
        self.hud.start_ui()

    def on_wake_word_detected(self):
        """Triggered when the wake word is spotted."""
        if not self.is_muted:
            self.hud.set_state("listening", text="Listening for command...")
            self.tray.set_status_color("#06B6D4")

    def on_audio_energy(self, level: float):
        """Updates live audio energy for waveform visualization."""
        if not self.is_muted:
            self.hud.update_audio_energy(level)

    def on_transcription(self, text: str):
        """Triggered when speech settles and transcription starts."""
        self.hud.set_state("processing", text=f'"{text}"')
        self.tray.set_status_color("#8B5CF6")

    def on_action_completed(self, tool_name: str, success: bool = True):
        """Triggered when a skill finishes executing."""
        if success:
            display_title = f"⚡ {tool_name.replace('_', ' ').upper()}"
            self.hud.set_state("success", title=display_title, text="Executed successfully")
            self.tray.set_status_color("#10B981")
        else:
            self.hud.set_state("error", text="Command not recognized")
            self.tray.set_status_color("#EF4444")

    def on_sleep(self):
        """Triggered when speech times out or returns to idle."""
        self.hud.set_state("idle", text="Say 'Nova' to begin")
        self.tray.set_status_color("#06B6D4")

    def toggle_hud(self):
        """Toggles HUD visibility on/off."""
        self.hud.toggle_visibility()

    def open_plugin_manager(self):
        """Opens the visual Plugin Manager window."""
        self.hud.open_plugin_manager()

    def toggle_mute(self):
        """Toggles assistant listening state."""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.hud.set_state("idle", text="Assistant is muted")
            self.tray.set_status_color("#EF4444")
            logger.info("NOVA Muted.")
        else:
            self.hud.set_state("idle", text="Say 'Nova' to begin")
            self.tray.set_status_color("#06B6D4")
            logger.info("NOVA Unmuted.")

    def shutdown(self):
        """Gracefully shuts down HUD and application."""
        logger.info("Shutting down UI Manager...")
        self.hud.close()
        # Trigger process termination
        os._exit(0)
