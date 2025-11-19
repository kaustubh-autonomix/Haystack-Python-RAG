"""
Ingestion pipeline: PDF → text → chunks → embeddings → Weaviate.
"""

from modules.pdf_reader import read_pdf
from modules.splitter import split_text
from modules.embedding_gemini import embed_texts
from modules.store_weaviate import create_schema, store_documents
from pipelines.monitor import log_ingestion
import os
from modules.kg_extractor import extract_kg
from modules.kg_store import store_kg
from modules.knowledge_base_manager import get_active_kb, generate_pdf_id

def do_ingest(path: str, tenant_id: str, chunk_size: int = 800, overlap: int = 100):
    create_schema()
    kb_id = get_active_kb(tenant_id)
    if kb_id is None:
        raise Exception("No active Knowledge Base selected. Create or activate a KB first.")

    pdf_id = generate_pdf_id()

    full_text = read_pdf(path)
    chunks = split_text(full_text, chunk_size, overlap)
    embeddings = embed_texts(chunks)
    store_documents(chunks, embeddings, tenant_id, kb_id=kb_id, pdf_id=pdf_id)
    # Knowledge Graph extraction
    pdf_name = os.path.basename(path)
    kg = extract_kg(full_text)
    kg_result = store_kg(kg, tenant_id, pdf_name, kb_id=kb_id, pdf_id=pdf_id)
    return {
        "chunks": len(chunks),
        "kb_id": kb_id,
        "pdf_id": pdf_id,
        "kg_nodes": kg_result.get("nodes", 0),
        "kg_edges": kg_result.get("edges", 0),
        "status": "ok"
    }

def ingest_pdf(path: str, tenant_id: str, chunk_size: int = 800, overlap: int = 100):
    res = do_ingest(path, tenant_id, chunk_size, overlap)
    log_ingestion(tenant_id, res["chunks"], os.path.basename(path), kb_id=res["kb_id"], pdf_id=res["pdf_id"])
    return res