from __future__ import annotations

import asyncio
import json
import random
from collections import OrderedDict
from pathlib import Path

from PIL import Image
from rich.text import Text
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Middle, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Label,
    LoadingIndicator,
    ProgressBar,
    Static,
)

from gifterm import GIF_DIR, IMAGE_EXT, load_frames

BASE = Path(__file__).resolve().parent
FAVORITES = BASE / "favorites.json"
MAX_FRAMES = 500
THUMB_WIDTH = 14
THUMB_FRAMES = 24
DEFAULT_BORDER = ("round", "#3a3f4b")
PULSE_BORDERS = [
    ("heavy", "#22d3ee"),
    ("heavy", "#a78bfa"),
    ("heavy", "#f472b6"),
]
HINT = "Esc close  ·  Space pause  ·  F favorite  ·  R random  ·  <-/-> slide  ·  +/- zoom  ·  0 reset  ·  Q quit"

_FRAME_CACHE: "OrderedDict[tuple[str, int], list[tuple[str, float]]]" = OrderedDict()
_STILL_CACHE: dict[tuple[str, int], str] = {}


def media_paths() -> list[Path]:
    if not GIF_DIR.is_dir():
        return []
    paths = [
        p for p in GIF_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXT
    ]

    def key(p: Path):
        rel = p.relative_to(GIF_DIR)
        return (0 if len(rel.parts) == 1 else 1, rel.as_posix().lower())

    return sorted(paths, key=key)


def rel_path(path: Path) -> str:
    try:
        return path.relative_to(GIF_DIR).as_posix()
    except ValueError:
        return path.as_posix()


