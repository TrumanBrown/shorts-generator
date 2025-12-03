import argparse
import os
import shutil
from src.config import SCRIPT_PATH, OUTPUT_PATH, IMAGE_DIR, AUDIO_DIR
from src.script_generator import generate_anime_script, parse_script
from src.video_renderer import create_video


def clean_generated_dirs():
    """Clear generated asset folders to avoid stale media."""
    for path in (IMAGE_DIR, AUDIO_DIR):
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Cleared existing directory: {path}")
        os.makedirs(path, exist_ok=True)


def run_pipeline(use_audio=True, regenerate_script=True):
    """Generate script, fetch assets, and render the final video."""
    clean_generated_dirs()
    if regenerate_script:
        generate_anime_script()
    segments = parse_script(SCRIPT_PATH)
    create_video(segments, OUTPUT_PATH, use_audio=use_audio)


def cli():
    parser = argparse.ArgumentParser(description="Generate an anime short video.")
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Skip TTS generation and render without narration.",
    )
    parser.add_argument(
        "--skip-script",
        action="store_true",
        help="Reuse the existing script at the configured path instead of generating a new one.",
    )
    # action="store_true" -> defaults to False; becomes True only when the flag is present
    args = parser.parse_args()
    # use_audio defaults to True unless --no-audio is passed
    # regenerate_script defaults to True unless --skip-script is passed
    run_pipeline(use_audio=not args.no_audio, regenerate_script=not args.skip_script)


if __name__ == "__main__":
    cli()
