import os
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, ColorClip
)
from src.image_handler import is_valid_image, fetch_image_url, download_image
from src.audio_generator import generate_tts
from src.subtitles import styled_subtitle

IMAGE_DIR = "input/images"
AUDIO_DIR = "audio"

def load_clips(segments, use_audio=True):
    clips = []
    for idx, (prompt, text) in enumerate(segments, 1):
        image_path = os.path.join(IMAGE_DIR, f"step{idx}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"step{idx}.mp3")

        # Generate audio only if enabled
        if use_audio and not os.path.exists(audio_path):
            generate_tts(text, audio_path)

        # Always download image if needed
        if not os.path.exists(image_path) or not is_valid_image(image_path):
            url = fetch_image_url(prompt)
            download_image(url, image_path, original_prompt=prompt)

        duration = None
        if use_audio:
            audio = AudioFileClip(audio_path)
            duration = audio.duration
        else:
            duration = 3.5  # default length if no audio

        img = ImageClip(image_path).set_duration(duration)
        if use_audio:
            img = img.set_audio(audio)

        img = img.resize(width=1080) if img.w > img.h else img.resize(height=1080)
        background = ColorClip((1080, 1080), color=(0, 0, 0), duration=duration)
        base = CompositeVideoClip([background, img.set_position("center")]).fadein(0.5).fadeout(0.5)

        subtitle = styled_subtitle(text, duration)
        final = CompositeVideoClip([base, subtitle])
        if use_audio:
            final = final.set_audio(audio)

        clips.append(final)
    return clips

def create_video(segments, output_path, use_audio=True):
    clips = load_clips(segments, use_audio=use_audio)
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=24)
