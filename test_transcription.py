
import io
from agents.voice_agent import transcribe_audio

print("\n===== TESTING HINDI VOICE INPUT =====")

try:
    with open("voice_input.wav", "rb") as file:
        audio_bytes = file.read()

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice_input.wav"
    audio_file.type = "audio/wav"

    transcript = transcribe_audio(
        audio_file,
        language="Hindi"
    )

    print("\nRECOGNIZED HINDI SPEECH:")
    print(transcript)

    if transcript:
        print("\nSUCCESS: Hindi voice recognition is working!")
    else:
        print("\nNo speech detected.")

except Exception as error:
    print("\nVOICE INPUT ERROR:")
    print(error)
