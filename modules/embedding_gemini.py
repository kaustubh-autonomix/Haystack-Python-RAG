"""

Gemini embeddings helper for Haystack-Python-RAG

Provides `embed_texts(texts, batch_size=32, concurrency=4)` which returns a
list of embeddings (list of floats) corresponding to `texts`.

Notes:
- Loads GEMINI_API_KEY from environment (python-dotenv is used by the project).
- Uses Google Generative Language REST endpoint for text-embedding-004.
- Uses a small concurrency pool to speed up many calls while keeping each
  request simple and robust (retries + backoff).
- Returns embeddings in the same order as input texts.

"""

from __future__ import annotations

import os
import time
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # do not raise here; let callers decide, but log prominently
    logger.warning("GEMINI_API_KEY is not set in environment. Set GEMINI_API_KEY in your .env or env vars.")

# Endpoint for single-text embedding requests
_EMBED_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"


def _embed_single(text: str, api_key: str, max_retries: int = 3, timeout: int = 60) -> List[float]:
    """Embed a single text using Gemini embedding endpoint with retries.

    Returns the embedding vector (list of floats). Raises RuntimeError on fatal failure.
    """
    url = f"{_EMBED_ENDPOINT}?key={api_key}"
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]},
    }

    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            # raise for HTTP errors
            r.raise_for_status()
            data = r.json()
            # Attempt to extract embedding in multiple possible shapes
            # Common: {"embedding": {"values": [...]}}
            if isinstance(data, dict):
                if "embedding" in data and isinstance(data["embedding"], dict):
                    vals = data["embedding"].get("values") or data["embedding"].get("values", [])
                    if vals:
                        return vals
                # some responses wrap under 'responses' or 'output'
                if "responses" in data and isinstance(data["responses"], list) and data["responses"]:
                    first = data["responses"][0]
                    if isinstance(first, dict) and "embedding" in first:
                        return first.get("embedding", {}).get("values", [])
                # fallback: try to find any list of floats in top-level keys
                for v in data.values():
                    if isinstance(v, dict) and "values" in v and isinstance(v["values"], list):
                        return v["values"]
            # If no embedding found, raise to trigger retry
            raise RuntimeError(f"No embedding found in response: {r.status_code} - {r.text}")
        except Exception as e:
            logger.debug(f"Embedding attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.exception("Embedding failed after retries.")
                raise
            time.sleep(backoff)
            backoff *= 2
    # Should not reach here
    raise RuntimeError("Embedding failed unexpectedly")


def embed_texts(texts: List[str], batch_size: int = 32, concurrency: int = 4, show_progress: bool = True) -> List[List[float]]:
    """Return embeddings for a list of texts.

    Implementation detail:
    - Breaks texts into batches of `batch_size` for nicer progress reporting.
    - Executes embedding requests with a ThreadPoolExecutor (`concurrency` workers).
    - Ensures output order matches input order.

    Note: Gemini embedding usage may be rate-limited; tune `concurrency` and
    `batch_size` accordingly.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    all_embeddings: List[Optional[List[float]]] = [None] * len(texts)

    # Helper to run embedding for a single index
    def _task(idx_text_pair):
        idx, txt = idx_text_pair
        emb = _embed_single(txt, GEMINI_API_KEY)
        return idx, emb

    # Build index-text pairs so we can place results in order
    indexed_texts = list(enumerate(texts))

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = {}
        # submit tasks in batches to avoid flooding API
        for i in range(0, len(indexed_texts), batch_size):
            batch = indexed_texts[i : i + batch_size]
            for pair in batch:
                fut = ex.submit(_task, pair)
                futures[fut] = pair[0]

            # optional progress
            if show_progress:
                for fut in tqdm(as_completed(list(futures.keys())), total=len(batch), desc="Embedding batch", leave=False):
                    idx, emb = fut.result()
                    all_embeddings[idx] = emb
                # clear futures for next batch
                futures = {}
            else:
                for fut in as_completed(list(futures.keys())):
                    idx, emb = fut.result()
                    all_embeddings[idx] = emb
                futures = {}

    # At this point, all_embeddings should be fully populated
    if any(x is None for x in all_embeddings):
        missing = [i for i, x in enumerate(all_embeddings) if x is None]
        raise RuntimeError(f"Embeddings missing for indices: {missing}")

    return all_embeddings  # type: ignore


if __name__ == "__main__":
    # quick local smoke test (requires GEMINI_API_KEY set)
    sample = ["Hello world", "The quick brown fox jumps over the lazy dog"]
    try:
        embs = embed_texts(sample, batch_size=2, concurrency=2)
        print(f"Got {len(embs)} embeddings; first dim={len(embs[0])}")
    except Exception as e:
        print("Embedding smoke test failed:", e)
