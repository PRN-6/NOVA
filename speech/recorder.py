import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

SAMPLE_RATE = 44100

device = sd.default.device[0]

def record_audio(filename="record.wav",duration=10):
    print("recording....")

    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.int16,
        device=device
    )

   

    sd.wait()

    print("Maximum value:", np.max(audio))
    print("Minimum value:", np.min(audio))

    write(filename,SAMPLE_RATE,audio)

    print(f"saved to {filename}")

