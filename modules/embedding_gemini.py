"""
Minimal Gemini embedding helper for Haystack-Python-RAG.
Provides embed_texts(texts) → list of embedding vectors.
"""

import os
import logging
import requests
from dotenv import load_dotenv
from typing import List

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment.")

# Gemini embedding endpoint
_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "text-embedding-004:embedContent?key=" + GEMINI_API_KEY
)


def _embed_single(text: str) -> List[float]:
    """Embed a single text. Lightweight, no retries."""
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]},
    }

    r = requests.post(_EMBED_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Standard Gemini embedding format
    if "embedding" in data:
        return data["embedding"].get("values", [])

    # Fallback (rare)
    if "responses" in data and isinstance(data["responses"], list):
        emb = data["responses"][0].get("embedding", {}).get("values", [])
        return emb

    raise RuntimeError(f"Unexpected embedding response: {data}")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts sequentially (simple + predictable)."""
    embeddings = []
    for t in texts:
        emb = _embed_single(t)
        embeddings.append(emb)
    return embeddings
