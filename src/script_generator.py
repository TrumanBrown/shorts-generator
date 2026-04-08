"""Script generation and parsing using Azure OpenAI.

Generates a ~60-second 'Did You Know?' anime trivia script, writes it to
disk, and provides a parser that converts the file into (prompt, narration)
segment pairs consumed by the video renderer.
"""

import logging
import re
from pathlib import Path

from openai import AzureOpenAI

from src.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    SCRIPT_PATH,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a scriptwriter for short-form anime trivia content. "
    "Your job is to write 60-second 'Did You Know?' style scripts for fans "
    "of ONE specific anime (Naruto, One Piece, or Attack on Titan). "
    "Each script should focus on one obscure, surprising, or strange fact — "
    "not a summary or moral. "
    "Structure the script as ~10–12 alternating lines: one image tag in "
    "square brackets, followed by one narration sentence. "
    "Each [image description] should be specific enough to help find a "
    "relevant image, but not so specific it becomes too rare or obscure. "
    "Use terms like character names, key objects, expressions, or settings "
    "(e.g., [one piece young luffy with dagger], "
    "[attack on titan eren touching basement key]). "
    "Avoid overly long tags or deep cut scene references. Keep tags searchable. "
    "No 'Narrator:' labels. No summaries, no morals, no intros or outros — "
    "only focused trivia with matching visual tags."
)

USER_PROMPT = (
    "Write a short anime 'Did You Know?' video script focused on one "
    "obscure or surprising fact from Naruto, One Piece, or Attack on Titan. "
    "Pick just one fact and expand on it using multiple angles. "
    "Structure the script as alternating lines of [image search prompt] "
    "and a short narration sentence. "
    "Each image prompt should include character names, context, or actions — "
    "but stay reasonably general and searchable "
    "(e.g., [one piece luffy showing scar], [naruto young sasuke with family], "
    "[attack on titan zeke yelling]). "
    "Do not use vague prompts like [anime scene] or [battle shot], but also "
    "don't go too narrow like [one piece episode 4 scene with dagger at timestamp]. "
    "Keep it 10–12 lines total, no intro/outro."
)

# Prefixes the GPT model sometimes injects before image prompts.
_STRIP_PREFIXES = ("Scene:", "Final shot:", "Opening:", "Shot:")


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate_anime_script() -> Path:
    """Call Azure OpenAI to generate a script and write it to *SCRIPT_PATH*.

    Returns the path to the written script file.

    Raises:
        EnvironmentError: If required Azure OpenAI env vars are missing.
    """
    required = {
        "AZURE_OPENAI_API_KEY": AZURE_OPENAI_API_KEY,
        "AZURE_OPENAI_API_VERSION": AZURE_OPENAI_API_VERSION,
        "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
        "AZURE_OPENAI_DEPLOYMENT": AZURE_OPENAI_DEPLOYMENT,
    }
    missing = [name for name, val in required.items() if not val]
    if missing:
        raise EnvironmentError(
            f"Missing required Azure OpenAI env vars: {', '.join(missing)}"
        )

    logger.info("Generating anime script via Azure OpenAI (%s)…", AZURE_OPENAI_DEPLOYMENT)

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=AZURE_OPENAI_DEPLOYMENT,
    )

    script_text = response.choices[0].message.content.strip()
    # Ensure each [image tag] is on its own line.
    script_text = re.sub(r"(\[[^\]]+\])\s+(?!\n)", r"\1\n", script_text)

    SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCRIPT_PATH.write_text(script_text, encoding="utf-8")

    logger.info("Script saved to %s", SCRIPT_PATH)
    return SCRIPT_PATH


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _clean_image_prompt(raw: str) -> str:
    """Strip brackets and common GPT-injected prefixes from an image tag."""
    raw = raw.strip("[]")
    for prefix in _STRIP_PREFIXES:
        if raw.lower().startswith(prefix.lower()):
            return raw[len(prefix):].strip()
    return raw


def parse_script(script_path: Path | str) -> list[tuple[str, str]]:
    """Parse an alternating [image prompt] / narration script file.

    Returns a list of ``(image_prompt, narration_text)`` tuples.

    Raises:
        FileNotFoundError: If *script_path* does not exist.
        ValueError: If the script has an odd number of non-empty lines.
    """
    path = Path(script_path)
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if len(lines) % 2 != 0:
        raise ValueError(
            f"Script must have an even number of lines (got {len(lines)}). "
            "Each [image prompt] must be followed by a narration line."
        )

    segments = [
        (_clean_image_prompt(lines[i]), lines[i + 1])
        for i in range(0, len(lines), 2)
    ]
    logger.info("Parsed %d segments from %s", len(segments), path.name)
    return segments
