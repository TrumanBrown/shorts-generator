"""Subtitle clip generation for MoviePy.

Creates styled subtitle overlays — either a single static caption when no
word timings are available, or individual per-word clips synchronised to
TTS audio boundaries for a karaoke-style effect.
"""

import logging

from moviepy.config import change_settings
from moviepy.editor import CompositeVideoClip, TextClip

from src.config import (
    IMAGEMAGICK_BINARY,
    SUBTITLE_BOTTOM_MARGIN,
    SUBTITLE_CAPTION_WIDTH,
    SUBTITLE_COLOR,
    SUBTITLE_FONT_PATH,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_STROKE_COLOR,
    SUBTITLE_STROKE_WIDTH,
)

logger = logging.getLogger(__name__)

# Configure ImageMagick path if provided (needed on Windows).
if IMAGEMAGICK_BINARY:
    change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})


def styled_subtitle(
    text: str,
    duration: float,
    word_timings: list[dict] | None = None,
) -> TextClip | CompositeVideoClip:
    """Build a subtitle clip for a single video segment.

    When *word_timings* is provided (from Azure TTS), each word is rendered
    as an independent clip timed to its spoken interval.  Otherwise a single
    static caption is used for the entire *duration*.
    """
    timings = word_timings or []

    if not timings:
        return _static_caption(text, duration)
    return _word_level_caption(timings, duration)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _static_caption(text: str, duration: float) -> TextClip:
    """Render a single caption spanning the full *duration*."""
    logger.debug("Static subtitle: '%s' (%.1fs)", text[:40], duration)
    return (
        TextClip(
            txt=text,
            fontsize=SUBTITLE_FONT_SIZE,
            font=SUBTITLE_FONT_PATH,
            color=SUBTITLE_COLOR,
            stroke_color=SUBTITLE_STROKE_COLOR,
            stroke_width=SUBTITLE_STROKE_WIDTH,
            method="caption",
            size=(SUBTITLE_CAPTION_WIDTH, None),
        )
        .set_duration(duration)
        .set_position(("center", "bottom"))
        .margin(bottom=SUBTITLE_BOTTOM_MARGIN)
    )


def _word_level_caption(
    timings: list[dict], duration: float
) -> CompositeVideoClip:
    """Render one clip per word, timed to TTS word boundaries."""
    logger.debug("Word-level subtitles: %d words over %.1fs", len(timings), duration)
    word_clips = []
    for info in timings:
        clip = (
            TextClip(
                txt=info["word"],
                fontsize=SUBTITLE_FONT_SIZE,
                font=SUBTITLE_FONT_PATH,
                color=SUBTITLE_COLOR,
                stroke_color=SUBTITLE_STROKE_COLOR,
                stroke_width=SUBTITLE_STROKE_WIDTH,
            )
            .set_start(info["start"] / 1000)   # ms → seconds
            .set_duration(info["duration"] / 1000)
            .set_position(("center", "bottom"))
        )
        word_clips.append(clip)

    return (
        CompositeVideoClip(word_clips)
        .set_duration(duration)
        .margin(bottom=SUBTITLE_BOTTOM_MARGIN)
    )
