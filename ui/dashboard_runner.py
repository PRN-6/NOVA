import os
import sys
import logging

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import webview
from ui.dashboard_bridge import DashboardAPI

logger = logging.getLogger("NOVA.DashboardRunner")

def get_dashboard_html_path() -> str:
    """Resolves the path to index.html supporting both source and PyInstaller."""
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = PROJECT_ROOT

    html_path = os.path.join(base, "ui", "dashboard", "index.html")
    if not os.path.exists(html_path):
        alt_path = os.path.join(os.path.dirname(__file__), "dashboard", "index.html")
        if os.path.exists(alt_path):
            return alt_path
    return html_path

def run_dashboard():
    """Launches the modern NOVA Control Center via WebView2."""
    html_path = get_dashboard_html_path()
    if not os.path.exists(html_path):
        logger.error(f"Dashboard HTML file not found at: {html_path}")
        return

    api = DashboardAPI()
    window = webview.create_window(
        title="NOVA Control Center",
        url=html_path,
        js_api=api,
        width=1000,
        height=740,
        min_size=(800, 620),
        text_select=True
    )
    api.set_window(window)

    logger.info(f"Opening NOVA Tailwind Control Center via WebView2 ({html_path})...")
    webview.start(debug=False)

if __name__ == "__main__":
    run_dashboard()
