import os
import requests
from dotenv import load_dotenv
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
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
            print(f"🧹 Cleared existing directory: {path}")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_anime_script(output_path="input/script.txt"):
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, api_version, azure_endpoint, deployment]):
        raise EnvironmentError("❌ Missing required Azure OpenAI environment variables.")

    print("✅ Loaded OpenAI config:")
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
        "Each script should focus on one surprising, strange, dark, or obscure fact — not a summary or inspirational story arc. "
        "Do not include life lessons or moral reflections. No summaries or 'he taught us...' or 'this shows...' type conclusions. "
        "Structure the script as ~12 alternating lines: one image tag in square brackets, followed by one short narration sentence. "
        "Image tags must begin with the anime name (e.g., [naruto sakura punching], [one piece gear 5 luffy], [attack on titan zeke scream]). "
        "Narration must be direct, punchy, and surprising — include obscure trivia, creator easter eggs, character quirks, or fan debates. "
        "No 'Narrator:' labels. No intros, no outros, no recaps, no emotional sendoffs — just fun, sharp facts."
    )

    user_prompt = (
        "Write a 60-second anime 'Did You Know?' script about one weird, dark, or obscure fact from Naruto, One Piece, or Attack on Titan. "
        "Use only one anime for the entire script. Avoid summaries or morals — focus only on a surprising or lesser-known fact. "
        "Use [image prompt] followed by one-sentence narration, alternating for ~12 lines total."
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

    print(f"✅ Generated anime script to {output_path}")

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
        raise ValueError(f"Expected even number of lines in script.txt, but got {len(lines)}")

    segments = []
    for i in range(0, len(lines), 2):
        prompt = clean_prompt(lines[i])
        text = lines[i+1]
        segments.append((prompt, text))
    return segments

def fetch_image_url(query, max_attempts=5):
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
            raise ValueError("No image results found")

        for i, item in enumerate(data["items"]):
            image_url = item.get("link")
            if image_url:
                print(f"✅ Found image (index {i}): {image_url}")
                return image_url

        raise ValueError("No usable image links found")

    except Exception as e:
        print(f"❌ Failed to find image for '{query}': {e}")
        return fetch_image_url("anime background")

def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, timeout=10)
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL did not return image content: {content_type}")
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded image to {save_path}")
    except Exception as e:
        print(f"❌ Failed to download {image_url}: {e}")
        fallback_url = fetch_image_url("anime background")
        download_image(fallback_url, save_path)

def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"❌ Invalid image at {path}: {e}")
        return False

def generate_tts(text, output_path, key, region, voice="en-US-BrianMultilingualNeural"):
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise Exception(f"TTS failed: {result.reason}")
    else:
        print(f"✅ Generated TTS: {output_path}")

def load_clips(segments):
    clips = []
    for idx, (prompt, text) in enumerate(segments, start=1):
        image_path = os.path.join(IMAGE_DIR, f"step{idx}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"step{idx}.mp3")

        if not os.path.exists(audio_path):
            print(f"🎙️ Generating TTS for line {idx}: {text}")
            generate_tts(text, audio_path, AZURE_TTS_KEY, AZURE_TTS_REGION)

        if not os.path.exists(image_path) or not is_valid_image(image_path):
            print(f"🔍 Searching and downloading image for: {prompt}")
            image_url = fetch_image_url(prompt)
            download_image(image_url, image_path)

        if not is_valid_image(image_path):
            print(f"⚠️ Image still invalid, using fallback.")
            fallback_url = fetch_image_url("anime background")
            download_image(fallback_url, image_path)

        audio = AudioFileClip(audio_path)
        image = ImageClip(image_path).set_duration(audio.duration).set_audio(audio)
        image = image.resize(height=720).fadein(0.5).fadeout(0.5)

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
