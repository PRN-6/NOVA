import logging
from typing import Callable, Dict, List
from plugins.base_plugin import BasePlugin
from plugins.win_keys import (
    trigger_volume_up,
    trigger_volume_down,
    trigger_volume_mute,
    trigger_lock_workstation,
    trigger_snipping_tool,
    trigger_press_enter,
    trigger_press_tab,
    trigger_close_window
)

logger = logging.getLogger("NOVA.Plugin.System")

class SystemPlugin(BasePlugin):
    id = "system"
    name = "Windows System"
    icon = "⚙️"
    description = "Control Windows OS: volume, screen lock, screenshot, press enter, and close active window."
    version = "1.2.0"
    author = "NOVA Team"

    @property
    def actions(self) -> Dict[str, Callable[[str], bool]]:
        return {
            "system.close_window": self.close_window,
            "system.press_enter": self.press_enter,
            "system.press_tab": self.press_tab,
            "system.volume_up": self.volume_up,
            "system.volume_down": self.volume_down,
            "system.volume_mute": self.volume_mute,
            "system.lock": self.lock_screen,
            "system.screenshot": self.take_screenshot,
        }

    @property
    def fast_intents(self) -> Dict[str, List[str]]:
        return {
            "system.close_window": [
                "close window",
                "close this window",
                "close current window",
                "close active window",
                "close app",
                "close this app",
                "exit app",
                "quit app",
                "exit window",
            ],
            "system.press_enter": [
                "press enter",
                "hit enter",
                "enter",
                "press return",
                "hit return",
                "submit",
            ],
            "system.press_tab": [
                "press tab",
                "hit tab",
                "next item",
            ],
            "system.volume_up": [
                "volume up",
                "increase volume",
                "turn up the volume",
                "louder",
            ],
            "system.volume_down": [
                "volume down",
                "decrease volume",
                "turn down the volume",
                "lower volume",
            ],
            "system.volume_mute": [
                "mute volume",
                "unmute volume",
                "mute audio",
                "unmute audio",
                "mute",
                "unmute",
            ],
            "system.lock": [
                "lock screen",
                "lock pc",
                "lock my computer",
                "lock windows",
            ],
            "system.screenshot": [
                "take a screenshot",
                "take screenshot",
                "capture screen",
                "screenshot",
                "snip screen",
            ]
        }

    @property
    def descriptions(self) -> Dict[str, str]:
        return {
            "system.close_window": "- system.close_window: Close the currently active window or application (Alt+F4).",
            "system.press_enter": "- system.press_enter: Simulate pressing the Enter / Return key on the keyboard.",
            "system.press_tab": "- system.press_tab: Simulate pressing the Tab key on the keyboard.",
            "system.volume_up": "- system.volume_up: Increase master audio volume.",
            "system.volume_down": "- system.volume_down: Decrease master audio volume.",
            "system.volume_mute": "- system.volume_mute: Toggle mute/unmute master audio.",
            "system.lock": "- system.lock: Lock the Windows workstation/computer screen.",
            "system.screenshot": "- system.screenshot: Launch Windows screenshot snip tool.",
        }

    def close_window(self, text: str) -> bool:
        logger.info("Plugin Action: Closing active window (Alt+F4)")
        trigger_close_window()
        return True

    def press_enter(self, text: str) -> bool:
        logger.info("Plugin Action: Pressing Enter key")
        trigger_press_enter()
        return True

    def press_tab(self, text: str) -> bool:
        logger.info("Plugin Action: Pressing Tab key")
        trigger_press_tab(1)
        return True

    def volume_up(self, text: str) -> bool:
        logger.info("Plugin Action: Volume Up")
        trigger_volume_up()
        return True

    def volume_down(self, text: str) -> bool:
        logger.info("Plugin Action: Volume Down")
        trigger_volume_down()
        return True

    def volume_mute(self, text: str) -> bool:
        logger.info("Plugin Action: Toggle Volume Mute")
        trigger_volume_mute()
        return True

    def lock_screen(self, text: str) -> bool:
        logger.info("Plugin Action: Locking Computer Screen")
        trigger_lock_workstation()
        return True

    def take_screenshot(self, text: str) -> bool:
        logger.info("Plugin Action: Taking Screenshot")
        trigger_snipping_tool()
        return True

