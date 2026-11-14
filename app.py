import difflib
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
GREY = "\033[90m"
WHITE = "\033[97m"
CLEAR = "\033[2J\033[H"
ANSI_RE = re.compile(r"\033\[[0-9;]*m")

ACCENT = CYAN
SECTIONS = [
    ("CHAT", [
        ("1", "Chat with Gemini", "talk to the model"),
    ]),
    ("MEDIA", [
        ("2", "GIF inbox", "play a gif from gifs/"),
        ("3", "Pick best face", "gemini ranks the faces"),
    ]),
    ("LAB", [
        ("4", "Generate sample GIFs", "happy / sad / smart / work"),
        ("5", "Fetch reaction GIFs", "from snipe/animated-gifs"),
        ("6", "Red-team probes", "benign jailbreak tests"),
        ("9", "Vibe check", "random dev mood"),
    ]),
    ("SYSTEM", [
        ("7", "Check connection & key", "network + api status"),
        ("8", "AI self-repair", "let gemini fix a script"),
        ("0", "Exit", ""),
    ]),
]


def vlen(s):
    return len(ANSI_RE.sub("", s))


def pad(s, width):
    return s + " " * max(0, width - vlen(s))


def card(lines, width=60):
    print(f"{GREY}  ┌{'─' * width}┐{RESET}")
    for line in lines:
        print(f"{GREY}  │{RESET} {pad(line, width - 2)} {GREY}│{RESET}")
    print(f"{GREY}  └{'─' * width}┘{RESET}")


def banner():
    width = 60
    print(f"  {ACCENT}{'━' * width}{RESET}")
    title = f"  {BOLD}{WHITE}GEMINI{RESET} {GREY}·{RESET} {WHITE}TERMINAL HUB{RESET}"
    ver = f"{DIM}v1.0{RESET}"
    gap = max(1, width + 2 - vlen(title) - vlen(ver))
    print(title + " " * gap + ver)
    print(f"  {DIM}a python side-project with main-character energy{RESET}")
    print(f"  {ACCENT}{'━' * width}{RESET}")


def status_bar():
    from test_api import check_internet
    from gifterm import list_gifs

    online = check_internet()
    key_set = bool(os.environ.get("GOOGLE_API_KEY", "").strip())
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    net = f"{GREEN}●{RESET} {DIM}online{RESET}" if online else f"{RED}●{RESET} {DIM}offline{RESET}"
    key = f"{GREEN}●{RESET} {DIM}key{RESET}" if key_set else f"{YELLOW}○{RESET} {DIM}no key{RESET}"
    sep = f"  {GREY}│{RESET}  "
    print()
    print("  " + sep.join([net, key, f"{DIM}{model}{RESET}", f"{DIM}{len(list_gifs())} media{RESET}"]))
    print()


def show_menu():
    hint_col = 46
    for section, items in SECTIONS:
        print(f"  {DIM}{BOLD}{section}{RESET}")
        for key, label, desc in items:
            num_color = RED if key == "0" else ACCENT
            left = f"   {num_color}{key:>2}{RESET}   {WHITE}{label}{RESET}"
            gap = max(2, hint_col - vlen(left))
            print((left + " " * gap + f"{DIM}{desc}{RESET}").rstrip())
        print()


def ensure_key():
    if os.environ.get("GOOGLE_API_KEY", "").strip():
        return
    key = input(f"  {YELLOW}Enter Gemini API key{RESET} ❯ ").strip()
    if key:
        os.environ["GOOGLE_API_KEY"] = key


def pause():
    input(f"\n  {DIM}press enter to return to the hub{RESET} ")


def run_script(name, *args):
    cmd = [sys.executable, str(BASE / name), *args]
    print(f"  {GREY}▸ {name} {' '.join(args)}{RESET}\n")
    return subprocess.run(cmd, cwd=BASE).returncode


def cmd_chat():
    ensure_key()
    run_script("test_api.py", "--no-intro")


