import os
import sys
import logging
import threading

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import webview
from ui.dashboard_bridge import DashboardAPI

logger = logging.getLogger("PRIVACY68.DashboardRunner")

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


def _start_capture_stream() -> None:
    """
    Spins up a SpeechStreamer in the dashboard process solely for enrollment
    audio capture.  No Whisper is loaded; the stream just collects mic chunks
    via the callback so that _get_enrollment_audio() can tap it.
    """
    try:
        from speech.streamer import SpeechStreamer, set_speech_streamer
        streamer = SpeechStreamer()
        set_speech_streamer(streamer)
        # Open the InputStream so _audio_callback runs (needed for capture)
        streamer.stream.start()
        logger.info("Dashboard capture stream started (enrollment mode).")
    except Exception as e:
        logger.warning(f"Could not start dashboard capture stream: {e}")


def run_dashboard():
    """Launches the modern PRIVACY68 Control Center via WebView2."""
    html_path = get_dashboard_html_path()
    if not os.path.exists(html_path):
        logger.error(f"Dashboard HTML file not found at: {html_path}")
        return

    # Start a lightweight capture-only stream so enrollment uses the correct mic
    threading.Thread(target=_start_capture_stream, daemon=True).start()

    api = DashboardAPI()
    window = webview.create_window(
        title="PRIVACY68 Control Center",
        url=html_path,
        js_api=api,
        width=1000,
        height=740,
        min_size=(800, 620),
        text_select=True
    )
    api.set_window(window)

    logger.info(f"Opening PRIVACY68 Tailwind Control Center via WebView2 ({html_path})...")
    webview.start(debug=False)

if __name__ == "__main__":
    run_dashboard()
