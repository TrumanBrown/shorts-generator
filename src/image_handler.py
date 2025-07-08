import os
import requests
from PIL import Image
from src.config import GOOGLE_API_KEY, CSE_ID

def fetch_image_url(query, max_attempts=5):
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
        response = requests.get(url, params=params)
        items = response.json().get("items", [])
        for item in items:
            link = item.get("link")
            if link:
                try:
                    r = requests.get(link, timeout=10)
                    if r.headers.get("Content-Type", "").startswith("image"):
                        return link
                except:
                    continue
        raise ValueError("No usable image found")
    except Exception as e:
        print(f"Image fetch failed: {e}")
        return fetch_image_url("anime background")

def download_image(image_url, save_path, original_prompt=None, attempt=1, max_attempts=5):
    try:
        r = requests.get(image_url, timeout=10)
        if not r.headers.get("Content-Type", "").startswith("image"):
            raise ValueError("Invalid image content")
        with open(save_path, 'wb') as f:
            f.write(r.content)
        print(f"Downloaded image to {save_path}")
    except Exception as e:
        print(f"Download failed (attempt {attempt}): {e}")
        if original_prompt and attempt < max_attempts:
            next_url = fetch_image_url(original_prompt, max_attempts=5 + attempt)
            download_image(next_url, save_path, original_prompt, attempt + 1, max_attempts)
        else:
            fallback_url = fetch_image_url("anime background")
            download_image(fallback_url, save_path)

def is_valid_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except:
        return False