def cmd_gif_inbox():
    from gifterm import list_gifs, resolve, play

    names = list_gifs()
    if not names:
        print(f"  {RED}No GIFs in gifs/. Add some first.{RESET}")
        return

    print(f"  {MAGENTA}{BOLD}GIF INBOX{RESET}")
    for i, name in enumerate(names, 1):
        print(f"   {CYAN}[{i:>2}]{RESET} {WHITE}{name}{RESET}")
    print()

    choice = input(f"  {YELLOW}pick number or name{RESET} ❯ ").strip()
    if not choice:
        return
    if choice.isdigit():
        idx = int(choice)
        if not 1 <= idx <= len(names):
            print(f"  {RED}Out of range.{RESET}")
            return
        target = names[idx - 1]
    else:
        target = choice

    path = resolve(target)
    if path is None:
        print(f"  {RED}No GIF named '{target}'.{RESET}")
        return
    try:
        play(path, loops=2, speed=0.8)
    except OSError as exc:
        print(f"  {RED}Could not play GIF: {exc}{RESET}")


def cmd_pick_face():
    ensure_key()
    run_script("pick_face.py")


def cmd_make_gifs():
    run_script("make_gifs.py")


def cmd_fetch_gifs():
    run_script("fetch_gifs.py", "--per", "1")


def cmd_redteam():
    ensure_key()
    run_script("redteam.py")


VIBES = [
    "compiles on the first try — rarity: mythic",
    "works on my machine. shipping it.",
    "git commit -m \"final final v2 REAL\"",
    "the bug was a missing comma. it always is.",
    "coffee in, code out.",
    "stack-overflow copy-paste, but with confidence.",
    "writes tests after the bug report, like a legend.",
]


def top_level_gifs():
    from gifterm import GIF_DIR, IMAGE_EXT

    if not GIF_DIR.is_dir():
        return []
    return sorted(
        p for p in GIF_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXT
    )


def cmd_vibe():
    import random

    from gifterm import play

    print(f"  {ACCENT}vibe check...{RESET}")
    print(f"  {WHITE}{random.choice(VIBES)}{RESET}\n")
    gifs = top_level_gifs()
    if gifs:
        g = random.choice(gifs)
        print(f"  {DIM}mood: {g.name}{RESET}")
        try:
            play(g, loops=1, speed=0.9)
        except OSError:
            pass


def cmd_check():
    from test_api import check_internet, check_api_key

    online = check_internet()
    state = f"{GREEN}connected{RESET}" if online else f"{RED}NOT connected{RESET}"
    print(f"  internet: {state}")
    ensure_key()
    check_api_key(os.environ["GOOGLE_API_KEY"])


def gemini_generate(api_key, prompt, max_tokens=8192):
    import requests

    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(
        url,
        params={"key": api_key},
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens},
        },
        timeout=180,
    )
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\n", "", text)
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def show_diff(old, new, name):
    diff = list(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile=f"{name} (current)", tofile=f"{name} (fixed)", lineterm="",
    ))
    shown = 0
    for line in diff:
        if shown >= 80:
            print(f"  {DIM}... diff truncated ...{RESET}")
            break
        if line.startswith("+++") or line.startswith("---"):
            print(f"  {GREY}{line}{RESET}")
        elif line.startswith("+"):
            print(f"  {GREEN}{line}{RESET}")
        elif line.startswith("-"):
            print(f"  {RED}{line}{RESET}")
        elif line.startswith("@@"):
            print(f"  {CYAN}{line}{RESET}")
        else:
            print(f"  {DIM}{line}{RESET}")
        shown += 1
    changed = sum(
        1 for l in diff
        if (l.startswith("+") or l.startswith("-"))
        and not l.startswith(("+++", "---"))
    )
    return changed


