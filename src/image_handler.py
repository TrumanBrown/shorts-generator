import os
import requests
from PIL import Image
from src.config import GOOGLE_API_KEY, CSE_ID

def fetch_image_url(query, max_attempts=5):
    print(f"Fetching image for query: '{query}' with max_attempts={max_attempts}")
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CSE_ID,
        "q": query,
        "searchType": "image",
        "num": max_attempts,
        "safe": "active"
    }
    url = "https://www.googleapis.com/customsearch/v1"
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        items = response.json().get("items", [])
        print(f"Received {len(items)} items from Google CSE for '{query}'")

        for idx, item in enumerate(items):
            link = item.get("link")
            if link:
                print(f"Attempting to validate image {idx + 1}/{len(items)}: {link}")
                try:
                    r = requests.get(link, timeout=10)
                    content_type = r.headers.get("Content-Type", "")
                    print(f"Content-Type of {link}: {content_type}")
                    if content_type.startswith("image"):
                        print(f"Valid image found: {link}")
                        return link
                    else:
                        print(f"Skipped non-image content: {content_type}")
                except Exception as img_error:
                    print(f"Failed to fetch or validate image at {link}: {img_error}")
                    continue

        raise ValueError("No usable image found")
    except Exception as e:
        print(f"Image fetch failed for query '{query}': {e}")
        print(f"Falling back to 'anime background' for query '{query}'")
        return fetch_image_url("anime background")

def download_image(image_url, save_path, original_prompt=None, attempt=1, max_attempts=5):
    print(f"Downloading image from: {image_url} | attempt {attempt}")
    try:
        r = requests.get(image_url, timeout=10)
        content_type = r.headers.get("Content-Type", "")
        print(f"Downloaded content-type: {content_type}")

        if not content_type.startswith("image"):
            raise ValueError("Invalid image content")

        with open(save_path, 'wb') as f:
            f.write(r.content)
        print(f"Successfully downloaded image to {save_path}")
    except Exception as e:
        print(f"Download failed (attempt {attempt}): {e}")
        if original_prompt and attempt < max_attempts:
            print(f"Retrying download for prompt: '{original_prompt}' (attempt {attempt + 1})")
            next_url = fetch_image_url(original_prompt, max_attempts=5 + attempt)
            download_image(next_url, save_path, original_prompt, attempt + 1, max_attempts)
        else:
            print(f"Falling back to 'anime background' for prompt: '{original_prompt}'")
            fallback_url = fetch_image_url("anime background")
            download_image(fallback_url, save_path)

def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        print(f"Image at {path} is valid.")
        return True
    except Exception as e:
        print(f"Image at {path} is invalid: {e}")
        return False
