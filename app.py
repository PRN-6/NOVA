import sys
import logging
from speech.streamer import SpeechStreamer
from actions.executor import execute_system_command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NOVA.Core")

def on_text_transcribed(text: str) -> bool:
    """Callback hook executed whenever a transcription segment settles."""
    # Write to terminal using stdout flush to update line live
    sys.stdout.write(f"\r[User Input] {text}")
    sys.stdout.flush()
    
    # Forward the text payload to command executor
    return execute_system_command(text)

def main() -> None:
    logger.info("Initializing NOVA Assistant Services...")
    try:
        streamer = SpeechStreamer()
        streamer.start(on_text_collback=on_text_transcribed)
    except KeyboardInterrupt:
        logger.info("Graceful shutdown sequence initialized by user.")
    except Exception as e:
        logger.critical(f"Unhandled fatal error in main thread: {e}")
        sys.exit(1)
    finally:
        logger.info("Cleanup completed. NOVA is offline.")

if __name__ == "__main__":
    main()