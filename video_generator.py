import os
import requests
from dotenv import load_dotenv
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from PIL import Image
import shutil
import re

# Load environment variables
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
        "You are a scriptwriter for short-form anime trivia content. Your job is to write 60-second 'Did You Know?' style scripts for fans of ONE specific anime (Naruto, One Piece, or Attack on Titan). "
        "Each script should focus on one obscure, surprising, or strange fact — not a summary or moral. "
        "Structure the script as ~10–12 alternating lines: one image tag in square brackets, followed by one narration sentence. "
        "Each [image description] should be specific enough to help find a relevant image, but not so specific it becomes too rare or obscure. "
        "Use terms like character names, key objects, expressions, or settings (e.g., [one piece young luffy with dagger], [attack on titan eren touching basement key]). "
        "Avoid overly long tags or deep cut scene references. Keep tags searchable. "
        "No 'Narrator:' labels. No summaries, no morals, no intros or outros — only focused trivia with matching visual tags."
    )

    user_prompt = (
        "Write a short anime 'Did You Know?' video script focused on one obscure or surprising fact from Naruto, One Piece, or Attack on Titan. "
        "Pick just one fact and expand on it using multiple angles. "
        "Structure the script as alternating lines of [image search prompt] and a short narration sentence. "
        "Each image prompt should include character names, context, or actions — but stay reasonably general and searchable (e.g., [one piece luffy showing scar], [naruto young sasuke with family], [attack on titan zeke yelling]). "
        "Do not use vague prompts like [anime scene] or [battle shot], but also don’t go too narrow like [one piece episode 4 scene with dagger at timestamp]. "
        "Keep it 10–12 lines total, no intro/outro."
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
    for prefix in ["Scene:", "Final shot:", "Opening:", "Shot:"]:
        if raw.lower().startswith(prefix.lower()):
            return raw[len(prefix):].strip()
    return raw

def parse_script(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    if len(lines) % 2 != 0:
        raise ValueError("Script should have even number of lines.")
    return [(clean_prompt(lines[i]), lines[i+1]) for i in range(0, len(lines), 2)]

def fetch_image_url(query, max_attempts=5):
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CSE_ID,
        "q": query,
        "searchType": "image",
        "num": max_attempts,
        "safe": "active"
    }
    url = "https://www.googleapis.com/customsearch/v1"
    try:
        response = requests.get(url, params=params)
        items = response.json().get("items", [])
        for i, item in enumerate(items):
            link = item.get("link")
            if link:
                try:
                    r = requests.get(link, timeout=10)
                    if r.headers.get("Content-Type", "").startswith("image"):
                        return link
                except:
                    continue
        raise ValueError("No usable image found")
    except Exception as e:
        print(f"Image fetch failed: {e}")
        return fetch_image_url("anime background")

def download_image(image_url, save_path, original_prompt=None, attempt=1, max_attempts=5):
    try:
        r = requests.get(image_url, timeout=10)
        if not r.headers.get("Content-Type", "").startswith("image"):
            raise ValueError("Invalid image content")
        with open(save_path, 'wb') as f:
            f.write(r.content)
        print(f"Downloaded image to {save_path}")
    except Exception as e:
        print(f"Download failed (attempt {attempt}): {e}")
        if original_prompt and attempt < max_attempts:
            next_url = fetch_image_url(original_prompt, max_attempts=5 + attempt)
            download_image(next_url, save_path, original_prompt, attempt + 1, max_attempts)
        else:
            fallback_url = fetch_image_url("anime background")
            download_image(fallback_url, save_path)

def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except:
        return False

def generate_tts(text, path, key, region, voice="en-US-BrianMultilingualNeural"):
    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_synthesis_voice_name = voice
    out_cfg = speechsdk.audio.AudioOutputConfig(filename=path)
    synth = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=out_cfg)
    result = synth.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise Exception("TTS failed")
    print(f"Generated TTS: {path}")

def load_clips(segments):
    clips = []
    for idx, (prompt, text) in enumerate(segments, 1):
        image_path = os.path.join(IMAGE_DIR, f"step{idx}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"step{idx}.mp3")

        if not os.path.exists(audio_path):
            generate_tts(text, audio_path, AZURE_TTS_KEY, AZURE_TTS_REGION)

        if not os.path.exists(image_path) or not is_valid_image(image_path):
            url = fetch_image_url(prompt)
            download_image(url, image_path, original_prompt=prompt)


        audio = AudioFileClip(audio_path)
        img = ImageClip(image_path).set_audio(audio).set_duration(audio.duration)
        img = img.resize(width=1080) if img.w > img.h else img.resize(height=1080)
        background = ColorClip((1080, 1080), color=(0, 0, 0), duration=audio.duration)
        img = img.set_position("center")
        base = CompositeVideoClip([background, img]).fadein(0.5).fadeout(0.5)

        subtitle = TextClip(text, fontsize=40, color='white', font='Arial-Bold', size=img.size, method='caption')
        subtitle = subtitle.set_position("bottom").set_duration(audio.duration)

        final = CompositeVideoClip([base, subtitle]).set_audio(audio)
        clips.append(final)
    return clips

def main():
    clean_generated_dirs()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    generate_anime_script(SCRIPT_PATH)
    segments = parse_script(SCRIPT_PATH)
    clips = load_clips(segments)
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(OUTPUT_PATH, fps=24)

if __name__ == "__main__":
    main()
