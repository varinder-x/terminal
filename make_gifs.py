import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(r"C:\Users\Secure Web\Desktop\Varinder\.vscode\Prac\gifs")
SIZE = 72
N = 10
BG = (30, 30, 40)


def new_frame():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    return img, ImageDraw.Draw(img)


FORCE = False


def save(frames, name):
    dest = OUT / f"{name}.gif"
    if dest.exists() and not FORCE:
        print(f"skip {dest.name} (exists, use --force to overwrite)")
        return
    frames[0].save(
        dest,
        save_all=True,
        append_images=frames[1:],
        duration=120,
        loop=0,
        disposal=2,
    )


def face(draw, cx, cy, color, eye="open", mouth="smile", tear_y=None):
    r = 24
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    for ex in (cx - 9, cx + 9):
        if eye == "open":
            draw.ellipse((ex - 3, cy - 8, ex + 3, cy - 2), fill=(20, 20, 20))
        elif eye == "closed":
            draw.arc((ex - 4, cy - 8, ex + 4, cy - 1), 180, 360, fill=(20, 20, 20), width=2)
        elif eye == "happy":
            draw.arc((ex - 5, cy - 9, ex + 5, cy + 1), 200, 340, fill=(20, 20, 20), width=2)
    if mouth == "smile":
        draw.arc((cx - 12, cy + 2, cx + 12, cy + 18), 0, 180, fill=(20, 20, 20), width=3)
    elif mouth == "frown":
        draw.arc((cx - 12, cy + 8, cx + 12, cy + 22), 180, 360, fill=(20, 20, 20), width=3)
    elif mouth == "open":
        draw.ellipse((cx - 8, cy + 4, cx + 8, cy + 18), fill=(20, 20, 20))
        draw.ellipse((cx - 5, cy + 13, cx + 5, cy + 18), fill=(200, 80, 80))
    if tear_y is not None:
        draw.ellipse((cx - 12, tear_y, cx - 8, tear_y + 6), fill=(80, 160, 255))


