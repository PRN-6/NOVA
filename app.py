import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# 1. PyInstaller frozen-safe base directory resolution
#    sys._MEIPASS is set when running as a compiled .exe — use it as base.
#    Falls back to the script's own directory when running from source.
# ─────────────────────────────────────────────────────────────────────────────
IS_FROZEN = getattr(sys, "frozen", False)
BASE_DIR = sys._MEIPASS if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# 2. User AppData Directory — safe persistent storage for logs & config
# ─────────────────────────────────────────────────────────────────────────────
APPDATA_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NOVA")
os.makedirs(APPDATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(APPDATA_DIR, "nova.log")

# ─────────────────────────────────────────────────────────────────────────────
# 3. CUDA 12 Runtime DLL paths (required by faster-whisper / ctranslate2)
#    Search both frozen (dist/NOVA/nvidia/*) and source (.venv) locations.
# ─────────────────────────────────────────────────────────────────────────────
for _pkg in ["cublas", "cudnn", "cuda_nvrtc"]:
    for _candidate in [
        os.path.join(BASE_DIR, "nvidia", _pkg, "bin"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Lib", "site-packages", "nvidia", _pkg, "bin"),
    ]:
        if os.path.isdir(_candidate):
            try:
                os.add_dll_directory(_candidate)
                os.environ["PATH"] = _candidate + os.pathsep + os.environ["PATH"]
            except Exception:
                pass

import logging
import threading

# ─────────────────────────────────────────────────────────────────────────────
# 4. Logging — always write to AppData log file; only echo to stdout if a
#    console is attached (i.e. not in --windowed EXE mode where stdout=None).
# ─────────────────────────────────────────────────────────────────────────────
log_handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if sys.stdout is not None:
    log_handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger("NOVA.Core")

logger.info(f"NOVA starting — frozen={IS_FROZEN}, base={BASE_DIR}")
logger.info(f"Log file: {LOG_FILE}")

from speech.streamer import SpeechStreamer
from actions.executor import execute_system_command
from ui.manager import UIManager


def main() -> None:
    if "--dashboard" in sys.argv or "--settings" in sys.argv:
        logger.info("Launching NOVA Control Center Dashboard...")
        from ui.dashboard_runner import run_dashboard
        run_dashboard()
        return

    logger.info("Initializing NOVA Assistant Services...")

    ui_manager = UIManager()

    def on_text_transcribed(text: str) -> bool:
        """Callback hook executed whenever a transcription segment settles."""
        logger.info(f"User: '{text}'")
        if sys.stdout is not None:
            try:
                sys.stdout.write(f"\r[User Input] {text}\n")
                sys.stdout.flush()
            except Exception:
                pass

        ui_manager.on_transcription(text)
        return execute_system_command(
            text,
            on_action_callback=ui_manager.on_action_completed
        )

    try:
        # Start System Tray in background
        ui_manager.start_tray()

        # Initialize Audio Streamer
        streamer = SpeechStreamer()

        # Run speech streamer in a dedicated worker thread
        audio_thread = threading.Thread(
            target=streamer.start,
            kwargs={
                "on_text_callback": on_text_transcribed,
                "on_wake_word_callback": ui_manager.on_wake_word_detected,
                "on_audio_energy_callback": ui_manager.on_audio_energy,
                "on_sleep_callback": ui_manager.on_sleep
            },
            daemon=True
        )
        audio_thread.start()

        # Run the Floating HUD Tkinter loop on the main thread
        logger.info("Starting NOVA Floating HUD Overlay...")
        ui_manager.run_hud_loop()

    except KeyboardInterrupt:
        logger.info("Graceful shutdown sequence initialized by user.")
    except Exception as e:
        logger.critical(f"Unhandled fatal error in main thread: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Cleanup completed. NOVA is offline.")


if __name__ == "__main__":
    main()