def load_favorites() -> set[str]:
    try:
        data = json.loads(FAVORITES.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def save_favorites(favs: set[str]) -> None:
    try:
        FAVORITES.write_text(json.dumps(sorted(favs), indent=2), encoding="utf-8")
    except OSError:
        pass


def ansi_text(ansi: str) -> Text:
    try:
        return Text.from_ansi(ansi)
    except Exception:
        return Text("")


def still_frame(path: Path, width: int = THUMB_WIDTH) -> str:
    key = (str(path), width)
    cached = _STILL_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        frames = load_frames(path, width, max_frames=1)
    except OSError:
        frames = []
    ansi = frames[0][0] if frames else ""
    _STILL_CACHE[key] = ansi
    return ansi


def decoded_frames(path: Path, width: int) -> list[tuple[str, float]]:
    key = (str(path), width)
    if key in _FRAME_CACHE:
        _FRAME_CACHE.move_to_end(key)
        return _FRAME_CACHE[key]
    frames = load_frames(path, width, max_frames=MAX_FRAMES)
    _FRAME_CACHE[key] = frames
    while len(_FRAME_CACHE) > 48:
        _FRAME_CACHE.popitem(last=False)
    return frames


class Thumbnail(Static):
    can_focus = True

    def __init__(self, path: Path, index: int) -> None:
        super().__init__(classes="thumb")
        self.path = path
        self.index = index
        self.still = ""
        self.anim: list[tuple[str, float]] | None = None
        self.anim_pos = 0
        self.hovered = False

    def on_mount(self) -> None:
        self.border_title = self.path.name

    def set_still(self, ansi: str) -> None:
        self.still = ansi
        if not self.hovered:
            self.update(ansi_text(ansi))

    def ensure_anim(self) -> list[tuple[str, float]]:
        if self.anim is None:
            try:
                self.anim = load_frames(self.path, THUMB_WIDTH, max_frames=THUMB_FRAMES)
            except OSError:
                self.anim = []
        return self.anim

    def tick(self) -> None:
        if not self.hovered:
            return
        frames = self.ensure_anim()
        if frames:
            ansi, _ = frames[self.anim_pos % len(frames)]
            self.anim_pos += 1
            self.update(ansi_text(ansi))

    def reset(self) -> None:
        if self.still:
            self.update(ansi_text(self.still))

    def on_enter(self) -> None:
        self.hovered = True
        screen = self.screen
        if isinstance(screen, GalleryScreen):
            screen.set_hover(self)

    def on_leave(self) -> None:
        self.hovered = False
        screen = self.screen
        if isinstance(screen, GalleryScreen):
            screen.set_hover(None)
        self.reset()

    def on_click(self) -> None:
        screen = self.screen
        if isinstance(screen, GalleryScreen):
            screen.open_at(self.index)


class GalleryScreen(Screen):
    BINDINGS = [
        Binding("left", "thumb_left", "prev", show=False),
        Binding("right", "thumb_right", "next", show=False),
        Binding("up", "thumb_up", "up", show=False),
        Binding("down", "thumb_down", "down", show=False),
        Binding("enter", "open_selected", "open"),
        Binding("escape", "quit_app", "quit"),
        Binding("q", "quit_app", "quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.paths = media_paths()
        self.index = 0
        self.thumbs: list[Thumbnail] = []
        self.hovered: Thumbnail | None = None
        self._pulse = 0
        self._resize_timer = None
        self.favorites = load_favorites()

    def compose(self) -> ComposeResult:
        yield Label("GIF Gallery", id="gallery_title", markup=False)
        if self.paths:
            with VerticalScroll(id="grid"):
                for i, path in enumerate(self.paths):
                    thumb = Thumbnail(path, i)
                    self.thumbs.append(thumb)
                    yield thumb
        else:
            yield Label("No media found in gifs/", id="empty", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.12, self._tick)
        if self.thumbs:
            self._select(0)
            self._load_stills()
        self._fit_columns()

    @work(thread=True, exclusive=True, name="stills")
    def _load_stills(self) -> None:
        for thumb in list(self.thumbs):
            ansi = still_frame(thumb.path)
            if ansi:
                try:
                    self.app.call_from_thread(thumb.set_still, ansi)
                except Exception:
                    return

    def _fit_columns(self) -> None:
        if not self.thumbs:
            return
        try:
            grid = self.query_one("#grid", VerticalScroll)
        except Exception:
            return
        grid.styles.grid_size_columns = max(2, self.size.width // 20)

    def on_resize(self, event: events.Resize) -> None:
        if self._resize_timer is not None:
            self._resize_timer.stop()
        self._resize_timer = self.set_timer(0.15, self._fit_columns)

    def _tick(self) -> None:
        if not self.thumbs:
            return
        active = self.hovered or self.thumbs[self.index]
        active.tick()
        self._pulse = (self._pulse + 1) % len(PULSE_BORDERS)
        self.thumbs[self.index].styles.border = PULSE_BORDERS[self._pulse]

    def set_hover(self, thumb: Thumbnail | None) -> None:
        self.hovered = thumb
        if thumb is not None:
            thumb.tick()

    def _select(self, index: int) -> None:
        if not self.thumbs:
            return
        index %= len(self.thumbs)
        previous = self.thumbs[self.index]
        self.index = index
        if previous is not self.thumbs[index]:
            previous.styles.border = DEFAULT_BORDER
            previous.reset()
        for i, thumb in enumerate(self.thumbs):
            thumb.set_class(i == index, "selected")
        current = self.thumbs[index]
        current.focus()
        current.scroll_visible()
        self._pulse = 0
        current.styles.border = PULSE_BORDERS[0]
        self._update_title()

    def _update_title(self) -> None:
        if not self.paths:
            return
        path = self.paths[self.index]
        star = "* " if rel_path(path) in self.favorites else ""
        name = path.relative_to(GIF_DIR).as_posix()
        try:
            self.query_one("#gallery_title", Label).update(
                f"{star}{name}    ({self.index + 1} / {len(self.paths)})"
            )
        except Exception:
            pass

    def _move(self, delta: int) -> None:
        if self.thumbs:
            self._select(self.index + delta)

    def action_thumb_left(self) -> None:
        self._move(-1)

    def action_thumb_right(self) -> None:
        self._move(1)

    def action_thumb_up(self) -> None:
        self._move(-4)

    def action_thumb_down(self) -> None:
        self._move(4)

    def action_open_selected(self) -> None:
        self.open_at(self.index)

    def action_quit_app(self) -> None:
        self.app.exit()

    def open_at(self, index: int) -> None:
        if not self.paths:
            return
        self.app.push_screen(LightboxScreen(self.paths, index, self.favorites))

    def on_screen_resume(self) -> None:
        self.favorites = load_favorites()
        self._update_title()


class LightboxScreen(Screen):
    BINDINGS = [
        Binding("escape", "close", "close"),
        Binding("space", "toggle_pause", "pause"),
        Binding("f", "favorite", "favorite"),
        Binding("r", "random_gif", "random"),
        Binding("q", "quit_app", "quit"),
        Binding("left", "prev_gif", "prev"),
        Binding("right", "next_gif", "next"),
        Binding("0", "reset_zoom", "reset zoom"),
    ]

    def __init__(self, paths: list[Path], index: int, favorites: set[str]) -> None:
        super().__init__()
        self.paths = paths
        self.index = index
        self.favorites = favorites
        self.frames: list[tuple[str, float]] = []
        self.play_pos = 0
        self.paused = False
        self.width: int | None = None
        self.auto_width = True
        self._typing = None
        self._title_target = ""
        self._title_pos = 0
        self._resize_timer = None

    def compose(self) -> ComposeResult:
        with Vertical(id="lb_root"):
            with Horizontal(id="lb_head"):
                yield Label("", id="lb_title", markup=False)
                yield Label("", id="lb_counter", markup=False)
            with Middle(id="lb_middle"):
                with Horizontal(id="lb_row"):
                    yield Button("<", id="prev", classes="arrow")
                    yield Static("", id="stage")
                    yield Button(">", id="next", classes="arrow")
                with Vertical(id="lb_loading"):
                    yield LoadingIndicator()
                    yield ProgressBar(
                        total=None, show_percentage=False, show_eta=False
                    )
            yield Label(HINT, id="lb_hint", markup=False)
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#lb_loading").display = False
        self.width = self.fit_width()
        self.update_counter()
        self.type_title(self.title_text())
        self.play_current()

    def on_unmount(self) -> None:
        if self._typing is not None:
            self._typing.stop()
            self._typing = None

    def current_path(self) -> Path:
        return self.paths[self.index]

    def title_text(self) -> str:
        path = self.current_path()
        star = "* " if rel_path(path) in self.favorites else ""
        return f"{star}{path.name}"

    def update_counter(self) -> None:
        try:
            self.query_one("#lb_counter", Label).update(
                f"{self.index + 1} / {len(self.paths)}"
            )
        except Exception:
            pass

    def type_title(self, text: str) -> None:
        if self._typing is not None:
            self._typing.stop()
        self._title_target = text
        self._title_pos = 0
        try:
            label = self.query_one("#lb_title", Label)
        except Exception:
            return
        label.update("")
        self._typing = self.set_interval(0.018, self._type_step)

    def _type_step(self) -> None:
        self._title_pos += 1
        try:
            self.query_one("#lb_title", Label).update(
                self._title_target[: self._title_pos]
            )
        except Exception:
            return
        if self._title_pos >= len(self._title_target):
            if self._typing is not None:
                self._typing.stop()
                self._typing = None

    def fit_width(self) -> int:
        try:
            with Image.open(self.current_path()) as im:
                iw, ih = im.size
        except OSError:
            return 40
        size = self.app.size
        avail_w = max(10, size.width - 12)
        avail_lines = max(4, size.height - 8)
        fit = int(avail_lines * 2 * iw / max(1, ih))
        return max(10, min(avail_w, fit))

    @work(exclusive=True, name="player")
    async def play_current(self) -> None:
        path = self.current_path()
        width = self.width or self.fit_width()
        stage = self.query_one("#stage", Static)
        loading = self.query_one("#lb_loading", Vertical)
        row = self.query_one("#lb_row", Horizontal)

        if self.frames:
            stage.animate("styles.opacity", 0.0, duration=0.08)
            await asyncio.sleep(0.09)

        row.display = False
        loading.display = True
        stage.update("")

        try:
            frames = await asyncio.to_thread(decoded_frames, path, width)
        except Exception as exc:
            row.display = True
            loading.display = False
            stage.update(f"[red]Could not open {path.name}: {exc}[/]")
            return

        self.frames = frames
        self.play_pos = 0
        self.paused = False
        row.display = True
        loading.display = False
        stage.styles.opacity = 0.0
        stage.animate("styles.opacity", 1.0, duration=0.14)

        while True:
            if not self.frames:
                return
            if not self.paused:
                ansi, delay = self.frames[self.play_pos % len(self.frames)]
                self.play_pos += 1
                stage.update(ansi_text(ansi))
            await asyncio.sleep(delay)

    def reload(self) -> None:
        self.update_counter()
        self.type_title(self.title_text())
        self.play_current()

    def goto(self, index: int) -> None:
        if not self.paths:
            return
        self.index = index % len(self.paths)
        self.auto_width = True
        self.width = self.fit_width()
        self.reload()

    def action_prev_gif(self) -> None:
        self.goto(self.index - 1)

    def action_next_gif(self) -> None:
        self.goto(self.index + 1)

    def action_random_gif(self) -> None:
        if len(self.paths) <= 1:
            return
        index = random.randrange(len(self.paths) - 1)
        if index >= self.index:
            index += 1
        self.goto(index)

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused
        self.flash_hint("PAUSED" if self.paused else "PLAYING")

    def action_favorite(self) -> None:
        rel = rel_path(self.current_path())
        if rel in self.favorites:
            self.favorites.discard(rel)
            self.flash_hint("removed from favorites")
        else:
            self.favorites.add(rel)
            self.flash_hint("added to favorites")
        save_favorites(self.favorites)
        self.type_title(self.title_text())

    def action_close(self) -> None:
        self.dismiss(None)

    def action_quit_app(self) -> None:
        self.app.exit()

    def zoom(self, delta: int) -> None:
        base = self.width or self.fit_width()
        self.auto_width = False
        self.width = max(10, min(400, base + delta))
        self.type_title(self.title_text())
        self.play_current()

    def action_zoom_in(self) -> None:
        self.zoom(6)

    def action_zoom_out(self) -> None:
        self.zoom(-6)

    def action_reset_zoom(self) -> None:
        self.auto_width = True
        self.width = self.fit_width()
        self.type_title(self.title_text())
        self.play_current()

    def on_key(self, event: events.Key) -> None:
        char = event.character
        if char == "+" or event.key in {"plus", "keypad_plus"}:
            self.zoom(6)
            event.stop()
        elif char == "-" or event.key in {"minus", "keypad_minus"}:
            self.zoom(-6)
            event.stop()

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self.zoom(4)
        event.stop()

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self.zoom(-4)
        event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "prev":
            self.action_prev_gif()
        elif event.button.id == "next":
            self.action_next_gif()

    def flash_hint(self, message: str) -> None:
        try:
            hint = self.query_one("#lb_hint", Label)
        except Exception:
            return
        hint.update(message)
        self.set_timer(1.2, lambda: hint.update(HINT))

    def on_resize(self, event: events.Resize) -> None:
        if not self.auto_width:
            return
        if self._resize_timer is not None:
            self._resize_timer.stop()
        self._resize_timer = self.set_timer(0.2, self.apply_resize)

    def apply_resize(self) -> None:
        if not self.auto_width:
            return
        width = self.fit_width()
        if self.width is None or abs(width - self.width) >= 2:
            self.width = width
            self.play_current()


class GalleryApp(App):
    TITLE = "GIF Gallery"

    CSS = """
    Screen {
        background: #0b0e14;
    }

    #gallery_title {
        dock: top;
        height: 1;
        padding: 0 2;
        background: #11151f;
        color: #e2e8f0;
        text-style: bold;
    }

    #grid {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1 1;
        padding: 1 2;
    }

    .thumb {
        width: 18;
        height: 10;
        border: round #3a3f4b;
        content-align: center middle;
        padding: 0;
    }

    .thumb:hover {
        border: heavy #22d3ee;
    }

    #lb_root {
        width: 100%;
        height: 100%;
        padding: 0 1;
        background: #0b0e14;
    }

    #lb_head {
        height: 1;
    }

    #lb_title {
        width: 1fr;
        color: #e2e8f0;
        text-style: bold;
    }

    #lb_counter {
        width: auto;
        color: #22d3ee;
    }

    #lb_middle {
        height: 1fr;
        align: center middle;
    }

    #lb_row {
        width: auto;
        height: auto;
        align: center middle;
    }

    #stage {
        width: auto;
        height: auto;
    }

    .arrow {
        width: 3;
        min-width: 3;
        height: 3;
        margin: 0 1;
    }

    #lb_loading {
        width: auto;
        height: auto;
        align: center middle;
    }

    #lb_hint {
        height: 1;
        padding: 0 1;
        color: #64748b;
    }

    Footer {
        background: #11151f;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(GalleryScreen())


def main() -> None:
    GalleryApp().run()


if __name__ == "__main__":
    main()
