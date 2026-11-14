from __future__ import annotations

import datetime
import sys
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG_DIR = BASE / "logs"
LOG_FILE = LOG_DIR / "app.log"


def log_exception(exc: BaseException, context: str = "") -> None:
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            stamp = datetime.datetime.now().isoformat(timespec="seconds")
            handle.write(f"\n[{stamp}] {context}\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=handle)
    except OSError:
        pass


def friendly(exc: BaseException) -> str:
    name = type(exc).__name__
    text = str(exc).strip()
    if text:
        return text
    return name


def install_excepthook() -> None:
    def hook(exc_type, exc_value, exc_tb):
        log_exception(exc_value, "uncaught")
        print(f"\n  ! unexpected error: {friendly(exc_value)}  (see logs/app.log)")

    sys.excepthook = hook
