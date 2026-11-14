# Gemini Terminal Hub

> "It compiles, therefore it is. Probably."

A caffeinated Python side-project that lives entirely in your terminal: it
checks a Gemini API key, chats with the model, renders GIFs as colored ANSI
art, lets the model pick the best face, downloads reaction GIFs, stress-tests
the model with benign jailbreak prompts, and — the main-character feature —
asks Gemini to patch its own bugs like a tiny self-repair gremlin.

No HTML. No frameworks. Just `requests`, `Pillow`, and unreasonable confidence.

## The pitch (meme certified)

**Gemini Terminal Hub** is what happens when a dev says "I'll just test the API
key real quick" and wakes up three days later with a glowing terminal, a folder
full of GIFs, and an AI that edits its own source code.

- Chat with Gemini without opening a browser like some kind of animal.
- Play GIFs in the terminal because pixels are pixels.
- Let the AI judge cartoon faces (it has opinions).
- Red-team the model with prompts that would make a chatbot sweat.
- Ask Gemini to fix your code, then panic as it shows you the diff.

Built for people who think "works on my machine" is a valid deployment
strategy.


## Requirements

- Python 3.9+
- Packages:

```bash
pip install requests pillow
```

## Setup

Set your Gemini API key (get one from Google AI Studio):

```powershell
$env:GOOGLE_API_KEY = "your-api-key"
```

Also supported: the scripts prompt for the key if the env var is not set.

Optional: choose a model (default `gemini-3.5-flash-lite`):

```powershell
$env:GEMINI_MODEL = "gemini-3.5-flash"
```

> The 3.7/3.8 "flash" models are slow reasoning models and may time out in a
> chat loop. `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` respond fast.

## Files

| File | What it does |
| --- | --- |
| `app.py` | Unified terminal hub — menu-driven UI for everything below. |
| `test_api.py` | Checks internet + API key, then starts a chat. Supports `/gif` commands. |
| `chat.py` | Minimal standalone chat loop. |
| `gifterm.py` | Plays a GIF in the terminal using ANSI truecolor half-blocks. |
| `make_gifs.py` | Generates sample cartoon GIFs (happy, sad, laugh, smile, smart, work, poop). |
| `fetch_gifs.py` | Downloads a few reaction GIFs from `snipe/animated-gifs` into `gifs/`. |
| `pick_face.py` | Sends images to Gemini and asks it to pick the best-looking face. |
| `redteam.py` | Runs benign adversarial prompts and reports REFUSED / COMPLIANCE / UNCLEAR. |

## Usage

### Unified hub (recommended)

```powershell
python app.py
```

A styled, menu-driven terminal UI that ties everything together:

```
CHAT    chat with Gemini
MEDIA   GIF inbox (gifs/ + gifs/gifts/), pick best face
LAB     generate sample GIFs, fetch reaction GIFs, red-team probes, vibe check
SYSTEM  check connection & key, AI self-repair, exit
```

**AI self-repair** lists every editable file in the project (Python, HTML, CSS,
Markdown, etc.), sends it to Gemini, shows a colored diff, and — only after you
confirm — writes the fix. Originals are backed up as `<file>.bak` and Python
files are compile-checked.

### Check connectivity and API key

```powershell
python test_api.py --check      # just internet check, then exit
python test_api.py              # internet + key check, then chat
python test_api.py --no-intro   # skip the work.gif intro animation
```

Inside the chat:

```
/gifs           list available GIFs
/gif <name>     play a GIF (e.g. /gif poop)
quit            exit
```

### Play a GIF

```powershell
python gifterm.py --list
python gifterm.py work
python gifterm.py laugh --width 60 --loops 3 --speed 0.5
python gifterm.py C:\path\to\file.gif
```

### Generate sample GIFs

```powershell
python make_gifs.py            # skip files that already exist
python make_gifs.py --force    # overwrite with freshly generated frames
```

Generates: happy, sad, laugh, smile, smart, work, working (spinning gear),
circle (loading ring), poop.

### Fetch reaction GIFs

```powershell
python fetch_gifs.py
python fetch_gifs.py --per 2 --category smug --category lol
```

### Let Gemini pick the best face

```powershell
python pick_face.py                       # scans gifs/ (top level)
python pick_face.py --dir gifs --recursive
python pick_face.py --dir some_folder
```

The chosen image is reported by number and filename only; images are not
displayed in the terminal.

### Red-team probes

```powershell
python redteam.py
```

Sends a fixed list of benign prompt-injection / jailbreak-style prompts and
prints a heuristic verdict for each. This is a toy classifier, not ground truth.

## Folders

- `gifs/` — GIF library. Any file you drop here is playable by its name.
- `gifs/gifts/` — extra images; also listed in the GIF inbox (shown as one frame).

## Notes

- Never commit your API key. Use the `GOOGLE_API_KEY` environment variable.
- Terminal GIF playback is CPU/ANSI-heavy; large GIFs are capped at 500 frames.
- `fetch_gifs.py` downloads third-party images; respect their copyright.
