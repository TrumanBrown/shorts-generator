# Anime Shorts Generator

This project automates the creation of 60-second anime "Did You Know?" videos, focused on surprising or emotional trivia from a single anime series (Naruto, One Piece, or Attack on Titan). It uses OpenAI to generate a script, Azure TTS for voiceover, Google CSE for images, and MoviePy to output a complete vertical short.

## Features

- Generates a “Did You Know?” script using Azure OpenAI GPT-4
- Focuses on a single anime fact, not general summaries
- Parses [image prompt] tags and pairs them with narration
- Fetches relevant anime imagery using Google Custom Search API
- Converts narration to voice with Azure TTS
- Cleans output folders on every run for consistent results
- Outputs a complete, ready-to-post .mp4 video for YouTube Shorts or TikTok

## Requirements

- Python 3.11 (recommended)
	- This project's dependency pins are not compatible with very new Python versions (e.g. 3.13/3.14), which can cause `pip install -r requirements.txt` to fail while building `Pillow` from source.
- ffmpeg installed and accessible in your system PATH
- ImageMagick installed and on PATH (required by MoviePy for subtitles on Windows)
- Google API key and Custom Search Engine (CSE) ID with image search enabled
- Azure OpenAI resource with a GPT-4 deployment
- Azure Speech service key and region

Optional:

- ElevenLabs account if you want to use `TTS_PROVIDER=elevenlabs`

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/trumanbrown/shorts-generator.git
cd shorts-generator
```

### 2. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you see an error building `Pillow` on Windows, it almost always means your Python version is too new for the pinned dependencies. Recreate the venv with Python 3.11 (above) and retry.

Ensure ffmpeg is installed. You can download it from https://ffmpeg.org/download.html

ImageMagick on Windows (needed for subtitles):
- Download ImageMagick 7 (Q16) from https://imagemagick.org/script/download.php
- During setup, check “Add application directory to your system path” and “Install legacy utilities (convert)”
- Open a new terminal and verify `magick --version` works
- If MoviePy still cannot find it, set the path in `.env` (adjust if your install differs):
  - `IMAGEMAGICK_BINARY="C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"`
- If you hit a missing-font error, set a Windows font in `.env`, e.g. `SUBTITLE_FONT_PATH="C:\\Windows\\Fonts\\arialbd.ttf"`

## Environment Configuration

Create a `.env` file in the root directory and populate it with your credentials:

```
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_CSE_ID="your-custom-search-id"

AZURE_TTS_KEY="your-azure-tts-key"
AZURE_TTS_REGION="your-region"

AZURE_OPENAI_API_KEY="your-openai-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"

# Optional: swap to ElevenLabs TTS
TTS_PROVIDER="azure" # or "elevenlabs"
ELEVENLABS_API_KEY="your-elevenlabs-key"
ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"
```

Notes:
- `TTS_PROVIDER` defaults to `azure` when omitted.
- Scripts are written to `input/script.txt`. Use `--skip-script` to reuse or manually edit that file between runs.
- Each run clears `input/images/` and `audio/` to avoid stale assets.

## Usage

Run the generator (audio enabled by default):

```bash
python main.py
```

Flags:

- `--no-audio`: render without narration or word-level subtitles
- `--skip-script`: reuse the existing script file instead of generating a new one

Other entry points:

- `python main_with_audio.py` forces audio on.
- `python main_no_audio.py` runs with `--no-audio`.

The script will:

- Generate a single-anime script around one surprising or emotional fact
- Fetch 12 images using Google Search
- Generate voiceover using Azure TTS
- Combine all segments into `output/final_video.mp4`

Each run clears the `input/images/` and `audio/` directories to avoid stale content.

## Script Format

Generated scripts follow this format:

```
[zoro holding swords]
Zoro's three-sword style was inspired by a real Japanese swordsman.

[sanji cooking]
Some of Sanji’s recipes are based on meals the author personally enjoys.
```

Each `[tag]` line indicates the image search prompt, followed by a short narration line.

## Output

Final video is saved to `output/final_video.mp4`.

Output paths and cached assets:
- `input/script.txt`: latest generated script (reused with `--skip-script`)
- `input/images/`: downloaded images for the current run
- `audio/`: TTS mp3s (skipped when running with `--no-audio`)

Supports content suitable for YouTube Shorts, TikTok, or Instagram Reels.
