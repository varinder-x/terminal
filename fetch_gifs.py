import argparse
import sys
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent / "gifs"
API = "https://api.github.com/repos/snipe/animated-gifs/contents/"
DEFAULT_CATEGORIES = ["excited-happy", "smug", "Thinking", "Approved", "lol"]
MAX_BYTES = 8 * 1024 * 1024


def fetch_category(category, per):
    r = requests.get(API + requests.utils.quote(category), timeout=30)
    r.raise_for_status()
    items = [
        i
        for i in r.json()
        if i.get("type") == "file"
        and i["name"].lower().endswith(".gif")
        and i.get("size", 0) <= MAX_BYTES
    ]
    slug = category.lower().replace(" ", "-")
    saved = []
    for i, item in enumerate(items[:per], 1):
        dest = OUT / f"{slug}-{i}.gif"
        if dest.exists():
            saved.append(dest.name)
            continue
        blob = requests.get(item["download_url"], timeout=60)
        blob.raise_for_status()
        dest.write_bytes(blob.content)
        saved.append(dest.name)
        print(f"saved {dest.name} ({len(blob.content) // 1024} KB)")
    return saved


def main():
    parser = argparse.ArgumentParser(description="Fetch a few GIFs from snipe/animated-gifs.")
    parser.add_argument("--category", action="append", dest="categories")
    parser.add_argument("--per", type=int, default=1, help="gifs per category")
    args = parser.parse_args()

    categories = args.categories or DEFAULT_CATEGORIES
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for cat in categories:
        try:
            total += len(fetch_category(cat, args.per))
        except requests.exceptions.RequestException as exc:
            print(f"skip {cat}: {exc}", file=sys.stderr)
    print(f"done — {total} gif(s) in {OUT}")


if __name__ == "__main__":
    main()
