import queue
import sys
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


# initializing the whiper model
SAMPLE_RATE = 16000
model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

#initialize the queue
audio_queue = queue.Queue()

#the audio callback function
def audio_callback(indata, frames, time, status):
    #copy the audio to the queue
    if status:
        print(status)

    audio_queue.put(indata.copy())

#the microphone stream
stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    blocksize=8000, #processes the aduio in to 0.5 seconds chunks
    callback=audio_callback
)

#creating a threshold for silence 
SILENCE_THRESHOLD = 0.1
SILENCE_DURATION_CHUNKS = 3

#the main stream loop
def start_streaming():
    audio_buffer = [] #adding all the audio chunks here 
    silence_counter = 0

    print("\n[Nova] Listening... Speak into the microphone. (Press Ctrl+C to stop)")

    with stream:
        while True:
            try:
                #Get the next chunk from the queue
                chunk = audio_queue.get()

                #calculate the current chunk
                volume = np.sqrt(np.mean(chunk**2))

                #check if the chunk is silent
                if volume < SILENCE_THRESHOLD:
                    silence_counter+=1
                else:
                    silence_counter = 0
                
                if silence_counter >= SILENCE_DURATION_CHUNKS:
                    if len(audio_buffer) > 0:
                        audio_buffer.clear()
                        print("\n[Nova] Resetting buffer (silence detected)...")
                        continue

                audio_buffer.append(chunk)

                #concatinate chunks 
                full_audio = np.concatenate(audio_buffer).flatten()

                if len(full_audio) > SAMPLE_RATE * 10:
                    audio_buffer = audio_buffer[-20:]
                    full_audio = np.concatenate(audio_buffer).flatten()

                # transcribe the audio
                segments , info = model.transcribe(
                    full_audio,
                    beam_size=3,
                    language='en',
                    vad_filter=True,  # Automatically filters out silence
                    initial_prompt="Nova, Chrome, WhatsApp, Outlook, Excel, VS Code, GitHub"
                )

                text=""

                for segment in segments:
                    text+=segment.text.strip() + " "
                
                text = text.strip()

                if text:
                    print(f"\rYou: {text}", end="", flush=True)

                    if "chrome" in text.lower():
                        print("\n[Nova] Opening Chrome...")
                        audio_buffer.clear()
                        silence_counter = 0
                
            except KeyboardInterrupt:
                print("\n stopping...")
                break

if __name__ == "__main__":
    start_streaming()