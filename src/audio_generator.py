import os
from elevenlabs.client import ElevenLabs
import azure.cognitiveservices.speech as speechsdk
from src.config import AZURE_TTS_KEY, AZURE_TTS_REGION

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "azure").lower()


def generate_tts(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if TTS_PROVIDER == "azure":
        return generate_tts_azure(text, path)
    return generate_tts_elevenlabs(text, path)


def generate_tts_elevenlabs(text, path):
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
            model_id="eleven_multilingual_v2",
        )
        with open(path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        print(f"Generated TTS with ElevenLabs: {path}")
        return []  # ElevenLabs API does not return timings
    except Exception as e:
        raise RuntimeError(f"ElevenLabs TTS failed: {e}")


def generate_tts_azure(text, path):
    if not AZURE_TTS_KEY or not AZURE_TTS_REGION:
        raise EnvironmentError("AZURE_TTS_KEY and AZURE_TTS_REGION must be set for Azure TTS.")

    speech_config = speechsdk.SpeechConfig(subscription=AZURE_TTS_KEY, region=AZURE_TTS_REGION)
    speech_config.speech_synthesis_voice_name = "en-US-BrianMultilingualNeural"

    audio_config = speechsdk.audio.AudioOutputConfig(filename=path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    word_timings = []

    def word_boundary_handler(evt):
        start_time_ms = evt.audio_offset / 10000  # convert to ms
        word_timings.append(
            {
                "word": evt.text,
                "start": start_time_ms,
                "duration": evt.duration.total_seconds() * 1000 if evt.duration else 0,
            }
        )

    synthesizer.synthesis_word_boundary.connect(word_boundary_handler)

    try:
        result = synthesizer.speak_text_async(text).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"Azure TTS failed with reason: {result.reason}")

        print(f"Generated TTS with Azure: {path}")
        return word_timings
    except Exception as e:
        raise RuntimeError(f"Azure TTS failed: {e}")
