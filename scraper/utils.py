import json
import os


def clean_text(text: str) -> str:
    """Strips soft hyphens and normalises whitespace."""
    return " ".join(text.replace("\xad", "").split()).strip()


def write_json(data: dict, filepath: str) -> None:
    """Saves a dictionary to a JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"JSON saved to: {os.path.abspath(filepath)}")
    except IOError as e:
        print(f"Failed to write JSON: {e}")


def get_html_soup(url: str):
    """Fetches a URL and returns a BeautifulSoup object, or None on failure."""
    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None
