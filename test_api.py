import os
import socket
import sys

import requests

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
PING_HOSTS = [("1.1.1.1", 53), ("8.8.8.8", 53)]


def play_intro(loops=2):
    from pathlib import Path

    work_gif = Path(__file__).resolve().parent / "gifs" / "work.gif"
    if not work_gif.is_file():
        return

    import gifterm

    try:
        gifterm.play(work_gif, loops=loops, speed=0.8)
    except (OSError, KeyboardInterrupt):
        pass


def check_internet(timeout=3):
    for host, port in PING_HOSTS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def get_api_key():
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        api_key = input("Enter API key: ").strip()
    if not api_key:
        sys.exit("No API key entered.")
    return api_key


def check_api_key(api_key):
    response = requests.get(
        f"{BASE_URL}/models",
        params={"key": api_key},
        timeout=15,
    )
    print("Status:", response.status_code)
    if response.ok:
        print("API key is working.")
        return True
    print("API key check failed:")
    print(response.text)
    return False


def handle_gif_command(command):
    import gifterm

    parts = command.split()
    if parts[0] == "/gifs" or (len(parts) > 1 and parts[1] in {"list", "--list"}):
        names = gifterm.list_gifs()
        print("GIFs:", ", ".join(names) if names else "(none in gifs/)")
        return
    if len(parts) < 2:
        print("Usage: /gif <name>   (e.g. /gif poop) or /gifs to list")
        return

    name = parts[1]
    path = gifterm.resolve(name)
    if path is None:
        print(f"No gif named '{name}'. Try /gifs")
        return
    try:
        gifterm.play(path, loops=2, speed=0.8)
    except OSError as exc:
        print(f"Could not play gif: {exc}")


def chat(api_key):
    url = f"{BASE_URL}/models/{MODEL}:generateContent"
    history = []
    print(f"\nChat with {MODEL}. Type 'quit' to exit.")
    print("Commands: /gif <name>, /gifs\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break

        if user_input.startswith("/gif"):
            handle_gif_command(user_input)
            continue

        history.append({"role": "user", "parts": [{"text": user_input}]})

        try:
            response = requests.post(
                url,
                params={"key": api_key},
                json={"contents": history},
                timeout=180,
            )
        except requests.exceptions.RequestException as exc:
            print(f"Request failed: {exc}\n")
            history.pop()
            continue

        if not response.ok:
            print(f"Error {response.status_code}: {response.text}\n")
            history.pop()
            continue

        data = response.json()
        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            print(f"Unexpected response: {data}\n")
            history.pop()
            continue

        print(f"Gemini: {reply}\n")
        history.append({"role": "model", "parts": [{"text": reply}]})


def main():
    connected = check_internet()
    print("Internet:", "connected" if connected else "NOT connected")
    if not connected:
        sys.exit("No internet connection. Check your network and try again.")

    if "--check" in sys.argv:
        return

    if "--no-intro" not in sys.argv:
        play_intro()

    api_key = get_api_key()
    if check_api_key(api_key):
        chat(api_key)


if __name__ == "__main__":
    main()
