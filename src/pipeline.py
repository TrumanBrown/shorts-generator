"""Pipeline orchestration and CLI entry point.

Coordinates the end-to-end flow: clean workspace → generate script →
parse segments → render video.  Also exposes the ``cli()`` function used
by ``main.py``.
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

from src.config import AUDIO_DIR, IMAGE_DIR, OUTPUT_PATH, SCRIPT_PATH
from src.script_generator import generate_anime_script, parse_script
from src.video_renderer import create_video

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------

def _clean_generated_dirs() -> None:
    """Remove and recreate asset directories to avoid stale media."""
    for directory in (IMAGE_DIR, AUDIO_DIR):
        if directory.exists():
            shutil.rmtree(directory)
            logger.info("Cleared %s", directory)
        directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(*, use_audio: bool = True, regenerate_script: bool = True) -> Path:
    """Execute the full video generation pipeline.

    Args:
        use_audio: When False, skip TTS and render a silent video.
        regenerate_script: When False, reuse the existing script file.

    Returns:
        Path to the rendered video.
    """
    logger.info(
        "Starting pipeline (audio=%s, regenerate_script=%s)",
        use_audio, regenerate_script,
    )

    _clean_generated_dirs()

    if regenerate_script:
        generate_anime_script()
    else:
        if not SCRIPT_PATH.exists():
            logger.error("--skip-script used but %s does not exist", SCRIPT_PATH)
            sys.exit(1)
        logger.info("Reusing existing script at %s", SCRIPT_PATH)

    segments = parse_script(SCRIPT_PATH)
    output = create_video(segments, OUTPUT_PATH, use_audio=use_audio)

    logger.info("Pipeline complete → %s", output)
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cli() -> None:
    """Parse command-line arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate an anime 'Did You Know?' short video.",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Skip TTS generation and render without narration.",
    )
    parser.add_argument(
        "--skip-script",
        action="store_true",
        help="Reuse the existing script instead of generating a new one.",
    )
    args = parser.parse_args()

    run_pipeline(
        use_audio=not args.no_audio,
        regenerate_script=not args.skip_script,
    )
