from __future__ import annotations

import sys
import threading
from contextlib import contextmanager

import theme

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CLEAR_SEQ = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
HOME = "\033[H"


def clear() -> None:
    sys.stdout.write(CLEAR_SEQ)
    sys.stdout.flush()


def wordmark() -> None:
    rule = "━" * 56
    print()
    print(f"  {theme.C_PRIMARY}{rule}{theme.RESET}")
    print(
        f"  {theme.BOLD}{theme.C_PRIMARY}GEMINI{theme.RESET}"
        f" {theme.C_FAINT}·{theme.RESET} "
        f"{theme.C_TEXT}GIF TERMINAL{theme.RESET}"
        f" {theme.C_FAINT}·{theme.RESET} "
        f"{theme.C_MUTED}glitch purple dark{theme.RESET}"
    )
    print(f"  {theme.C_PRIMARY}{rule}{theme.RESET}")


def header(title: str, right: str = "") -> None:
    width = 56
    left = f"  {theme.BOLD}{theme.C_TEXT}{title}{theme.RESET}"
    tail = f"{theme.C_MUTED}{right}{theme.RESET}" if right else ""
    pad = max(1, width + 2 - _visible_len(left) - _visible_len(tail))
    print(f"\n{left}{' ' * pad}{tail}")


def footer_hint(text: str) -> None:
    print(f"  {theme.C_FAINT}{text}{theme.RESET}")


def info(text: str) -> None:
    print(f"  {theme.C_TEXT}{text}{theme.RESET}")


def success(text: str) -> None:
    print(f"  {theme.C_OK}{theme.ICONS['ok']} {text}{theme.RESET}")


def warn(text: str) -> None:
    print(f"  {theme.C_WARN}{theme.ICONS['warn']} {text}{theme.RESET}")


def error(text: str) -> None:
    print(f"  {theme.C_ERROR}{theme.ICONS['error']} {text}{theme.RESET}")


def glitch(text: str) -> None:
    print(f"  {theme.C_GLITCH}{text}{theme.RESET}")


def pause(label: str = "press enter to return") -> None:
    try:
        input(f"\n  {theme.C_FAINT}{label}{theme.RESET} ")
    except (EOFError, KeyboardInterrupt):
        print()


def _visible_len(text: str) -> int:
    state = 0
    count = 0
    for ch in text:
        if ch == "\033":
            state = 1
        elif state == 1:
            if ch == "[":
                state = 2
            else:
                state = 0
        elif state == 2:
            if ch.isalpha():
                state = 0
        else:
            count += 1
    return count


@contextmanager
def spinner(message: str):
    stop = threading.Event()

    def run() -> None:
        index = 0
        while not stop.is_set():
            frame = theme.SPINNER[index % len(theme.SPINNER)]
            sys.stdout.write(
                f"\r  {theme.C_ACCENT}{frame}{theme.RESET} "
                f"{theme.C_TEXT}{message}{theme.RESET}   "
            )
            sys.stdout.flush()
            index += 1
            if stop.wait(0.09):
                break
        sys.stdout.write("\r" + " " * (len(message) + 12) + "\r")
        sys.stdout.flush()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1.0)
