from src.script_generator import generate_anime_script, parse_script
from src.config import SCRIPT_PATH, OUTPUT_PATH
from src.video_renderer import create_video
import shutil
import os

def clean_generated_dirs():
    for path in ["input/images", "audio"]:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Cleared existing directory: {path}")
        os.makedirs(path, exist_ok=True)

def main():
    clean_generated_dirs()
    generate_anime_script()
    segments = parse_script(SCRIPT_PATH)
    create_video(segments, OUTPUT_PATH, use_audio=True)

if __name__ == "__main__":
    main()
