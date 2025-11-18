"""
Gemini text-generation helper provides generate_answer(prompt) → string.
"""

import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment.")

_GEN_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)


def generate_answer(prompt: str, max_tokens: int = 512) -> str:
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.2
        }
    }

    attempts = 3
    for attempt in range(attempts):
        try:
            r = requests.post(_GEN_URL, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0].get("text", "")
        except Exception as e:
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
            return f"Gemini API error: {str(e)}"