def build_happy():
    frames = []
    for i in range(N):
        img, d = new_frame()
        bounce = int(abs(math.sin(i / N * math.pi)) * 6)
        face(d, SIZE // 2, SIZE // 2 - bounce, (255, 210, 60), eye="happy", mouth="smile")
        frames.append(img)
    save(frames, "happy")


def build_sad():
    frames = []
    for i in range(N):
        img, d = new_frame()
        tear_y = 30 + int((i % 5) * 6)
        face(d, SIZE // 2, SIZE // 2, (150, 180, 220), eye="closed" if i % 2 else "open",
             mouth="frown", tear_y=tear_y)
        frames.append(img)
    save(frames, "sad")


def build_laugh():
    frames = []
    for i in range(N):
        img, d = new_frame()
        shake = -3 if i % 2 else 3
        face(d, SIZE // 2 + shake, SIZE // 2 - 2, (255, 210, 60), eye="happy", mouth="open")
        frames.append(img)
    save(frames, "laugh")


def build_smart():
    frames = []
    for i in range(N):
        img, d = new_frame()
        face(d, SIZE // 2, SIZE // 2, (255, 224, 130), eye="open", mouth="smile")
        bulb = 30 if i % N < N // 2 else 34
        d.ellipse((SIZE // 2 - bulb // 2, 2, SIZE // 2 + bulb // 2, 2 + bulb),
                  fill=(255, 240, 120))
        d.rectangle((SIZE // 2 - 3, 4 + bulb, SIZE // 2 + 3, 8 + bulb), fill=(120, 120, 120))
        for ex in (SIZE // 2 - 9, SIZE // 2 + 9):
            d.ellipse((ex - 7, SIZE // 2 - 12, ex + 7, SIZE // 2 - 4),
                      outline=(20, 20, 20), width=2)
        d.line((SIZE // 2 - 2, SIZE // 2 - 8, SIZE // 2 + 2, SIZE // 2 - 8),
               fill=(20, 20, 20), width=2)
        frames.append(img)
    save(frames, "smart")


def build_smile():
    frames = []
    for i in range(N):
        img, d = new_frame()
        face(d, SIZE // 2, SIZE // 2, (255, 224, 130),
             eye="closed" if 3 <= i <= 5 else "open", mouth="smile")
        for sx in (14, 58):
            d.ellipse((sx - 4, SIZE // 2 + 2, sx + 4, SIZE // 2 + 8), fill=(255, 150, 150))
        frames.append(img)
    save(frames, "smile")


def build_work():
    frames = []
    skin = (255, 224, 163)
    for i in range(N):
        img, d = new_frame()
        d.ellipse((24, 6, 48, 30), fill=skin)
        d.arc((23, 4, 49, 26), 180, 360, fill=(60, 40, 20), width=4)
        for ex in (30, 42):
            d.ellipse((ex - 2, 18, ex + 2, 22), fill=(20, 20, 20))
        d.rectangle((4, 60, 68, 66), fill=(110, 75, 50))
        d.rectangle((16, 34, 56, 58), fill=(25, 25, 35), outline=(70, 70, 90))
        for j in range(5):
            y = 37 + ((j * 5 + i * 2) % 18)
            w = 10 + ((j * 7) % 22)
            d.rectangle((19, y, 19 + w, y + 2), fill=(90, 220, 120))
        tap = 1 if i % 2 else 0
        d.ellipse((24, 53 + tap, 30, 59 + tap), fill=skin)
        d.ellipse((42, 53 + tap, 48, 59 + tap), fill=skin)
        frames.append(img)
    save(frames, "work")


def build_working():
    frames = []
    cx = cy = SIZE // 2
    r_out, r_in, teeth = 24, 17, 8
    for i in range(N):
        img, d = new_frame()
        ang0 = i / N * 2 * math.pi
        pts = []
        for t in range(teeth):
            a = ang0 + t * 2 * math.pi / teeth
            for rr, da in [(r_in, -0.20), (r_out, -0.13), (r_out, 0.13), (r_in, 0.20)]:
                pts.append((cx + rr * math.cos(a + da), cy + rr * math.sin(a + da)))
        d.polygon(pts, fill=(130, 150, 180))
        d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=(70, 90, 120))
        d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(25, 25, 35))
        frames.append(img)
    save(frames, "working")


def build_circle():
    frames = []
    cx = cy = SIZE // 2
    r = 25
    for i in range(N):
        img, d = new_frame()
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(60, 70, 90), width=4)
        start = i / N * 360
        end = start + 100
        d.arc((cx - r, cy - r, cx + r, cy + r), start, end, fill=(90, 200, 255), width=4)
        a = math.radians(end)
        dx, dy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse((dx - 5, dy - 5, dx + 5, dy + 5), fill=(255, 255, 255))
        d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(90, 200, 255))
        frames.append(img)
    save(frames, "circle")


def build_poop():
    frames = []
    brown = (120, 72, 32)
    dark = (90, 52, 22)
    for i in range(N):
        img, d = new_frame()
        wob = int(math.sin(i / N * 2 * math.pi) * 4)
        cx = SIZE // 2 + wob
        d.ellipse((cx - 22, 44, cx + 22, 64), fill=brown)
        d.ellipse((cx - 17, 34, cx + 17, 54), fill=dark)
        d.ellipse((cx - 11, 25, cx + 11, 44), fill=brown)
        d.ellipse((cx - 5, 18, cx + 5, 33), fill=dark)
        for ex in (cx - 8, cx + 8):
            d.ellipse((ex - 4, 36, ex + 4, 44), fill=(255, 255, 255))
            d.ellipse((ex - 2, 38, ex + 2, 42), fill=(20, 20, 20))
        d.arc((cx - 7, 44, cx + 7, 54), 0, 180, fill=(20, 20, 20), width=2)
        frames.append(img)
    save(frames, "poop")


if __name__ == "__main__":
    import sys

    FORCE = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    build_happy()
    build_sad()
    build_laugh()
    build_smile()
    build_smart()
    build_work()
    build_working()
    build_circle()
    build_poop()
    print("gifs:", ", ".join(sorted(p.name for p in OUT.glob("*.gif"))))
