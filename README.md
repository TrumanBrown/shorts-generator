# Anime Shorts Generator

Automated pipeline that creates 60-second anime "Did You Know?" vertical videos from scratch — generates a trivia script with GPT-4, fetches matching images, synthesizes narration, overlays word-level subtitles, and exports a ready-to-post `.mp4`.

## How It Works

```
main.py (CLI)
  └─ pipeline.py
       ├─ 1. script_generator.py  →  Azure OpenAI GPT-4 writes a trivia script
       ├─ 2. script_generator.py  →  Parses script into (image_prompt, narration) pairs
       ├─ 3. image_handler.py     →  Google Custom Search fetches + validates images
       ├─ 4. audio_generator.py   →  Azure TTS or ElevenLabs generates voiceover
       ├─ 5. subtitles.py         →  MoviePy renders word-level subtitle overlays
       └─ 6. video_renderer.py    →  Composes 1080×1080 video @ 24fps → output/final_video.mp4
```

Each run clears `input/images/` and `audio/` to avoid stale assets.

## Project Structure

```
├── main.py                  # CLI entry point (--no-audio, --skip-script)
├── main_with_audio.py       # Convenience: always renders with audio
├── main_no_audio.py         # Convenience: always renders without audio
├── requirements.txt
├── .env                     # Credentials (not committed)
├── .python-version          # 3.11
│
├── src/
│   ├── __init__.py
│   ├── config.py            # All env vars, paths, and constants
│   ├── pipeline.py          # Orchestration + CLI argument parsing
│   ├── script_generator.py  # GPT-4 script generation + parsing
│   ├── image_handler.py     # Google CSE image search + download
│   ├── audio_generator.py   # Azure TTS / ElevenLabs TTS
│   ├── subtitles.py         # Static or word-level subtitle clips
│   └── video_renderer.py    # MoviePy segment composition + export
│
├── input/
│   ├── script.txt           # Generated script (gitignored)
│   └── images/              # Downloaded images (gitignored)
├── audio/                   # TTS audio files (gitignored)
└── output/
    └── final_video.mp4      # Final rendered video (gitignored)
```

## Requirements

### System dependencies

