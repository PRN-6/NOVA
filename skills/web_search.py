import logging
import re
import subprocess
import urllib.parse
import webbrowser
from skills.base_skill import BaseSkill

logger = logging.getLogger("NOVA.WebSearchSkill")

class WebSearch(BaseSkill):

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "- web_search: Use this when the user asks to search the web, google something, find information, look up a topic, or browse queries (e.g., 'search python tutorial', 'look up today weather', 'google latest tech news')."

    @property
    def fast_intents(self) -> list[str]:
        return [
            "search",
            "search for",
            "search the web",
            "search google",
            "search online",
            "google",
            "google search",
            "look up",
            "find online",
            "search web",
        ]

    def _extract_query(self, text: str) -> tuple[str, str]:
        """
        Extracts the search query and any preferred browser mention.
        Returns: (query_text, target_browser_or_empty)
        """
        cleaned = text.strip(".!?, \t\n")
        target_browser = ""
        
        if re.search(r"\bbrave\b", cleaned, re.IGNORECASE):
            target_browser = "brave"
        elif re.search(r"\bchrome\b", cleaned, re.IGNORECASE):
            target_browser = "chrome"

        patterns = [
            r"^(?:please\s+)?search\s+(?:for|about|on|google)?\s*(.+)$",
            r"^(?:please\s+)?look\s+up\s*(.+)$",
            r"^(?:please\s+)?google\s*(.+)$",
            r"^(?:please\s+)?find\s+(?:me\s+)?(?:information\s+about\s+|info\s+on\s+)?(.+)$",
        ]

        query = ""
        for p in patterns:
            m = re.match(p, cleaned, re.IGNORECASE)
            if m:
                query = m.group(1).strip()
                break

        if not query:
            # Fallback: remove leading trigger words if any
            query = re.sub(r"^(?:search|google|look up|find)\s*", "", cleaned, flags=re.IGNORECASE).strip()

        # Clean browser words from query if present
        query = re.sub(r"\b(?:in|on|using|with)?\s*(?:brave|chrome|google|browser)\b", "", query, flags=re.IGNORECASE).strip()

        return query, target_browser

    def _detect_running_browser(self) -> str:
        """Detects if Brave or Chrome is currently open on Windows."""
        try:
            output = subprocess.check_output("tasklist /FI \"STATUS eq RUNNING\"", shell=True, text=True).lower()
            if "brave.exe" in output:
                return "brave"
            elif "chrome.exe" in output:
                return "chrome"
        except Exception as e:
            logger.debug(f"Could not check running tasks: {e}")
        return ""

    def execute(self, text: str) -> bool:
        query, target_browser = self._extract_query(text)
        
        if not query:
            query = text.strip(".!? ")

        logger.info(f"AI Action: Searching web for '{query}'")
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"

        # 1. If user explicitly specified browser
        if target_browser:
            subprocess.Popen(f'start {target_browser} "{search_url}"', shell=True)
            return True

        # 2. If Brave or Chrome is already open, open tab in that running browser
        running_browser = self._detect_running_browser()
        if running_browser:
            logger.info(f"Detected running browser: '{running_browser}'. Opening search tab...")
            subprocess.Popen(f'start {running_browser} "{search_url}"', shell=True)
            return True

        # 3. Fallback: Open in system default browser
        webbrowser.open(search_url)
        return True
