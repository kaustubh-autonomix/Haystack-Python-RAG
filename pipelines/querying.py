"""
Query pipeline: query → embedding → vector search → LLM answer.
"""

from modules.embedding_gemini import embed_texts
from modules.store_weaviate import query_embeddings
from modules.generator_gemini import generate_answer
from pipelines.monitor import log_query
from modules.store_weaviate import get_client


def query_kg(term: str, tenant_id: str) -> str:
    client = get_client()

    # Semantic search for KG_Node
    node_res = (
        client.query.get("KG_Node", ["node_id", "label", "type"])
        .with_where({
            "path": ["tenant_id"],
            "operator": "Equal",
            "valueString": tenant_id,
        })
        .with_near_text({"concepts": [term]})
        .with_limit(5)
        .do()
    )

    nodes = node_res.get("data", {}).get("Get", {}).get("KG_Node", [])

    if not nodes:
        return "No KG information found for this term."

    node_lines = [f"Node: {n.get('label')} (id={n.get('node_id')})" for n in nodes]

    # Fetch edges for each node
    edge_lines = []
    for n in nodes:
        nid = n.get("node_id")

        edge_res = (
            client.query.get("KG_Edge", ["source", "target", "relation"])
            .with_where({
                "operator": "And",
                "operands": [
                    {
                        "path": ["tenant_id"],
                        "operator": "Equal",
                        "valueString": tenant_id,
                    },
                    {
                        "operator": "Or",
                        "operands": [
                            {
                                "path": ["source"],
                                "operator": "Equal",
                                "valueString": nid,
                            },
                            {
                                "path": ["target"],
                                "operator": "Equal",
                                "valueString": nid,
                            },
                        ],
                    },
                ],
            })
            .do()
        )

        edges = edge_res.get("data", {}).get("Get", {}).get("KG_Edge", [])

        for e in edges:
            edge_lines.append(
                f"{e.get('source')} -[{e.get('relation')}]-> {e.get('target')}"
            )

    return "\n".join(node_lines + edge_lines)


def answer_query(query: str, tenant_id: str, top_k: int = 5) -> str:
    if query.lower().startswith("kg "):
        term = query[3:].strip()
        return query_kg(term, tenant_id)

    q_emb = embed_texts([query])[0]

    hits = query_embeddings(q_emb, top_k=top_k, tenant_id=tenant_id)

    context = "\n".join([h.get("text", "") for h in hits])

    prompt = f"Use the context below to answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"

    log_query(tenant_id, query)
    return generate_answer(prompt)
