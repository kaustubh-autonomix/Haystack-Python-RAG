"""
Query pipeline: query → embedding → vector search → LLM answer.
"""

from modules.embedding_gemini import embed_texts
from modules.store_weaviate import query_embeddings
from modules.generator_gemini import generate_answer


def answer_query(query: str, top_k: int = 5) -> str:
    q_emb = embed_texts([query])[0]
    hits = query_embeddings(q_emb, top_k=top_k)

    context = "\n".join([h.get("text", "") for h in hits])

    prompt = f"Use the context below to answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"

    return generate_answer(prompt)
