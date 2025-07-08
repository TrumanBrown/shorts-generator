import os
from elevenlabs.client import ElevenLabs

def generate_tts(text, path):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    if not api_key:
        raise EnvironmentError("ELEVENLABS_API_KEY not set")

    client = ElevenLabs(api_key=api_key)

    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2"
        )
        with open(path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        print(f"Generated TTS: {path}")
    except Exception as e:
        raise RuntimeError(f"ElevenLabs TTS failed: {e}")
