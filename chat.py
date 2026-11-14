import os
import sys

import requests

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def main():
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        api_key = input("Enter API key: ").strip()
    if not api_key:
        sys.exit("No API key entered.")

    history = []
    print(f"Chat with {MODEL}. Type 'quit' to exit.\n")

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

        history.append({"role": "user", "parts": [{"text": user_input}]})

        response = requests.post(
            URL,
            params={"key": api_key},
            json={"contents": history},
            timeout=60,
        )

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


if __name__ == "__main__":
    main()
