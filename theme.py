"""GLITCH PURPLE DARK theme — the single source of truth for colour.

Every screen imports from here. Nothing else should hardcode a colour.
"""

from __future__ import annotations

BG = "#0a0612"
SURFACE = "#1a0b2e"
SURFACE_2 = "#241035"
PRIMARY = "#9d4edd"
ACCENT = "#ff2e97"
GLITCH = "#00f5d4"
TEXT = "#c8b6ff"
MUTED = "#6d5a8a"
FAINT = "#4a3a63"
OK = "#00f5d4"
WARN = "#ffd166"
ERROR = "#ff2e97"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def set_fg(value: str) -> str:
    r, g, b = _hex_to_rgb(value)
    return f"\033[38;2;{r};{g};{b}m"


def set_bg(value: str) -> str:
    r, g, b = _hex_to_rgb(value)
    return f"\033[48;2;{r};{g};{b}m"


def paint(text: str, fg: str | None = None, bg: str | None = None,
          bold: bool = False) -> str:
    prefix = (BOLD if bold else "") + (set_fg(fg) if fg else "")
    prefix += set_bg(bg) if bg else ""
    return f"{prefix}{text}{RESET}"


C_BG = set_bg(BG)
C_SURFACE = set_fg(SURFACE)
C_PRIMARY = set_fg(PRIMARY)
C_ACCENT = set_fg(ACCENT)
C_GLITCH = set_fg(GLITCH)
C_TEXT = set_fg(TEXT)
C_MUTED = set_fg(MUTED)
C_FAINT = set_fg(FAINT)
C_OK = set_fg(OK)
C_WARN = set_fg(WARN)
C_ERROR = set_fg(ERROR)

BORDER = "round"
BORDER_FOCUS = "heavy"

ICONS = {
    "net": "●",
    "key": "●",
    "model": "◆",
    "media": "▦",
    "gif": "▣",
    "star": "★",
    "play": "▶",
    "random": "⤨",
    "search": "⌕",
    "gallery": "▦",
    "chat": "✦",
    "face": "☺",
    "lab": "⚗",
    "system": "⚙",
    "ok": "✓",
    "warn": "!",
    "error": "✗",
}

SPINNER = "⣾⣽⣻⢿⡿⣟⣯⣷"
