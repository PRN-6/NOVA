import logging
import subprocess
from typing import Callable, Dict, List
from plugins.base_plugin import BasePlugin
from plugins.win_keys import trigger_new_chat, kill_process

logger = logging.getLogger("NOVA.Plugin.WhatsApp")

class WhatsAppPlugin(BasePlugin):
    """
    Standalone WhatsApp Desktop Plugin for NOVA Assistant.
    Provides launching, tree-process termination, and new conversation shortcuts.
    """
    id = "whatsapp"
    name = "WhatsApp Desktop"
    icon = "💬"
    description = "Control WhatsApp Desktop: launch app, close app, open new chat."
    version = "1.2.0"
    author = "Community Plugin"
    is_builtin = False

    @property
    def actions(self) -> Dict[str, Callable[[str], bool]]:
        return {
            "whatsapp.open": self.open_app,
            "whatsapp.close": self.close_app,
            "whatsapp.new_chat": self.new_chat,
        }

    @property
    def fast_intents(self) -> Dict[str, List[str]]:
        return {
            "whatsapp.open": [
                "open whatsapp",
                "launch whatsapp",
                "start whatsapp",
                "open whats app",
                "launch whats app",
                "open what's app",
                "launch what's app",
                "whatsapp",
                "open wa",
                "launch wa",
            ],
            "whatsapp.close": [
                "close whatsapp",
                "exit whatsapp",
                "quit whatsapp",
                "terminate whatsapp",
                "close whats app",
                "exit whats app",
                "close wa",
            ],
            "whatsapp.new_chat": [
                "new chat in whatsapp",
                "start new chat",
                "new conversation in whatsapp",
                "whatsapp new chat",
            ]
        }

    @property
    def descriptions(self) -> Dict[str, str]:
        return {
            "whatsapp.open": "- whatsapp.open: Open or bring up WhatsApp desktop application.",
            "whatsapp.close": "- whatsapp.close: Force close or exit WhatsApp application.",
            "whatsapp.new_chat": "- whatsapp.new_chat: Start a new conversation or chat in WhatsApp.",
        }

    def open_app(self, text: str) -> bool:
        logger.info("Plugin Action: Launching WhatsApp")
        subprocess.Popen("start whatsapp:", shell=True)
        return True

    def close_app(self, text: str) -> bool:
        logger.info("Plugin Action: Force Closing WhatsApp (process tree)")
        kill_process("WhatsApp*")
        kill_process("WhatsApp.exe")
        return True

    def new_chat(self, text: str) -> bool:
        logger.info("Plugin Action: Triggering new chat in WhatsApp")
        trigger_new_chat()
        return True