| Tool | Purpose | Install |
|------|---------|---------|
| **Python 3.11** | Runtime (Pillow pin requires ≤3.12) | `sudo apt install python3.11` or [python.org](https://www.python.org/downloads/) |
| **ffmpeg** | Video encoding | `sudo apt install ffmpeg` / [ffmpeg.org](https://ffmpeg.org/download.html) |
| **ImageMagick** | Subtitle text rendering (MoviePy) | `sudo apt install imagemagick` / [imagemagick.org](https://imagemagick.org/script/download.php) |

### API accounts

| Service | What it does | Required |
|---------|-------------|----------|
| **Azure OpenAI** (GPT-4 deployment) | Generates the trivia script | Yes |
| **Azure Speech** | Text-to-speech with word-level timings | Yes (default TTS) |
| **Google Custom Search** | Fetches anime images | Yes |
| **ElevenLabs** | Alternative TTS (no word timings) | Optional |

## Setup

### 1. Clone and enter the repo

```bash
git clone git@github.com:TrumanBrown/shorts-generator.git
cd shorts-generator
```

### 2. Create a virtual environment

**Linux / macOS:**

```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> If `Pillow` fails to build, your Python version is likely too new. Use 3.11 or 3.12.

### 4. Verify system tools

```bash
ffmpeg -version       # should print version info
convert --version     # ImageMagick (Linux) — or `magick --version` on Windows
```

### 5. Create `.env`

Copy this template into a `.env` file in the project root:

```env
# --- Google Image Search ---
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_CSE_ID="your-custom-search-engine-id"

# --- Azure TTS ---
AZURE_TTS_KEY="your-azure-speech-key"
AZURE_TTS_REGION="westus"

# --- Azure OpenAI (script generation) ---
AZURE_OPENAI_API_KEY="your-azure-openai-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"

# --- TTS Provider (azure or elevenlabs) ---
TTS_PROVIDER="azure"

# --- ElevenLabs (optional, only if TTS_PROVIDER=elevenlabs) ---
# ELEVENLABS_API_KEY="your-elevenlabs-key"
# ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"

# --- Optional overrides ---
# LOG_LEVEL="DEBUG"                          # Default: INFO
# IMAGEMAGICK_BINARY="/usr/bin/convert"      # Override ImageMagick path
# SUBTITLE_FONT_PATH="/path/to/font.ttf"    # Override subtitle font
```

## Usage

### Generate a video (default — with audio)

```bash
python main.py
```

### CLI flags

| Flag | Effect |
|------|--------|
| `--no-audio` | Skip TTS, render silent video with static subtitles |
| `--skip-script` | Reuse existing `input/script.txt` instead of generating a new one |

```bash
# Silent video (no TTS)
python main.py --no-audio

# Reuse an existing script (edit input/script.txt first if desired)
python main.py --skip-script

# Combine both
python main.py --no-audio --skip-script
```

### Convenience entry points

```bash
python main_with_audio.py    # Same as: python main.py
python main_no_audio.py      # Same as: python main.py --no-audio
```

## Script Format

The generated (or hand-edited) script at `input/script.txt` uses alternating lines:

```
[naruto shikamaru playing shogi]
Did you know Shikamaru's tactics were inspired by a real chess grandmaster?

[naruto shikamaru shadow possession jutsu]
Even his Shadow Possession Jutsu mirrors how chess masters anticipate opponents.
```

- **Odd lines** — `[image search prompt]` used to find images via Google CSE
- **Even lines** — Narration text sent to TTS and rendered as subtitles

The file must have an even number of non-empty lines.

## Output

| Path | Contents |
|------|----------|
| `output/final_video.mp4` | Final 1080×1080 vertical video at 24fps |
| `input/script.txt` | Last generated script |
| `input/images/step1.jpg` … | Downloaded images for each segment |
| `audio/step1.mp3` … | TTS audio for each segment (when audio enabled) |

## Configuration Reference

All configuration lives in `src/config.py`. Key constants:

| Constant | Default | Purpose |
|----------|---------|---------|
| `VIDEO_WIDTH` / `VIDEO_HEIGHT` | 1080 × 1080 | Output resolution |
| `VIDEO_FPS` | 24 | Frame rate |
| `DEFAULT_CLIP_DURATION` | 3.5s | Clip length when audio is disabled |
| `FADE_DURATION` | 0.5s | Fade-in/out per segment |
| `SUBTITLE_FONT_SIZE` | 60 | Subtitle text size |
| `SUBTITLE_COLOR` | yellow | Subtitle text color |
| `TTS_PROVIDER` | azure | `azure` or `elevenlabs` |
| `LOG_LEVEL` | INFO | Python logging level |

## Logging

The pipeline uses Python's `logging` module. Set `LOG_LEVEL` in `.env` to control verbosity:

```env
LOG_LEVEL="DEBUG"    # DEBUG, INFO, WARNING, ERROR
```

Logs include timestamps and module names:

```
2026-04-07 12:00:00 [INFO] src.pipeline: Starting pipeline (audio=True, regenerate_script=True)
2026-04-07 12:00:01 [INFO] src.script_generator: Generating anime script via Azure OpenAI (gpt-4)…
2026-04-07 12:00:05 [INFO] src.image_handler: Searching images for 'naruto shikamaru playing shogi' (max 5 results)
```

## Windows Notes

- Install ImageMagick 7 (Q16) and check "Add to system path" + "Install legacy utilities"
- If MoviePy can't find ImageMagick, set `IMAGEMAGICK_BINARY` in `.env`:
  ```
  IMAGEMAGICK_BINARY="C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
  ```
- If subtitles fail with a font error, set `SUBTITLE_FONT_PATH`:
  ```
  SUBTITLE_FONT_PATH="C:\Windows\Fonts\arialbd.ttf"
  ```
