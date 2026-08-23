from faster_whisper import WhisperModel

model = WhisperModel(
    "medium",
    device="cpu",
    compute_type="int8"
)

def recognize(filename: str) -> str:

    segments , info = model.transcribe(
        filename,
        beam_size=5,
        language="en",
        vad_filter=True,
        initial_prompt="Orion, Chrome, WhatsApp, Outlook, Excel, VS Code, GitHub"
    )

    text = ""

    for segment in segments:
        text += segment.text.strip() + " "

    return text.strip()

if __name__ == "__main__":
    result = recognize("record.wav")

    print("\nRecognized text:")
    print(result)