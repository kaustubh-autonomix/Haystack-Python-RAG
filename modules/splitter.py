

"""
Minimal text splitter for Haystack-Python-RAG.
Provides split_text(text, chunk_size, overlap).
"""


def split_text(text: str, chunk_size: int = 800, overlap: int = 100):
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0

    return chunks