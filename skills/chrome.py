import logging
import re
import subprocess
import urllib.parse
from skills.base_skill import BaseSkill

logger = logging.getLogger("NOVA.ChromeSkill")

class Chrome(BaseSkill):

    @property
    def name(self) -> str:
        return "open_chrome"

    @property
    def description(self) -> str:
        return "- open_chrome: Use this when the user wants to browse, search the web, look up topics, or open Google Chrome."

    @property
    def fast_intents(self) -> list[str]:
        return [
            "open chrome",
            "launch chrome",
            "start chrome",
            "open browser",
            "launch browser",
            "chrome",
            "search in chrome",
            "search on chrome",
            "search with chrome",
            "chrome search",
            "google search",
        ]

    def _extract_query(self, text: str) -> str:
        """Extracts the search query from user voice command if present."""
        cleaned = text.strip(".!?, ")
        patterns = [
            r"search\s+(?:for|about|on)?\s*(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
            r"look\s+up\s*(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
            r"find\s*(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
            r"google\s*(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
        ]
        for p in patterns:
            m = re.search(p, cleaned, re.IGNORECASE)
            if m:
                query = m.group(1).strip()
                # Clean any lingering trigger words
                query = re.sub(r"\b(?:in|on|using|with)?\s*(?:chrome|browser)\b", "", query, flags=re.IGNORECASE).strip()
                if query:
                    return query
        return ""

    def execute(self, text: str) -> bool:
        query = self._extract_query(text)
        if query:
            logger.info(f"AI Action: Searching Chrome for '{query}'")
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            subprocess.Popen(f'start chrome "{url}"', shell=True)
        else:
            logger.info("AI Action: Launching Google Chrome")
            subprocess.Popen("start chrome", shell=True)
        return True

