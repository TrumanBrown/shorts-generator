import os
from moviepy.config import change_settings
from moviepy.editor import TextClip, CompositeVideoClip

# Configure ImageMagick path if provided (needed on Windows)
magick_path = os.getenv("IMAGEMAGICK_BINARY")
if magick_path:
    change_settings({"IMAGEMAGICK_BINARY": magick_path})


def styled_subtitle(text, duration, word_timings=None):
    timings = word_timings or []
    fontsize = 60
    # Default to Windows bold Arial if available; otherwise fall back to a common Linux font
    default_font = "C:\\Windows\\Fonts\\arialbd.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = os.getenv("SUBTITLE_FONT_PATH", default_font)

    if not timings:
        caption = (
            TextClip(
                txt=text,
                fontsize=fontsize,
                font=font,
                color="yellow",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(900, None),
            )
            .set_duration(duration)
            .set_position(("center", "bottom"))
            .margin(bottom=60)
        )
        return caption

    word_clips = []
    for word_info in timings:
        word = word_info["word"]
        start_time = word_info["start"] / 1000
        word_duration = word_info["duration"] / 1000

        word_clip = (
            TextClip(
                txt=word,
                fontsize=fontsize,
                font=font,
                color="yellow",
                stroke_color="black",
                stroke_width=3,
            )
            .set_start(start_time)
            .set_duration(word_duration)
            .set_position(("center", "bottom"))
        )
        word_clips.append(word_clip)

    subtitle_clip = CompositeVideoClip(word_clips).set_duration(duration).margin(bottom=60)
    return subtitle_clip
