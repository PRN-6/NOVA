import logging
import subprocess
from skills.base_skill import BaseSkill

logger = logging.getLogger("NOVA.ChromeSkill")

class Chrome(BaseSkill):

    @property
    def name(self) -> str:
        return "open_chrome"

    @property
    def description(self) -> str:
        return "- open_chrome: Use this when the user wants to browse, search, or open Google Chrome."

    @property
    def fast_intents(self) -> list[str]:
        return [
            "open chrome",
            "launch chrome",
            "start chrome",
            "open browser",
            "launch browser",
            "chrome",
        ]

    def execute(self, text: str) -> bool:
        logger.info("AI Action: Launching Google Chrome")
        subprocess.Popen("start chrome", shell=True)
        return True
