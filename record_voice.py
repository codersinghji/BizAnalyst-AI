
import sounddevice as sd
from scipy.io.wavfile import write

DURATION = 6
SAMPLE_RATE = 16000

print("Recording will start in 2 seconds...")
input("Press ENTER when you are ready to speak: ")

print("Recording... Speak now!")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16"
)

sd.wait()

write("voice_input.wav", SAMPLE_RATE, audio)

print("Recording saved successfully!")
print("File: voice_input.wav")
