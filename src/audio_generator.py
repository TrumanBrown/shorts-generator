"""Text-to-speech generation via Azure Speech or ElevenLabs.

Provides a unified ``generate_tts`` entry point that dispatches to the
provider configured by the ``TTS_PROVIDER`` environment variable.  Azure TTS
returns per-word timing data used for dynamic subtitle rendering.
"""

import logging
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from elevenlabs.client import ElevenLabs

from src.config import (
    AZURE_TTS_KEY,
    AZURE_TTS_REGION,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    TTS_PROVIDER,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_tts(text: str, path: str | Path) -> list[dict]:
    """Generate a TTS audio file for *text* at *path*.

    Returns a list of word-timing dicts (``{word, start, duration}`` in ms)
    when available (Azure), or an empty list (ElevenLabs).
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if TTS_PROVIDER == "elevenlabs":
        return _generate_elevenlabs(text, str(path))
    return _generate_azure(text, str(path))


# ---------------------------------------------------------------------------
# Azure Speech
# ---------------------------------------------------------------------------

def _generate_azure(text: str, path: str) -> list[dict]:
    """Synthesize speech with Azure Cognitive Services.

    Raises:
        EnvironmentError: If Azure TTS credentials are missing.
        RuntimeError: If synthesis fails.
    """
    if not AZURE_TTS_KEY or not AZURE_TTS_REGION:
        raise EnvironmentError(
            "AZURE_TTS_KEY and AZURE_TTS_REGION must be set for Azure TTS."
        )

    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_TTS_KEY, region=AZURE_TTS_REGION
    )
    speech_config.speech_synthesis_voice_name = "en-US-BrianMultilingualNeural"

    audio_config = speechsdk.audio.AudioOutputConfig(filename=path)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    word_timings: list[dict] = []

    def _on_word_boundary(evt):
        word_timings.append({
            "word": evt.text,
            "start": evt.audio_offset / 10_000,  # ticks → milliseconds
            "duration": (
                evt.duration.total_seconds() * 1000 if evt.duration else 0
            ),
        })

    synthesizer.synthesis_word_boundary.connect(_on_word_boundary)

    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Azure TTS failed: {result.reason}")

    logger.info("Azure TTS complete (%d words) → %s", len(word_timings), path)
    return word_timings


# ---------------------------------------------------------------------------
# ElevenLabs
# ---------------------------------------------------------------------------

def _generate_elevenlabs(text: str, path: str) -> list[dict]:
    """Synthesize speech with ElevenLabs.

    Raises:
        EnvironmentError: If the ElevenLabs API key is missing.
        RuntimeError: If the API call fails.
    """
    if not ELEVENLABS_API_KEY:
        raise EnvironmentError("ELEVENLABS_API_KEY must be set.")

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    try:
        audio_stream = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
        )
        with open(path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
    except Exception as exc:
        raise RuntimeError(f"ElevenLabs TTS failed: {exc}") from exc

    logger.info("ElevenLabs TTS complete → %s", path)
    return []  # ElevenLabs does not provide word-level timings
