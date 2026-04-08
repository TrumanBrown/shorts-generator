"""Centralised configuration loaded from environment variables.

All credentials and file paths used by the pipeline are defined here.
Modules should import values from this module rather than calling
``os.getenv`` directly so that validation happens in one place.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Custom Search
# ---------------------------------------------------------------------------
GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID: str | None = os.getenv("GOOGLE_CSE_ID")

# ---------------------------------------------------------------------------
# Azure TTS
# ---------------------------------------------------------------------------
AZURE_TTS_KEY: str | None = os.getenv("AZURE_TTS_KEY")
AZURE_TTS_REGION: str | None = os.getenv("AZURE_TTS_REGION")

# ---------------------------------------------------------------------------
# ElevenLabs TTS (optional)
# ---------------------------------------------------------------------------
ELEVENLABS_API_KEY: str | None = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# ---------------------------------------------------------------------------
# Azure OpenAI (script generation)
# ---------------------------------------------------------------------------
AZURE_OPENAI_API_KEY: str | None = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION: str | None = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT: str | None = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ---------------------------------------------------------------------------
# TTS provider selection
# ---------------------------------------------------------------------------
TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "azure").lower()

# ---------------------------------------------------------------------------
# Video rendering constants
# ---------------------------------------------------------------------------
VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1080
VIDEO_FPS: int = 24
DEFAULT_CLIP_DURATION: float = 3.5  # seconds, used when audio is disabled
FADE_DURATION: float = 0.5

# ---------------------------------------------------------------------------
# Subtitle styling
# ---------------------------------------------------------------------------
SUBTITLE_FONT_SIZE: int = 60
SUBTITLE_COLOR: str = "yellow"
SUBTITLE_STROKE_COLOR: str = "black"
SUBTITLE_STROKE_WIDTH: int = 3
SUBTITLE_CAPTION_WIDTH: int = 900
SUBTITLE_BOTTOM_MARGIN: int = 60
IMAGEMAGICK_BINARY: str | None = os.getenv("IMAGEMAGICK_BINARY")
SUBTITLE_FONT_PATH: str = os.getenv(
    "SUBTITLE_FONT_PATH",
    "C:\\Windows\\Fonts\\arialbd.ttf" if os.name == "nt"
    else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
SCRIPT_PATH: Path = PROJECT_ROOT / "input" / "script.txt"
IMAGE_DIR: Path = PROJECT_ROOT / "input" / "images"
AUDIO_DIR: Path = PROJECT_ROOT / "audio"
OUTPUT_PATH: Path = PROJECT_ROOT / "output" / "final_video.mp4"

# Ensure directories exist on import
for _dir in (IMAGE_DIR, AUDIO_DIR, SCRIPT_PATH.parent, OUTPUT_PATH.parent):
    _dir.mkdir(parents=True, exist_ok=True)

logger.debug("Configuration loaded — TTS provider: %s", TTS_PROVIDER)
