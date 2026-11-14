from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
FAVORITES = BASE / "favorites.json"


def load() -> set[str]:
    try:
        data = json.loads(FAVORITES.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def save(favs: set[str]) -> None:
    try:
        FAVORITES.write_text(
            json.dumps(sorted(favs), indent=2), encoding="utf-8"
        )
    except OSError:
        pass


def toggle(rel: str) -> bool:
    favs = load()
    if rel in favs:
        favs.discard(rel)
        added = False
    else:
        favs.add(rel)
        added = True
    save(favs)
    return added
