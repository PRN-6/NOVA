from typing import final
import sys
import logging
from speech.streamer import SpeechStreamer
from actions.executor import execute_system_command

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",

)

logger = logging.getLogger("NOVA.Core")

def on_text_transcribe(text: str) -> bool:
    sys.stdout.write(f"\r[user input] {text}")
    sys.stdout.flush()

    return execute_system_command(text)

def main() -> None:
    logger.info("Initializing Nova assistant services..")

    try:
        streamer = SpeechStreamer()
        streamer.start(on_text_transcribe)
    except Exception as e:
        logger.critical(f"unhandled failure: {e}")
        sys.exit(1)
    finally:
        logger.info("cleanup completed")

if __name__ == "__main__":
    main()