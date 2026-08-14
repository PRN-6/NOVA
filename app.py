from speech.recorder import record_audio
from speech.recognizer import recognize

print("Nova assistant started")

print("Say something...")

record_audio("input.wav")

text = recognize("input.wav")

print("You said:", text)