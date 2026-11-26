"""Local bilingual speech-to-text and text-to-speech helpers."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_whisper_model = None
_whisper_model_name = None


def get_whisper_model(model_size: str = "tiny"):
    """Load Whisper once per Python process (not once per Streamlit rerun)."""
    global _whisper_model, _whisper_model_name
    if _whisper_model is None or _whisper_model_name != model_size:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=max(1, min(4, os.cpu_count() or 2)),
            num_workers=1,
        )
        _whisper_model_name = model_size
    return _whisper_model


def transcribe_audio(audio_file, language: str = "Auto detect") -> str:
    """Transcribe a Streamlit UploadedFile/audio object in English or Hindi."""
    if audio_file is None:
        raise ValueError("Please record or upload audio first.")

    audio_bytes = audio_file.getvalue() if hasattr(audio_file, "getvalue") else bytes(audio_file)
    if not audio_bytes:
        raise ValueError("The recorded audio is empty.")

    mime = getattr(audio_file, "type", "") or ""
    name = getattr(audio_file, "name", "") or ""
    suffix = Path(name).suffix or (".wav" if "wav" in mime else ".webm")
    temp_path = None

    language_map = {"English": "en", "Hindi": "hi", "Auto detect": None, "Auto": None}
    whisper_language = language_map.get(language, None)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(audio_bytes)
            temp_path = temp.name

        model = get_whisper_model("tiny")
        segments, info = model.transcribe(
            temp_path,
            language=whisper_language,
            beam_size=1,
            best_of=1,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        if not transcript:
            raise ValueError("No speech was detected. Please record again, speaking clearly.")
        return transcript
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def get_available_voices():
    """Return installed Windows/system voices where pyttsx3 is available."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = []
        for voice in engine.getProperty("voices"):
            languages = []
            for lang in getattr(voice, "languages", []) or []:
                if isinstance(lang, bytes):
                    lang = lang.decode("utf-8", errors="ignore")
                languages.append(str(lang))
            voices.append({"id": voice.id, "name": voice.name, "languages": languages})
        engine.stop()
        return voices
    except Exception:
        return []


def text_to_speech(text: str, language: str = "English") -> bytes:
    """Convert text to a WAV byte string using installed system voices."""
    if not text or not str(text).strip():
        raise ValueError("There is no response text to speak.")

    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty("voices") or []
    language_terms = ("hindi", "hi-in", "hi_in") if language.lower().startswith("hi") else ("english", "en-in", "en-us", "en-gb")

    selected = None
    for voice in voices:
        identity = (str(getattr(voice, "name", "")) + " " + str(getattr(voice, "id", ""))).lower()
        raw_languages = getattr(voice, "languages", []) or []
        langs = " ".join(x.decode("utf-8", errors="ignore") if isinstance(x, bytes) else str(x) for x in raw_languages).lower()
        if any(term in identity or term in langs for term in language_terms):
            selected = voice.id
            break

    if selected:
        engine.setProperty("voice", selected)
    engine.setProperty("rate", 165)
    engine.setProperty("volume", 0.9)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            temp_path = temp.name
        engine.save_to_file(str(text)[:3000], temp_path)
        engine.runAndWait()
        engine.stop()
        with open(temp_path, "rb") as audio:
            data = audio.read()
        if not data:
            raise RuntimeError("The system speech engine did not create an audio file.")
        return data
    finally:
        try:
            engine.stop()
        except Exception:
            pass
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def get_voice_status() -> dict:
    voices = get_available_voices()
    has_hindi = any("hindi" in v["name"].lower() or "hindi" in " ".join(v["languages"]).lower() for v in voices)
    has_english = any("english" in v["name"].lower() or "en" in " ".join(v["languages"]).lower() for v in voices)
    return {
        "speech_to_text": "faster-whisper tiny (local CPU)",
        "text_to_speech": "pyttsx3 (system voices)",
        "voice_count": len(voices),
        "hindi_voice_available": has_hindi,
        "english_voice_available": has_english,
        "voices": voices,
    }
