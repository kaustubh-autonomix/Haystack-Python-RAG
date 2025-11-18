"""
Ingestion pipeline: PDF → text → chunks → embeddings → Weaviate.
"""

from modules.pdf_reader import read_pdf
from modules.splitter import split_text
from modules.embedding_gemini import embed_texts
from modules.store_weaviate import create_schema, store_documents
from pipelines.monitor import log_ingestion
import os

def ingest_pdf(path: str, tenant_id: str, chunk_size: int = 800, overlap: int = 100):
    create_schema()
    full_text = read_pdf(path)
    chunks = split_text(full_text, chunk_size, overlap)
    embeddings = embed_texts(chunks)
    store_documents(chunks, embeddings, tenant_id)
    log_ingestion(tenant_id, len(chunks), os.path.basename(path))
    return {
        "chunks": len(chunks),
        "status": "ok"
    }