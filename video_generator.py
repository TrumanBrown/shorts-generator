import os
import requests
from dotenv import load_dotenv
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import azure.cognitiveservices.speech as speechsdk
import openai

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")
AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY")
AZURE_TTS_REGION = os.getenv("AZURE_TTS_REGION")

# Configs
SCRIPT_PATH = "input/script.txt"
IMAGE_DIR = "input/images"
AUDIO_DIR = "audio"
OUTPUT_PATH = "output/final_video.mp4"

def parse_script(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) % 2 != 0:
        raise ValueError(f"Expected even number of lines in script.txt, but got {len(lines)}")

    segments = []
    for i in range(0, len(lines), 2):
        prompt = lines[i].strip("[]")
        text = lines[i+1]
        segments.append((prompt, text))
    return segments

def fetch_image_url(query):
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CSE_ID,
        "q": query,
        "searchType": "image",
        "num": 1,
        "safe": "active"
    }
    url = "https://www.googleapis.com/customsearch/v1"
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Google CSE request failed: {response.status_code} - {response.text}")

    data = response.json()
    if "items" not in data or not data["items"]:
        raise Exception(f"No image results found for: {query}")

    return data["items"][0]["link"]


def download_image(image_url, save_path):
    try:
        img_data = requests.get(image_url, timeout=10).content
        with open(save_path, 'wb') as f:
            f.write(img_data)
        print(f"Downloaded image to {save_path}")
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")

def generate_tts(text, output_path, key, region, voice="en-US-BrianMultilingualNeural"):
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise Exception(f"TTS failed: {result.reason}")
    else:
        print(f"Generated TTS: {output_path}")

def load_clips(segments):
    clips = []
    for idx, (prompt, text) in enumerate(segments, start=1):
        image_path = os.path.join(IMAGE_DIR, f"step{idx}.jpg")
        audio_path = os.path.join(AUDIO_DIR, f"step{idx}.mp3")

        if not os.path.exists(audio_path):
            print(f"Generating TTS for line {idx}: {text}")
            generate_tts(text, audio_path, AZURE_TTS_KEY, AZURE_TTS_REGION)

        if not os.path.exists(image_path):
            print(f"Searching and downloading image for: {prompt}")
            image_url = fetch_image_url(prompt)
            download_image(image_url, image_path)

        audio = AudioFileClip(audio_path)
        image = ImageClip(image_path).set_duration(audio.duration).set_audio(audio)
        image = image.resize(height=720).fadein(0.5).fadeout(0.5)
        clips.append(image)
    return clips

def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    segments = parse_script(SCRIPT_PATH)
    clips = load_clips(segments)
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(OUTPUT_PATH, fps=24)

if __name__ == "__main__":
    main()
