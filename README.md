# Anime Shorts Generator

This project automates the creation of 60-second anime "fun fact" or "did you know" videos. It combines a tagged script format with pre-generated audio and automatically downloaded images using the Google Custom Search API. The output is a ready-to-publish video suitable for platforms like YouTube Shorts or TikTok.

## Features

- Parses a tagged script with `[image prompt]` markers
- Fetches relevant images via Google Custom Search
- Combines images with pre-recorded TTS audio
- Outputs a final `.mp4` video using MoviePy

## Requirements

- Python 3.8 or newer
- ffmpeg installed and accessible in your system PATH
- Google API key and Custom Search Engine (CSE) ID with image search enabled

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/trumanbrown/anime-shorts-generator.git
cd anime-shorts-generator
```

### 2. Create and activate a virtual environment

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Ensure `ffmpeg` is installed. You can download it from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html).

## API Configuration

Open `video_generator.py` and update the following variables with your actual credentials:

```python
GOOGLE_API_KEY = "your-google-api-key"
CSE_ID = "your-custom-search-engine-id"
```

To obtain these:

1. Create a Custom Search Engine at [https://programmablesearchengine.google.com/](https://programmablesearchengine.google.com/)
2. Enable "Search the entire web" and "Image search"
3. Generate an API key in the Google Cloud Console
4. Enable the **Custom Search API** for your project


## Usage

1. Write your script in `input/script.txt` using the following format:

```
[sasuke fighting itachi]
Did you know Sasuke was unaware of the truth behind the Uchiha massacre?

[young sasuke crying]
He didn't learn Itachi’s real motives until years later.
```

2. Place corresponding audio files (`step1.mp3`, `step2.mp3`, etc.) in the `audio/` folder.

3. Run the generator:

```bash
python video_generator.py
```

The script will:

- Read your script
- Fetch one image per `[prompt]`
- Combine each image with its corresponding audio
- Concatenate clips into `output/final_video.mp4`


test