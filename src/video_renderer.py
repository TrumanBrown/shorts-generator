"""Video composition and export.

Loads images, generates audio, overlays subtitles, and concatenates all
segments into a single vertical short video.
"""

import logging
from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)

from src.audio_generator import generate_tts
from src.config import (
    AUDIO_DIR,
    DEFAULT_CLIP_DURATION,
    FADE_DURATION,
    IMAGE_DIR,
    VIDEO_FPS,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from src.image_handler import download_image, fetch_image_url, is_valid_image
from src.subtitles import styled_subtitle

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Clip assembly
# ---------------------------------------------------------------------------

def _build_segment_clip(
    idx: int,
    prompt: str,
    narration: str,
    use_audio: bool,
) -> CompositeVideoClip:
    """Build a single video segment from an image prompt and narration text.

    Steps:
        1. Generate TTS audio (if enabled) and capture word timings.
        2. Fetch / validate the image for this segment.
        3. Compose the image on a black background with fade transitions.
        4. Overlay styled subtitles.
    """
    image_path = IMAGE_DIR / f"step{idx}.jpg"
    audio_path = AUDIO_DIR / f"step{idx}.mp3"

    # --- Audio ---
    word_timings: list[dict] = []
    audio = None
    duration = DEFAULT_CLIP_DURATION

    if use_audio:
        word_timings = generate_tts(narration, str(audio_path)) or []
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

    # --- Image ---
    if not image_path.exists() or not is_valid_image(image_path):
        url = fetch_image_url(prompt)
        download_image(url, image_path, original_prompt=prompt)

    img = ImageClip(str(image_path)).set_duration(duration)
    if audio:
        img = img.set_audio(audio)

    # Scale to fit the square canvas while preserving aspect ratio.
    if img.w > img.h:
        img = img.resize(width=VIDEO_WIDTH)
    else:
        img = img.resize(height=VIDEO_HEIGHT)

    background = ColorClip(
        (VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0), duration=duration
    )
    base = (
        CompositeVideoClip([background, img.set_position("center")])
        .fadein(FADE_DURATION)
        .fadeout(FADE_DURATION)
    )

    # --- Subtitles ---
    subtitle = styled_subtitle(narration, duration, word_timings)
    final = CompositeVideoClip([base, subtitle])

    if audio:
        final = final.set_audio(audio)

    logger.info(
        "Segment %d ready (%.1fs) — prompt='%s'", idx, duration, prompt[:50]
    )
    return final


def _load_all_clips(
    segments: list[tuple[str, str]], use_audio: bool
) -> list[CompositeVideoClip]:
    """Build a clip for every segment in the script."""
    return [
        _build_segment_clip(idx, prompt, narration, use_audio)
        for idx, (prompt, narration) in enumerate(segments, 1)
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_video(
    segments: list[tuple[str, str]],
    output_path: str | Path,
    use_audio: bool = True,
) -> Path:
    """Render all *segments* into a single video file at *output_path*.

    Returns the output path for convenience.
    """
    logger.info(
        "Rendering %d segments (audio=%s) → %s",
        len(segments), use_audio, output_path,
    )
    clips = _load_all_clips(segments, use_audio)
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(str(output_path), fps=VIDEO_FPS)
    logger.info("Video saved to %s", output_path)
    return Path(output_path)
