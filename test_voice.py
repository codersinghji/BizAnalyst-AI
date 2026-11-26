
from agents.voice_agent import get_voice_status, text_to_speech

print("\n===== VOICE ENGINE STATUS =====")

status = get_voice_status()

print("Speech recognition:", status["speech_to_text"])
print("Speech output:", status["text_to_speech"])
print("Installed voices:", status["voice_count"])
print("English voice:", status["english_voice_available"])
print("Hindi voice:", status["hindi_voice_available"])

print("\n===== TESTING ENGLISH SPEECH =====")

try:
    audio = text_to_speech(
        "Hello! Welcome to BizAnalyst AI. Your voice assistant is working.",
        language="English"
    )

    with open("voice_test.wav", "wb") as file:
        file.write(audio)

    print("SUCCESS: English audio created: voice_test.wav")

except Exception as error:
    print("English speech error:", error)

print("\nVoice engine test completed.")