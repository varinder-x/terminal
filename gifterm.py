import argparse
import shutil
import sys
import time
from pathlib import Path

from PIL import Image, ImageSequence

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
HOME = "\033[H"
GIF_DIR = Path(__file__).resolve().parent / "gifs"
IMAGE_EXT = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _iter_media():
    if not GIF_DIR.is_dir():
        return
    for p in GIF_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXT:
            yield p


def list_gifs():
    names = [p.relative_to(GIF_DIR).with_suffix("").as_posix() for p in _iter_media()]
    return sorted(names)


def resolve(name):
    path = Path(name)
    if path.is_file():
        return path
    direct = GIF_DIR / name
    if direct.is_file():
        return direct
    lower = name.lower().replace("\\", "/")
    media = list(_iter_media())
    for p in media:
        if p.stem.lower() == lower:
            return p
    for p in media:
        rel = p.relative_to(GIF_DIR).with_suffix("").as_posix()
        if rel.lower() == lower:
            return p
    return None

def frame_to_ansi(image, width):
    width = max(10, width)
    height = max(2, int(image.height * width / image.width))
    if height % 2:
        height += 1
    img = image.convert("RGB").resize((width, height))
    px = img.load()

    lines = []
    for y in range(0, height, 2):
        parts = []
        for x in range(width):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, y + 1]
            parts.append(
                f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m\u2580"
            )
        lines.append("".join(parts) + RESET)
    return "\n".join(lines)


def load_frames(path, width, max_frames=500):
    gif = Image.open(path)
    frames = []
    for idx, frame in enumerate(ImageSequence.Iterator(gif)):
        if idx >= max_frames:
            break
        delay = frame.info.get("duration", 100) / 1000.0
        frames.append((frame_to_ansi(frame.copy(), width), max(0.02, delay)))
    return frames


def play(path, width=None, loops=0, speed=1.0, once=False):
    width = width or min(shutil.get_terminal_size().columns, 80)
    frames = load_frames(path, width)

    if once:
        sys.stdout.write(frames[0][0] + "\n")
        return

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()
    try:
        count = 0
        while loops == 0 or count < loops:
            for frame, delay in frames:
                sys.stdout.write(HOME + frame)
                sys.stdout.flush()
                time.sleep(delay * speed)
            count += 1
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Play a GIF in the terminal.")
    parser.add_argument("gif", nargs="?", help="gif name (in gifs/) or path to a .gif file")
    parser.add_argument("--list", action="store_true", help="list gifs in the gifs/ folder")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--loops", type=int, default=0, help="0 = forever")
    parser.add_argument("--once", action="store_true", help="render one frame and exit")
    parser.add_argument("--speed", type=float, default=1.0, help="delay multiplier")
    args = parser.parse_args()

    if args.list:
        names = list_gifs()
        print("\n".join(names) if names else "No gifs found in gifs/")
        return

    if not args.gif:
        parser.error("provide a gif name or path, or use --list")

    path = resolve(args.gif)
    if path is None:
        sys.exit(f"GIF not found: {args.gif} (try --list)")

    try:
        play(path, args.width, args.loops, args.speed, args.once)
    except OSError as exc:
        sys.exit(f"Could not open GIF: {exc}")


if __name__ == "__main__":
    main()
