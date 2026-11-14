"""Single shared Gemini client.

Handles .env + environment key loading, friendly errors, and retry/backoff on
429/503. Every screen goes through here — no duplicated request code.
"""

from __future__ import annotations

import base64
import io
import os
import socket
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

BASE = Path(__file__).resolve().parent
ENV_PATH = BASE / ".env"
API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
RETRY_STATUS = {429, 503}
MAX_RETRIES = 3
PING_HOSTS = [("1.1.1.1", 53), ("8.8.8.8", 53)]


class GeminiError(Exception):
    """A failure with a message that is safe to show to the user."""


def current_model() -> str:
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def load_env() -> None:
    try:
        load_dotenv(ENV_PATH)
    except Exception:
        pass


def set_env(name: str, value: str) -> None:
    lines: list[str] = []
    found = False
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{name}="):
                lines.append(f"{name}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{name}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_PATH, 0o600)
    except OSError:
        pass
    os.environ[name] = value


def save_key(key: str) -> None:
    set_env("GOOGLE_API_KEY", key)


def mask_key(key: str | None) -> str:
    key = (key or "").strip()
    return f"{key[:4]}****" if key else "(not set)"


def load_key(prompt: bool = True) -> str:
    load_env()
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if key or not prompt:
        return key
    key = input("  Gemini API key: ").strip()
    if not key:
        return ""
    os.environ["GOOGLE_API_KEY"] = key
    answer = input("  save key to .env? [y/N] ").strip().lower()
    if answer == "y":
        save_key(key)
        print("  saved to .env")
    return key


def check_internet(timeout: float = 3.0) -> bool:
    for host, port in PING_HOSTS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _request(method: str, url: str, *, timeout: float = 30, **kwargs):
    response = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
        except requests.exceptions.Timeout as exc:
            raise GeminiError(
                "request timed out — try again or switch to a faster model"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise GeminiError(
                "no internet connection — check your network"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise GeminiError(f"network error: {exc}") from exc
        if response.status_code in RETRY_STATUS and attempt < MAX_RETRIES - 1:
            time.sleep(0.8 * (2 ** attempt))
            continue
        return response
    return response


def _raise_for(response) -> None:
    if response is None:
        raise GeminiError("empty response from the API")
    if response.ok:
        return
    code = response.status_code
    if code in (401, 403):
        raise GeminiError(
            "bad or unauthorised API key — regenerate it and update .env"
        )
    if code == 429:
        raise GeminiError(
            "quota / rate limit hit (429) — wait a moment or check your plan"
        )
    if code == 404:
        raise GeminiError(
            "model unavailable (404) — set GEMINI_MODEL to a valid model"
        )
    if code == 503:
        raise GeminiError("service busy (503) — try again shortly")
    snippet = response.text[:200].replace("\n", " ")
    raise GeminiError(f"request failed ({code}): {snippet}")


def encode_image(path) -> str:
    with Image.open(path) as image:
        image.seek(0)
        rgb = image.convert("RGB")
        rgb.thumbnail((256, 256))
        buffer = io.BytesIO()
        rgb.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def generate(
    parts: list[dict],
    *,
    model: str | None = None,
    history: list[dict] | None = None,
    temperature: float = 0.0,
    max_tokens: int = 8192,
    timeout: float = 180,
    json_mode: bool = False,
    key: str | None = None,
) -> str:
    key = key or load_key()
    if not key:
        raise GeminiError("missing API key — add GOOGLE_API_KEY to .env")
    model = model or current_model()
    contents = list(history) if history else []
    contents.append({"role": "user", "parts": parts})

    config = {"temperature": temperature, "maxOutputTokens": max_tokens}
    if json_mode:
        config["responseMimeType"] = "application/json"

    response = _request(
        "post",
        f"{API_ROOT}/models/{model}:generateContent",
        params={"key": key},
        json={"contents": contents, "generationConfig": config},
        timeout=timeout,
    )
    _raise_for(response)
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise GeminiError("model returned an unexpected empty response")


def ask(
    prompt: str,
    image=None,
    *,
    history: list[dict] | None = None,
    **kwargs,
) -> str:
    parts: list[dict] = [{"text": prompt}]
    if image is not None:
        parts.append(
            {"inlineData": {"mimeType": "image/png", "data": encode_image(image)}}
        )
    return generate(parts, history=history, **kwargs)


def list_models(key: str | None = None) -> list[str]:
    key = key or load_key()
    if not key:
        raise GeminiError("missing API key — add GOOGLE_API_KEY to .env")
    response = _request(
        "get", f"{API_ROOT}/models", params={"key": key}, timeout=30
    )
    _raise_for(response)
    data = response.json()
    return [
        model.get("name", "").split("/")[-1]
        for model in data.get("models", [])
        if model.get("name")
    ]


def check_key(key: str | None = None) -> bool:
    key = key or load_key()
    if not key:
        raise GeminiError("missing API key — add GOOGLE_API_KEY to .env")
    response = _request(
        "get", f"{API_ROOT}/models", params={"key": key}, timeout=20
    )
    _raise_for(response)
    return True
