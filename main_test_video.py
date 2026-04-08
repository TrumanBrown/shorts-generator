"""Offline video test — no API calls.

Uses the existing script and images on disk to test video rendering,
image stitching, and subtitle display. Skips script generation, image
fetching, and TTS entirely.

Requires:
    - input/script.txt (existing script file)
    - input/images/step1.jpg … stepN.jpg (pre-downloaded images)
"""

import logging
import sys
from pathlib import Path

from src.config import IMAGE_DIR, OUTPUT_PATH, SCRIPT_PATH, VIDEO_FPS
from src.script_generator import parse_script
from src.subtitles import styled_subtitle
from src.config import (
    DEFAULT_CLIP_DURATION,
    FADE_DURATION,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    # --- Validate assets exist ---
    if not SCRIPT_PATH.exists():
        logger.error("No script found at %s — run a full pipeline first.", SCRIPT_PATH)
        sys.exit(1)

    segments = parse_script(SCRIPT_PATH)

    missing = []
    for idx in range(1, len(segments) + 1):
        img = IMAGE_DIR / f"step{idx}.jpg"
        if not img.exists():
            missing.append(str(img))
    if missing:
        logger.error("Missing images: %s", ", ".join(missing))
        sys.exit(1)

    logger.info("Found %d segments with matching images — rendering video…", len(segments))

    # --- Lazy-import MoviePy only after validation passes ---
    from moviepy.editor import (
        ColorClip,
        CompositeVideoClip,
        ImageClip,
        concatenate_videoclips,
    )

    clips = []
    for idx, (prompt, narration) in enumerate(segments, 1):
        image_path = IMAGE_DIR / f"step{idx}.jpg"
        duration = DEFAULT_CLIP_DURATION

        img = ImageClip(str(image_path)).set_duration(duration)
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

        subtitle = styled_subtitle(narration, duration)
        final = CompositeVideoClip([base, subtitle])
        clips.append(final)

        logger.info("Segment %d/%d ready — %s", idx, len(segments), prompt[:50])

    video = concatenate_videoclips(clips, method="compose")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(str(OUTPUT_PATH), fps=VIDEO_FPS)
    logger.info("Test video saved to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
