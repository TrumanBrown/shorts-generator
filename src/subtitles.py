from moviepy.editor import TextClip, CompositeVideoClip

def styled_subtitle(text, duration, word_timings):
    word_clips = []

    fontsize = 60
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

    for word_info in word_timings:
        word = word_info['word']
        start_time = word_info['start'] / 1000
        word_duration = word_info['duration'] / 1000

        word_clip = (
            TextClip(
                txt=word,
                fontsize=fontsize,
                font=font,
                color='yellow',
                stroke_color='black',
                stroke_width=3
                # Removed method='caption' and size
            )
            .set_start(start_time)
            .set_duration(word_duration)
            .set_position(('center', 'bottom'))
        )
        word_clips.append(word_clip)

    subtitle_clip = CompositeVideoClip(word_clips).set_duration(duration).margin(bottom=60)

    return subtitle_clip
