import threading
import logging
from PIL import Image, ImageDraw
import pystray

logger = logging.getLogger("PRIVACY68.SystemTray")

class SystemTray:
    """
    Windows System Tray integration for PRIVACY68 Assistant using pystray.
    Provides background controls, HUD toggle, and status indicators.
    """
    def __init__(self, ui_manager):
        self.ui_manager = ui_manager
        self.icon = None
        self.is_running = False

    def _create_icon_image(self, color="#EF4444"):
        """Generates a dynamic 64x64 icon with a glowing rounded circle."""
        width = 64
        height = 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Outer ring
        draw.ellipse((4, 4, 60, 60), fill="#111115", outline=color, width=4)
        # Inner core
        draw.ellipse((20, 20, 44, 44), fill=color)
        
        return image

    def start(self):
        """Starts the tray icon in a dedicated background thread."""
        image = self._create_icon_image("#EF4444")
        
        menu = pystray.Menu(
            pystray.MenuItem("⚡ PRIVACY68 Assistant (Online)", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📱 Open Mobile Web Remote", self._on_open_mobile_remote),
            pystray.MenuItem("⚙️ Control Center & Settings", self._on_open_plugins),
            pystray.MenuItem("👁️ Toggle HUD Overlay", self._on_toggle_hud),
            pystray.MenuItem("🔇 Mute / Pause", self._on_toggle_mute),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🚪 Exit PRIVACY68", self._on_exit)
        )
        
        self.icon = pystray.Icon(
            "PRIVACY68",
            image,
            "PRIVACY68 Voice Assistant",
            menu=menu
        )
        
        self.is_running = True
        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()
        logger.info("System Tray icon initialized.")

    def _on_open_mobile_remote(self):
        if self.ui_manager:
            self.ui_manager.open_mobile_remote()

    def _on_open_plugins(self):
        if self.ui_manager:
            self.ui_manager.open_plugin_manager()

    def _on_toggle_hud(self):
        if self.ui_manager:
            self.ui_manager.toggle_hud()

    def _on_toggle_mute(self):
        if self.ui_manager:
            self.ui_manager.toggle_mute()

    def _on_exit(self):
        logger.info("Exit requested via System Tray.")
        if self.icon:
            self.icon.stop()
        if self.ui_manager:
            self.ui_manager.shutdown()

    def set_status_color(self, color_hex: str):
        """Updates the tray icon color dynamically."""
        if self.icon and self.is_running:
            try:
                self.icon.icon = self._create_icon_image(color_hex)
            except Exception as e:
                logger.debug(f"Could not update tray icon: {e}")
