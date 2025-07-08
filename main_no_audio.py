from src.script_generator import generate_anime_script, parse_script
from src.config import SCRIPT_PATH, OUTPUT_PATH
from src.video_renderer import create_video

def main():
    generate_anime_script()
    segments = parse_script(SCRIPT_PATH)
    create_video(segments, OUTPUT_PATH, use_audio=False)

if __name__ == "__main__":
    main()
