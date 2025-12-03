import os
import requests
from PIL import Image
from src.config import GOOGLE_API_KEY, CSE_ID


def fetch_image_url(query, max_attempts=5):
    if not GOOGLE_API_KEY or not CSE_ID:
        raise EnvironmentError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set for image search.")

    print(f"Fetching image for query: '{query}' with max_attempts={max_attempts}")
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CSE_ID,
        "searchType": "image",
        "num": max_attempts,
        "safe": "active",
    }
    url = "https://www.googleapis.com/customsearch/v1"
    for search_query in (query, "anime background"):
        try:
            response = requests.get(url, params={**params, "q": search_query}, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Image search failed for '{search_query}': {e}")
            continue

        items = response.json().get("items", []) or []
        print(f"Received {len(items)} items from Google CSE for '{search_query}'")

        for idx, item in enumerate(items[:max_attempts]):
            link = item.get("link")
            if not link:
                continue
            print(f"Attempting to validate image {idx + 1}/{len(items)}: {link}")
            try:
                r = requests.get(link, timeout=10)
                content_type = r.headers.get("Content-Type", "")
                if content_type.startswith("image"):
                    print(f"Valid image found: {link}")
                    return link
                print(f"Skipped non-image content: {content_type}")
            except Exception as img_error:
                print(f"Failed to fetch or validate image at {link}: {img_error}")

    raise ValueError(f"No usable image found for '{query}' or fallback query.")


def download_image(image_url, save_path, original_prompt=None, max_attempts=5):
    current_url = image_url
    for attempt in range(1, max_attempts + 1):
        print(f"Downloading image from: {current_url} | attempt {attempt}")
        try:
            r = requests.get(current_url, timeout=10)
            content_type = r.headers.get("Content-Type", "")
            if not content_type.startswith("image"):
                raise ValueError(f"Invalid image content-type: {content_type}")

            with open(save_path, "wb") as f:
                f.write(r.content)
            if not is_valid_image(save_path):
                raise ValueError("Downloaded file failed validation")

            print(f"Successfully downloaded image to {save_path}")
            return
        except Exception as e:
            print(f"Download failed (attempt {attempt}): {e}")
            if os.path.exists(save_path):
                os.remove(save_path)
            if attempt == max_attempts:
                raise RuntimeError(f"Exhausted download attempts for '{original_prompt or current_url}'")

            retry_prompt = original_prompt if original_prompt else "anime background"
            current_url = fetch_image_url(retry_prompt, max_attempts=max_attempts + attempt)


def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        print(f"Image at {path} is valid.")
        return True
    except Exception as e:
        print(f"Image at {path} is invalid: {e}")
        return False
