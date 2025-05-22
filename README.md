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

- Python 3.8 or newer
- ffmpeg installed and accessible in your system PATH
- Google API key and Custom Search Engine (CSE) ID with image search enabled
- Azure OpenAI resource with a GPT-4 deployment
- Azure Speech service key and region

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/trumanbrown/anime-shorts-generator.git
cd anime-shorts-generator
```

### 2. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Ensure ffmpeg is installed. You can download it from https://ffmpeg.org/download.html

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
```

## Usage

1. Run the script generator:

```bash
python video_generator.py
```

2. It will automatically:

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

Supports content suitable for YouTube Shorts, TikTok, or Instagram Reels.