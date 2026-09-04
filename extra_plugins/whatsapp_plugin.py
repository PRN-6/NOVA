import logging
import subprocess
import time
import re
import json
import ctypes
from typing import Callable, Dict, List, Tuple, Optional
from plugins.base_plugin import BasePlugin
from plugins.win_keys import trigger_new_chat, trigger_press_enter, kill_process

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    ollama = None
    HAS_OLLAMA = False

user32 = ctypes.windll.user32
logger = logging.getLogger("NOVA.Plugin.WhatsApp")

# Virtual key codes
VK_CONTROL = 0x11
VK_V = 0x56
VK_DOWN = 0x28
KEYEVENTF_KEYUP = 0x0002

def _press_key(vk: int):
    """Sends keydown and keyup for a single virtual key."""
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def _press_paste():
    """Sends Ctrl+V to paste from clipboard."""
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

class WhatsAppPlugin(BasePlugin):
    """
    Standalone WhatsApp Desktop Plugin for NOVA Assistant.
    Provides launching, closing, and AI-powered voice messaging.
    """
    id = "whatsapp"
    name = "WhatsApp Desktop"
    icon = "💬"
    description = "Control WhatsApp Desktop: launch app, close app, and send messages."
    version = "1.4.0"
    author = "Community Plugin"
    is_builtin = False

    @property
    def actions(self) -> Dict[str, Callable[[str], bool]]:
        return {
            "whatsapp.open": self.open_app,
            "whatsapp.close": self.close_app,
            "whatsapp.new_chat": self.new_chat,
            "whatsapp.send_message": self.send_message,
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
                "open wa",
                "launch wa",
            ],
            "whatsapp.close": [
                "close whatsapp",
                "exit whatsapp",
                "quit whatsapp",
                "terminate whatsapp",
                "close whats app",
                "close wa",
            ],
            "whatsapp.new_chat": [
                "new chat in whatsapp",
                "start new chat in whatsapp",
                "whatsapp new chat",
            ],
            "whatsapp.send_message": [
                "send message to",
                "send a message to",
                "send whatsapp message to",
                "message someone on whatsapp",
                "text someone on whatsapp",
                "send hi to mom",
                "send message to mom",
                "send message to dad",
                "open chat with",
                "tell mom on whatsapp",
                "open whatsapp and send message",
            ]
        }

    @property
    def descriptions(self) -> Dict[str, str]:
        return {
            "whatsapp.open": "- whatsapp.open: Launch or open the WhatsApp Desktop application.",
            "whatsapp.close": "- whatsapp.close: Force close or exit WhatsApp application.",
            "whatsapp.new_chat": "- whatsapp.new_chat: Start a new conversation in WhatsApp.",
            "whatsapp.send_message": "- whatsapp.send_message: Send a message or open a chat with a specific person on WhatsApp (e.g. 'send message to mom', 'tell dad I will be late', 'send hi to mom').",
        }

    def open_app(self, text: str) -> bool:
        logger.info("Plugin Action: Launching WhatsApp")
        subprocess.Popen("start whatsapp:", shell=True)
        return True

    def close_app(self, text: str) -> bool:
        logger.info("Plugin Action: Force Closing WhatsApp")
        kill_process("WhatsApp*")
        kill_process("WhatsApp.exe")
        kill_process("WhatsApp.Root.exe")
        return True

    def new_chat(self, text: str) -> bool:
        logger.info("Plugin Action: Triggering new chat in WhatsApp")
        trigger_new_chat()
        return True

    def _set_clipboard(self, value: str) -> bool:
        """Copies text to the Windows clipboard via PowerShell."""
        try:
            safe = value.replace("'", "''")
            subprocess.run(
                ["powershell", "-Command", f"Set-Clipboard -Value '{safe}'"],
                check=True, capture_output=True
            )
            return True
        except Exception as e:
            logger.error(f"Clipboard error: {e}")
            return False

    def _focus_whatsapp(self) -> bool:
        """Launches and brings WhatsApp window to the front without disturbing its geometry."""
        logger.info("Activating WhatsApp Desktop...")
        # 'start whatsapp:' opens WhatsApp or brings existing instance to the front
        subprocess.Popen("start whatsapp:", shell=True)
        time.sleep(1.8)

        # If window handle is found, ensure foreground focus
        hwnd = user32.FindWindowW(None, "WhatsApp")
        if hwnd:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.3)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.4)
        return True

    def _parse_with_llm(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Uses local Ollama (qwen2.5) to reliably extract recipient and message body."""
        if not HAS_OLLAMA:
            return None, None

        try:
            system_prompt = (
                "Extract the contact name and message body from a WhatsApp voice command.\n"
                "Return ONLY valid JSON: {\"contact\": \"...\", \"message\": \"...\"}\n"
                "If the user did NOT specify a message to send (e.g. they only said 'send message to [name]' or 'open chat with [name]'), set \"message\": null.\n\n"
                "Examples:\n"
                "User: \"send hi to mom\"\n"
                "{\"contact\": \"mom\", \"message\": \"hi\"}\n"
                "User: \"send message to mom\"\n"
                "{\"contact\": \"mom\", \"message\": null}\n"
                "User: \"open whatsapp and send message to mom saying that i will be late\"\n"
                "{\"contact\": \"mom\", \"message\": \"i will be late\"}\n"
                "User: \"tell dad that dinner is ready\"\n"
                "{\"contact\": \"dad\", \"message\": \"dinner is ready\"}\n"
                "User: \"send a message to rahul\"\n"
                "{\"contact\": \"rahul\", \"message\": null}"
            )

            res = ollama.chat(
                model='qwen2.5:0.5b',
                keep_alive='60s',
                options={'temperature': 0.0, 'num_ctx': 512},
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'User: "{text}"'}
                ]
            )

            content = res.get('message', {}).get('content', '').strip()
            if "```" in content:
                content = re.sub(r"^```(?:json)?", "", content, flags=re.MULTILINE)
                content = content.replace("```", "").strip()

            data = json.loads(content)
            contact = data.get("contact")
            message = data.get("message")
            if contact:
                contact = str(contact).strip(".!?, \t\n")
                if message is not None:
                    message = str(message).strip()
                    if message.lower() in ("null", "none", ""):
                        message = None
                    elif message.lower() not in text.lower():
                        message = None
                logger.info(f"Ollama parsed WhatsApp command: contact='{contact}', message='{message}'")
                return contact, message
        except Exception as e:
            logger.warning(f"Ollama WhatsApp extraction skipped ({e}). Using regex fallback.")
        return None, None

    def _parse_contact_and_message(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts (contact_name, message_body) using LLM first, with regex fallback."""
        # 1. Try local LLM (Ollama)
        contact, message = self._parse_with_llm(text)
        if contact:
            return contact, message

        # 2. Fast Regex Fallback
        clean_contact = lambda s: re.sub(
            r"\b(?:send|message|text|to|in|on|whatsapp|app|desktop|please|can|you|open|a|chat|with|and)\b",
            "", s, flags=re.IGNORECASE
        ).strip(".!?, \t\n")

        # Pattern: "tell [contact] [message]"
        tell_match = re.match(r'\btell\s+(\w+(?:\s+\w+)?)\s+(.+)', text, re.IGNORECASE)
        if tell_match:
            return tell_match.group(1).strip(), tell_match.group(2).strip(".!?, \t\n")

        # Pattern: separator "saying that" / "saying" / "that"
        sep_match = re.search(r'\b(?:saying that|saying|that)\b', text, re.IGNORECASE)
        if sep_match:
            before_sep = text[:sep_match.start()]
            return clean_contact(before_sep), text[sep_match.end():].strip(".!?, \t\n")

        # Pattern: "send [body] to [contact]"
        send_match = re.match(r'\bsend\s+(.+?)\s+to\s+([\w\s]+?)(?:\s+(?:in|on|via)\s+\w+)?$', text, re.IGNORECASE)
        if send_match:
            potential_msg = send_match.group(1).strip()
            contact = send_match.group(2).strip(".!?, \t\n")
            if re.match(r'^(a\s+)?message$', potential_msg, re.IGNORECASE):
                return contact, None
            return contact, potential_msg

        # Fallback
        return clean_contact(text), None

    def send_message(self, text: str) -> bool:
        contact_name, message_body = self._parse_contact_and_message(text)
        if not contact_name:
            logger.warning(f"Could not extract contact name from: '{text}'")
            return False

        logger.info(f"WhatsApp target contact: '{contact_name}', message: '{message_body}'")

        # 1. Launch & focus WhatsApp window
        self._focus_whatsapp()

        # 2. Open New Chat (Ctrl+N)
        trigger_new_chat()
        time.sleep(1.0)

        # 3. Paste contact name and search
        if not self._set_clipboard(contact_name):
            return False
        _press_paste()
        time.sleep(1.8)

        # Select first result & open chat
        _press_key(VK_DOWN)
        time.sleep(0.2)
        trigger_press_enter()

        # 4. Type and send message (if provided)
        if message_body:
            time.sleep(1.5)
            if not self._set_clipboard(message_body):
                return False
            _press_paste()
            time.sleep(0.3)
            trigger_press_enter()
            logger.info(f"Message sent to '{contact_name}': '{message_body}'")

        return True
