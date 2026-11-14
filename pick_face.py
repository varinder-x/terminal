import base64
import io
import json
import os
import sys
from pathlib import Path

import requests
from PIL import Image

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
BASE = Path(__file__).resolve().parent
IMAGE_EXT = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAX_IMAGES = 16

INSTRUCTIONS = (
    "You are shown several images labeled 1..N. Each is the first frame of a "
    "cartoon/emoji GIF. Choose the single best-looking, friendliest, highest-quality "
    "face. Reply with ONLY JSON in this exact shape: "
    '{"number": <int>, "file": "<exact filename label>", "reason": "<short reason>"}. '
    "The number must match the image label you chose."
)


def get_api_key():
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        key = input("Enter API key: ").strip()
    if not key:
        sys.exit("No API key entered.")
    return key


def collect_files(directories, recursive=False):
    files = []
    for d in directories:
        p = Path(d)
        if not p.is_absolute():
            p = BASE / p
        if not p.is_dir():
            continue
        entries = p.rglob("*") if recursive else p.iterdir()
        for f in sorted(entries):
            if f.is_file() and f.suffix.lower() in IMAGE_EXT:
                files.append(f)
    return files[:MAX_IMAGES]


def encode_frame(path, max_side=256):
    img = Image.open(path)
    img.seek(0)
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def ask(api_key, parts):
    r = requests.post(
        URL,
        params={"key": api_key},
        json={
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "maxOutputTokens": 300,
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        },
        timeout=120,
    )
    return r


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Let Gemini pick the best face image.")
    parser.add_argument("--dir", action="append", dest="dirs",
                        help="directory to scan (repeatable). default: gifs")
    parser.add_argument("--recursive", action="store_true",
                        help="also scan subfolders")
    args = parser.parse_args()

    dirs = args.dirs or ["gifs"]

    files = collect_files(dirs, args.recursive)
    if not files:
        sys.exit(f"No images found in: {', '.join(dirs)}")

    api_key = get_api_key()
    parts = [{"text": INSTRUCTIONS}]
    for i, path in enumerate(files, 1):
        parts.append({"text": f"Image {i}: {path.name}"})
        parts.append({
            "inlineData": {
                "mimeType": "image/png",
                "data": encode_frame(path),
            }
        })

    r = ask(api_key, parts)
    if not r.ok:
        sys.exit(f"Error {r.status_code}: {r.text[:400]}")

    data = r.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        sys.exit(f"Unexpected response: {data}")

    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        pick = json.loads(text)
    except json.JSONDecodeError:
        sys.exit(f"Could not parse model reply:\n{text}")

    print(f"Gemini picked number {pick.get('number')}: {pick.get('file')}")
    if pick.get("reason"):
        print("Reason:", pick["reason"])


if __name__ == "__main__":
    main()
