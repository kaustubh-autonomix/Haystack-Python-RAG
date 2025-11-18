"""
Query pipeline: query → embedding → vector search → LLM answer.
"""

from modules.embedding_gemini import embed_texts
from modules.store_weaviate import query_embeddings
from modules.generator_gemini import generate_answer
from pipelines.monitor import log_query


def answer_query(query: str, tenant_id: str, top_k: int = 5) -> str:
    q_emb = embed_texts([query])[0]

    hits = query_embeddings(q_emb, top_k=top_k, tenant_id=tenant_id)

    context = "\n".join([h.get("text", "") for h in hits])

    prompt = f"Use the context below to answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"

    log_query(tenant_id, query)
    return generate_answer(prompt)
