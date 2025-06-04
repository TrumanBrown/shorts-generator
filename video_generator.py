import os
import requests
from dotenv import load_dotenv
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from PIL import Image
import shutil
import re

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")
AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY")
AZURE_TTS_REGION = os.getenv("AZURE_TTS_REGION")

SCRIPT_PATH = "input/script.txt"
IMAGE_DIR = "input/images"
AUDIO_DIR = "audio"
OUTPUT_PATH = "output/final_video.mp4"

def clean_generated_dirs():
    for path in [IMAGE_DIR, AUDIO_DIR]:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Cleared existing directory: {path}")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_anime_script(output_path="input/script.txt"):
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, api_version, azure_endpoint, deployment]):
        raise EnvironmentError("Missing required Azure OpenAI environment variables.")

    print("Loaded OpenAI config:")
    print("  endpoint:", azure_endpoint)
    print("  version:", api_version)
    print("  model:", deployment)

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint
    )

    system_prompt = (
        "You are a scriptwriter for short-form anime trivia content. Focus each script on one obscure or surprising fact from Naruto, One Piece, or Attack on Titan."
    )

    user_prompt = (
        "Write a short anime 'Did You Know?' video script. Use alternating lines of [image prompt] and one-sentence narration. Keep prompts specific but searchable."
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=deployment
    )

    script_text = response.choices[0].message.content.strip()
    script_text = re.sub(r"(\[[^\]]+\])\s+(?!\n)", r"\1\n", script_text)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script_text)

    print(f"Generated anime script to {output_path}")

def clean_prompt(raw):
    raw = raw.strip("[]")
    return raw

def parse_script(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) % 2 != 0:
        raise ValueError(f"Expected even number of lines in script.txt, but got {len(lines)}")

    return [(clean_prompt(lines[i]), lines[i+1]) for i in range(0, len(lines), 2)]

def fetch_image_urls(query, max_attempts=5):
    try:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": CSE_ID,
            "q": query,
            "searchType": "image",
            "num": max_attempts,
            "safe": "active"
        }
        url = "https://www.googleapis.com/customsearch/v1"
        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data or not data["items"]:
            return []

        return [item.get("link") for item in data["items"] if item.get("link")]
    except Exception as e:
        print(f"Image search error for '{query}': {e}")
        return []

def download_image(urls, save_path):
    for image_url in urls:
        try:
            response = requests.get(image_url, timeout=10)
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                continue
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded image to {save_path}")
            return True
        except Exception as e:
            print(f"Failed to download {image_url}: {e}")
    return False

def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except:
        return False

def generate_tts(text, output_path, key, region, voice="en-US-BrianMultilingualNeural"):
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise Exception(f"TTS failed: {result.reason}")

def load_clips(segments):
    clips = []
    for idx, (prompt, text) in enumerate(segments, start=1):
        image_path = os.path.join(IMAGE_DIR, f"step{idx}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"step{idx}.mp3")

        if not os.path.exists(audio_path):
            generate_tts(text, audio_path, AZURE_TTS_KEY, AZURE_TTS_REGION)

        if not os.path.exists(image_path) or not is_valid_image(image_path):
            image_urls = fetch_image_urls(prompt)
            success = download_image(image_urls, image_path)
            if not success:
                fallback_urls = fetch_image_urls("anime background")
                download_image(fallback_urls, image_path)

        audio = AudioFileClip(audio_path)
        image = ImageClip(image_path).set_audio(audio).set_duration(audio.duration)
        image = image.resize(width=1080) if image.w > image.h else image.resize(height=1080)

        background = ColorClip(size=(1080, 1080), color=(0, 0, 0), duration=audio.duration)
        image = image.set_position(("center", "center"))
        image = CompositeVideoClip([background, image]).fadein(0.5).fadeout(0.5)

        subtitle = TextClip(text, fontsize=40, color='white', font='Arial-Bold', size=image.size, method='caption')
        subtitle = subtitle.set_position(("center", "bottom")).set_duration(audio.duration)

        composite = CompositeVideoClip([image, subtitle]).set_duration(audio.duration).set_audio(audio)
        clips.append(composite)
    return clips

def main():
    clean_generated_dirs()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    generate_anime_script(SCRIPT_PATH)
    segments = parse_script(SCRIPT_PATH)
    clips = load_clips(segments)
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(OUTPUT_PATH, fps=24)

if __name__ == "__main__":
    main()