def cmd_self_repair():
    ensure_key()
    key = os.environ["GOOGLE_API_KEY"]

    skip = {
        ".gif", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".bmp",
        ".zip", ".bak", ".pyc", ".exe", ".dll", ".mp3", ".mp4", ".pdf",
    }
    files = sorted(
        p.name for p in BASE.iterdir()
        if p.is_file()
        and p.suffix.lower() not in skip
        and not p.name.startswith(".")
        and p.stat().st_size <= 512 * 1024
    )
    if not files:
        print(f"  {RED}No editable files found.{RESET}")
        return

    print(f"  {MAGENTA}{BOLD}AI SELF-REPAIR{RESET}")
    for i, name in enumerate(files, 1):
        print(f"   {CYAN}[{i:>2}]{RESET} {WHITE}{name}{RESET}")
    print()

    choice = input(f"  {YELLOW}file to repair{RESET} ❯ ").strip()
    if not choice:
        return
    if choice.isdigit():
        idx = int(choice)
        if not 1 <= idx <= len(files):
            print(f"  {RED}Out of range.{RESET}")
            return
        name = files[idx - 1]
    else:
        name = choice

    path = (BASE / name).resolve()
    if BASE not in path.parents or not path.is_file():
        print(f"  {RED}Not a valid file in this folder.{RESET}")
        return

    note = input(f"  {YELLOW}what should be fixed? (optional){RESET} ❯ ").strip()
    code = path.read_text(encoding="utf-8", errors="replace")

    prompt = (
        "You are a senior engineer. The file below may contain bugs or small "
        "issues. Fix them while preserving the existing behavior, style, and "
        "structure. Return ONLY the complete corrected file content. Do not use "
        "markdown fences and do not add commentary.\n\n"
        f"Extra notes: {note or 'none'}\n\n"
        f"File: {path.name}\n\n{code}"
    )

    print(f"\n  {DIM}asking gemini to review {path.name}...{RESET}")
    try:
        fixed = strip_fences(gemini_generate(key, prompt))
    except Exception as exc:
        print(f"  {RED}Request failed: {exc}{RESET}")
        return

    if fixed.strip() == code.strip():
        print(f"  {GREEN}No changes suggested — file looks fine.{RESET}")
        return

    if path.suffix == ".py":
        try:
            compile(fixed, path.name, "exec")
        except SyntaxError as exc:
            print(f"  {RED}Gemini returned code with a syntax error: {exc}{RESET}")
            return

    print()
    changed = show_diff(code, fixed, path.name)
    print(f"\n  {YELLOW}{changed} changed line(s).{RESET}")
    confirm = input(f"  {YELLOW}apply fix? [y/N]{RESET} ❯ ").strip().lower()
    if confirm != "y":
        print(f"  {DIM}cancelled — nothing written.{RESET}")
        return

    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(code, encoding="utf-8")
    path.write_text(fixed, encoding="utf-8")

    if path.suffix == ".py":
        res = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)], cwd=BASE,
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  {GREEN}✓ applied. backup: {backup.name} · compile OK{RESET}")
        else:
            print(f"  {RED}✗ applied but compile failed:{RESET}\n{res.stderr[:400]}")
    else:
        print(f"  {GREEN}✓ applied. backup: {backup.name}{RESET}")


ACTIONS = {
    "1": cmd_chat,
    "2": cmd_gif_inbox,
    "3": cmd_pick_face,
    "4": cmd_make_gifs,
    "5": cmd_fetch_gifs,
    "6": cmd_redteam,
    "7": cmd_check,
    "8": cmd_self_repair,
    "9": cmd_vibe,
}


def main():
    while True:
        print(CLEAR, end="")
        banner()
        status_bar()
        show_menu()
        try:
            choice = input(f"  {ACCENT}❯{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in {"0", "q", "quit", "exit"}:
            break
        action = ACTIONS.get(choice)
        if action is None:
            print(f"  {RED}unknown option{RESET}")
            pause()
            continue

        try:
            action()
        except KeyboardInterrupt:
            print(f"\n  {DIM}cancelled{RESET}")
        pause()

    print(f"\n  {CYAN}bye.{RESET}")


if __name__ == "__main__":
    main()
