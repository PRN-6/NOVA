import logging
from skills.base_skill import BaseSkill
import subprocess

logger = logging.getLogger("NOVA.whatsappskill")

class Whatsapp(BaseSkill):

    @property
    def name(self) -> str:
        return "open_whatsapp"
    
    @property
    def description(self) -> str:
        return "- open_whatsapp: Use this when the user wants to chat, text, or open WhatsApp."

    @property
    def fast_intents(self) -> list[str]:
        return [
            "open whatsapp",
            "launch whatsapp",
            "start whatsapp",
            "open wa",
            "launch wa",
            "start wa",
        ]

    def execute(self,text: str) -> bool:
        subprocess.Popen("start whatsapp:",shell=True)
        return True