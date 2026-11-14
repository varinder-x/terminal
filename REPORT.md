# Full Project Report — Gemini Terminal Hub

## 1. Summary
A terminal-only Python toolkit around Google's Gemini API. Everything is driven
from a screen-clearing, colorized menu (`app.py`) or individual scripts. No web
layer, no frameworks — just `requests` + `Pillow`. It covers API/key checks,
chat, GIF rendering/generation/fetching, vision (face ranking), a benign
red-team harness, and an AI self-repair mode.

## 2. Environment (verified)
- Python 3.12.10 (Microsoft Store)
- requests 2.32.5
- Pillow 12.1.1
- Default model: `gemini-3.5-flash-lite` (override with `GEMINI_MODEL`)
- Auth: env var `GOOGLE_API_KEY` (or prompted at runtime)

## 3. File-by-file

| File | Size | Role |
|---|---|---|
| `app.py` | 12 KB | Unified styled hub (menu + all features) |
| `test_api.py` | 4 KB | Internet + key check, chat loop, `/gif` commands |
| `chat.py` | 1.5 KB | Minimal standalone chat |
| `gifterm.py` | 4 KB | ANSI truecolor GIF/image player |
| `make_gifs.py` | 7 KB | Pillow GIF generators |
| `fetch_gifs.py` | 1.8 KB | Download GIFs from `snipe/animated-gifs` |
| `pick_face.py` | 3.7 KB | Gemini vision picks best face |
| `redteam.py` | 8.6 KB | Benign jailbreak/injection probes |
| `README.md` | 5 KB | Docs + meme pitch |
| `.gitignore` | 99 B | Ignores cache/env/private images |

## 4. Features

### `app.py` — Hub
- Sections: CHAT · MEDIA · LAB · SYSTEM
- Options: Chat, GIF inbox, Pick best face, Generate GIFs, Fetch GIFs,
  Red-team, Check status, AI self-repair, Vibe check, Exit
- Clean ANSI design: slim wordmark, status line
  (`net | key | model | media`), aligned menu.

### `test_api.py`
- `--check` = internet test only (TCP to `1.1.1.1`/`8.8.8.8:53`).
- Key validity via `GET /v1beta/models` (200 = working).
- Chat loop with `/gifs` and `/gif <name>`; `--no-intro`; plays `work.gif` intro.

### `gifterm.py`
- Renders images as truecolor half-block ANSI.
- `--list`, `--once`, `--width`, `--loops`, `--speed`; 500-frame cap.
- Resolves by name, stem, or relative path; scans `gifs/` and `gifs/gifts/`
  recursively.

### `make_gifs.py`
- Generators: happy, sad, laugh, smile, smart, work, working (gear),
  circle (loading ring), poop.
- Skips existing files; `--force` to overwrite. `CIRCLE.gif`, `WORKING.gif`,
  `smart.gif`, `smile.gif` are preserved.

### `fetch_gifs.py`
- GitHub contents API -> downloads a few GIFs (8 MB cap).
  `--category`, `--per`.

### `pick_face.py`
- Sends first frame of each image to Gemini vision; returns `number`, `file`,
  `reason` as JSON. `--dir` (default `gifs/`), `--recursive`, 16-image cap.
  Does not display images.

### `redteam.py`
- 7 benign adversarial prompts; classifies REFUSED / COMPLIANCE / UNCLEAR /
  NO REPLY / SKIPPED; per-probe detection + 503/429 retries.

## 5. Data / folders
- `gifs/` — 14 top-level GIFs (incl. `CIRCLE.gif`, `WORKING.gif`, `smart.gif`,
  `smile.gif`, `work.gif`).
- `gifs/gifts/` — 122 images (also shown in the GIF inbox).
- Total media reported by hub: ~136.

## 6. How to run
```powershell
$env:GOOGLE_API_KEY = "your-key"
python app.py                  # unified hub
python test_api.py --check     # internet only
python gifterm.py --list
python pick_face.py
python redteam.py
```

## 7. Verification results
- All `.py` files parse (AST check).
- `test_api.py --check` -> `Internet: connected`.
- `gifterm.py --list` -> 136 media entries.
- `pick_face.py` -> picked `happy.gif`.
- `make_gifs.py` -> all existing skipped (no overwrite).
- `app.py` -> renders and exits cleanly.
- `redteam.py` -> ran; mixed REFUSED/COMPLIANCE/UNCLEAR (heuristic).

## 8. Known issues / caveats
- `gemini-2.5-flash` is retired; `3.7/3.8-flash` are slow reasoning models that
  time out — default is fast `3.5-flash-lite`.
- Occasional `503 high demand` (transient; retries handle some).
- Large GIFs render slowly (frame cap 500).
- Red-team classifier is a toy heuristic, not ground truth.
- Self-repair can alter any text file — it always writes a `.bak` and
  compile-checks Python, but review diffs before applying.

## 9. Security / policy notes
- No API key is hardcoded in files; however the key was pasted repeatedly in
  chat -> regenerate it.
- `.gitignore` excludes `__pycache__`, `.env`, `gifs/gifts/`, and `*.zip` so
  private images/zips don't get pushed.
- Explicit-content generation was declined; `pick_face` still excludes
  `gifs/gifts/` by default.

## 10. Suggested next steps
1. Rotate the exposed API key.
2. (Optional) `git init && git add . && git commit` on explicit request.
