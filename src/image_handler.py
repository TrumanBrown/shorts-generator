"""Image search and download via Google Custom Search.

Fetches anime images matching script prompts, validates them with Pillow,
and saves them to disk for the video renderer.
"""

import logging
import os
from pathlib import Path

import requests
from PIL import Image

from src.config import GOOGLE_API_KEY, GOOGLE_CSE_ID

logger = logging.getLogger(__name__)

_GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"
_FALLBACK_QUERY = "anime background"
_REQUEST_TIMEOUT = 10  # seconds


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_image_url(query: str, max_results: int = 5) -> str:
    """Search Google CSE for an image matching *query* and return the first valid URL.

    Falls back to a generic anime query if the specific search yields nothing.

    Raises:
        EnvironmentError: If Google API credentials are not configured.
        ValueError: If no usable image is found after exhausting results.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise EnvironmentError(
            "GOOGLE_API_KEY and GOOGLE_CSE_ID must be set for image search."
        )

    for search_query in (query, _FALLBACK_QUERY):
        logger.info("Searching images for '%s' (max %d results)", search_query, max_results)
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": search_query,
            "searchType": "image",
            "num": max_results,
            "safe": "active",
        }

        try:
            response = requests.get(_GOOGLE_CSE_URL, params=params, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Image search failed for '%s': %s", search_query, exc)
            continue

        items = response.json().get("items") or []
        logger.debug("Received %d results for '%s'", len(items), search_query)

        for idx, item in enumerate(items, 1):
            link = item.get("link")
            if not link:
                continue
            logger.debug("Validating result %d/%d: %s", idx, len(items), link)
            try:
                head = requests.get(link, timeout=_REQUEST_TIMEOUT)
                if head.headers.get("Content-Type", "").startswith("image"):
                    logger.info("Valid image found: %s", link)
                    return link
                logger.debug("Skipped non-image content: %s", head.headers.get("Content-Type"))
            except requests.RequestException as exc:
                logger.debug("Could not reach %s: %s", link, exc)

    raise ValueError(f"No usable image found for '{query}' or fallback query.")


def download_image(
    image_url: str,
    save_path: str | Path,
    original_prompt: str | None = None,
    max_attempts: int = 5,
) -> None:
    """Download an image from *image_url* and save it to *save_path*.

    On failure the function re-fetches a new URL using *original_prompt*
    and retries up to *max_attempts* times.

    Raises:
        RuntimeError: If all download attempts are exhausted.
    """
    current_url = image_url
    for attempt in range(1, max_attempts + 1):
        logger.info("Downloading image (attempt %d/%d): %s", attempt, max_attempts, current_url)
        try:
            resp = requests.get(current_url, timeout=_REQUEST_TIMEOUT)
            content_type = resp.headers.get("Content-Type", "")
            if not content_type.startswith("image"):
                raise ValueError(f"Response is not an image (Content-Type: {content_type})")

            Path(save_path).write_bytes(resp.content)

            if not is_valid_image(save_path):
                raise ValueError("Downloaded file failed Pillow validation")

            logger.info("Image saved to %s", save_path)
            return

        except Exception as exc:
            logger.warning("Download failed (attempt %d/%d): %s", attempt, max_attempts, exc)
            if os.path.exists(save_path):
                os.remove(save_path)
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Exhausted {max_attempts} download attempts for "
                    f"'{original_prompt or current_url}'"
                ) from exc

            retry_query = original_prompt or _FALLBACK_QUERY
            current_url = fetch_image_url(retry_query, max_results=max_attempts + attempt)


def is_valid_image(path: str | Path) -> bool:
    """Return True if *path* is a valid image file (per Pillow)."""
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception as exc:
        logger.debug("Invalid image at %s: %s", path, exc)
        return False
