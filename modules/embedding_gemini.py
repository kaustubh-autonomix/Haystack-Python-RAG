"""
this file is for embed_texts(texts) → list of embedding vectors.
helps in embedding text through gemini
"""

import os
import logging
import requests
from dotenv import load_dotenv
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]},
    }

    r = requests.post(_EMBED_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    if "embedding" in data:
        return data["embedding"].get("values", [])

    # Fallback (rare fir bhi kabhi hua toh)
    if "responses" in data and isinstance(data["responses"], list):
        emb = data["responses"][0].get("embedding", {}).get("values", [])
        return emb

    raise RuntimeError(f"Unexpected embedding response: {data}")

def _embed_parallel(texts: List[str], workers: int = 4) -> List[List[float]]:
    embeddings = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_embed_single, texts[i]): i for i in range(len(texts))}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                embeddings[idx] = fut.result()
            except Exception as e:
                raise RuntimeError(f"Embedding failed for chunk {idx}: {e}")
    return embeddings

def embed_texts(texts: List[str]) -> List[List[float]]:
    return _embed_parallel(texts, workers=4)
