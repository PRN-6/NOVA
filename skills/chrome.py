import logging
import re
import subprocess
import time
import urllib.parse
import pyautogui
from skills.base_skill import BaseSkill

logger = logging.getLogger("NOVA.ChromeSkill")

# Only sites whose real URL differs from www.[name].com
# Everything else is handled automatically by the generic site opener
SITE_MAP = {
    "gmail":      "https://mail.google.com",
    "whatsapp":   "https://web.whatsapp.com",
    "chatgpt":    "https://chat.openai.com",
    "maps":       "https://maps.google.com",
    "meet":       "https://meet.google.com",
    "drive":      "https://drive.google.com",
    "translate":  "https://translate.google.com",
}

class Chrome(BaseSkill):

    @property
    def name(self) -> str:
        return "open_chrome"

    @property
    def description(self) -> str:
        return (
            "- open_chrome: Use this when the user wants to browse the web, search Google or YouTube, "
            "open a specific website, open a new tab, close a tab, go back, go forward, refresh the page, "
            "open incognito mode, open bookmarks, open history, or open downloads."
        )

    @property
    def fast_intents(self) -> list[str]:
        return [
            # Launch
            "open chrome", "launch chrome", "start chrome", "open browser",
            # Search
            "search", "google", "search for", "look up", "find",
            "search on chrome", "search in chrome", "chrome search", "google search",
            # YouTube
            "open youtube", "youtube", "search on youtube", "search youtube", "play on youtube",
            # Specific sites
            "open gmail", "open reddit", "open github", "open twitter",
            "open instagram", "open facebook", "open netflix", "open chatgpt",
            "open maps", "open google maps", "open google drive", "open google meet",
            "open whatsapp web", "open stackoverflow",
            # Tab control
            "new tab", "open new tab", "close tab", "close this tab",
            "reopen tab", "reopen closed tab",
            # Navigation
            "go back", "go forward", "refresh", "reload", "reload page", "refresh page",
            # Window control
            "incognito", "open incognito", "new incognito tab", "private mode",
            # Browser features
            "open bookmarks", "open history", "open downloads",
            "zoom in", "zoom out", "reset zoom",
            "scroll down", "scroll up",
            "open developer tools", "open settings",
        ]

    # --- Private Helpers ---

    def _google_search(self, query: str) -> None:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        subprocess.Popen(f'start chrome "{url}"', shell=True)
        logger.info(f"Chrome: Google search -> '{query}'")

    def _youtube_search(self, query: str) -> None:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        subprocess.Popen(f'start chrome "{url}"', shell=True)
        logger.info(f"Chrome: YouTube search -> '{query}'")

    def _open_url(self, url: str) -> None:
        subprocess.Popen(f'start chrome "{url}"', shell=True)
        logger.info(f"Chrome: Opening URL -> {url}")

    def _shortcut(self, *keys, delay: float = 0.1) -> None:
        """Sends a keyboard shortcut to the active Chrome window."""
        time.sleep(delay)
        pyautogui.hotkey(*keys)

    def _extract_query(self, text: str) -> str:
        """Extracts the Google search query from the voice command."""
        cleaned = text.strip(".!?, ")
        patterns = [
            r"search\s+(?:for|about|on)?\s*(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser|google))?$",
            r"look\s+up\s+(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
            r"find\s+(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
            r"google\s+(.+?)(?:\s+(?:in|on|using|with)\s+(?:chrome|browser))?$",
        ]
        for p in patterns:
            m = re.search(p, cleaned, re.IGNORECASE)
            if m:
                query = m.group(1).strip()
                query = re.sub(r"\b(?:in|on|using|with)?\s*(?:chrome|browser)\b", "", query, flags=re.IGNORECASE).strip()
                if query:
                    return query
        return ""

    def _extract_youtube_query(self, text: str) -> str:
        """Extracts the search query for a YouTube voice command."""
        patterns = [
            r"(?:search|find|look up|play)\s+(?:on|in|for|about)?\s*youtube\s+(?:for|about)?\s*(.+)$",
            r"(?:search|find|look up|play)\s+(.+?)\s+(?:on|in)\s+youtube$",
            r"youtube\s+(?:search|find|play|look up)\s+(?:for|about)?\s*(.+)$",
        ]
        for p in patterns:
            m = re.search(p, text.strip(), re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_site(self, text: str) -> str:
        """Returns a URL if the user mentions a specific well-known site."""
        for site, url in SITE_MAP.items():
            if re.search(rf"\b{re.escape(site)}\b", text, re.IGNORECASE):
                return url
        return ""

    # --- Main Execute ---

    def execute(self, text: str) -> bool:
        text_lower = text.lower()

        # YouTube Search
        yt_query = self._extract_youtube_query(text_lower)
        if yt_query:
            self._youtube_search(yt_query)
            return True

        # Navigation Controls
        if re.search(r"\bgo\s+back\b|\bback\b", text_lower):
            self._shortcut("alt", "left")
            logger.info("Chrome: Go back")
            return True

        if re.search(r"\bgo\s+forward\b|\bforward\b", text_lower):
            self._shortcut("alt", "right")
            logger.info("Chrome: Go forward")
            return True

        if re.search(r"\brefresh\b|\breload\b", text_lower):
            self._shortcut("f5")
            logger.info("Chrome: Refresh page")
            return True

        # Tab Controls
        if re.search(r"\bnew\s+tab\b|\bopen\s+(a\s+)?new\s+tab\b", text_lower):
            self._shortcut("ctrl", "t")
            logger.info("Chrome: New tab")
            return True

        if re.search(r"\bclose\s+tab\b|\bclose\s+this\s+tab\b", text_lower):
            self._shortcut("ctrl", "w")
            logger.info("Chrome: Close tab")
            return True

        if re.search(r"\breopen\b|\breopen\s+(closed\s+)?tab\b", text_lower):
            self._shortcut("ctrl", "shift", "t")
            logger.info("Chrome: Reopen closed tab")
            return True

        # Window Controls
        if re.search(r"\bincognito\b|\bprivate\s+mode\b|\bprivate\s+tab\b", text_lower):
            subprocess.Popen("start chrome --incognito", shell=True)
            logger.info("Chrome: Opening incognito window")
            return True

        # Browser Pages
        if re.search(r"\bbookmarks\b", text_lower):
            self._open_url("chrome://bookmarks")
            return True

        if re.search(r"\bhistory\b", text_lower):
            self._open_url("chrome://history")
            return True

        if re.search(r"\bdownloads\b", text_lower):
            self._open_url("chrome://downloads")
            return True

        if re.search(r"\bsettings\b", text_lower):
            self._open_url("chrome://settings")
            return True

        if re.search(r"\bdeveloper\s+tools\b|\bdev\s+tools\b", text_lower):
            self._shortcut("f12")
            logger.info("Chrome: Open Developer Tools")
            return True

        # Zoom
        if re.search(r"\bzoom\s+in\b", text_lower):
            self._shortcut("ctrl", "+")
            logger.info("Chrome: Zoom in")
            return True

        if re.search(r"\bzoom\s+out\b", text_lower):
            self._shortcut("ctrl", "-")
            logger.info("Chrome: Zoom out")
            return True

        if re.search(r"\breset\s+zoom\b", text_lower):
            self._shortcut("ctrl", "0")
            logger.info("Chrome: Reset zoom")
            return True

        # Scroll
        if re.search(r"\bscroll\s+down\b", text_lower):
            pyautogui.scroll(-5)
            logger.info("Chrome: Scroll down")
            return True

        if re.search(r"\bscroll\s+up\b", text_lower):
            pyautogui.scroll(5)
            logger.info("Chrome: Scroll up")
            return True

        # Open a specific known site (from SITE_MAP)
        site_url = self._extract_site(text_lower)
        if site_url:
            self._open_url(site_url)
            return True

        # Generic site opener — "open Spotify" -> www.spotify.com
        # Catches any site not in SITE_MAP automatically
        m = re.search(r"\bopen\s+([a-zA-Z0-9]+)\b", text_lower)
        if m:
            site_name = m.group(1).strip()
            # Skip keywords that shouldn't be converted to www.[name].com
            skip_words = {
                "chrome", "google", "browser", "incognito", "tab", "new", "a", "the",
                "settings", "downloads", "history", "bookmarks", "dev", "tools",
                "whatsapp", "brave", "notepad", "app", "file", "folder", "window"
            }
            if site_name not in skip_words:
                url = f"https://www.{site_name}.com"
                logger.info(f"Chrome: Generic site open -> {url}")
                self._open_url(url)
                return True

        # Google Search with a query
        query = self._extract_query(text)
        if query:
            self._google_search(query)
            return True

        # Fallback: just open Chrome
        logger.info("Chrome: Launching Google Chrome")
        subprocess.Popen("start chrome", shell=True)
        return True
