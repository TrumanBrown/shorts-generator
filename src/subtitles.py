from moviepy.editor import TextClip, CompositeVideoClip


def styled_subtitle(text, duration, word_timings=None):
    timings = word_timings or []
    fontsize = 60
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

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
