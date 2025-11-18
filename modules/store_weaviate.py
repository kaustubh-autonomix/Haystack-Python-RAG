"""
local Weaviate store helper,
This Provides create_schema(), store_documents(docs), and query_embeddings().
"""

import os
import weaviate
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
_client = None

def get_client():
    global _client
    if _client is None:
        _client = weaviate.Client(url=WEAVIATE_URL)
    return _client

CLASS_NAME = "DocumentChunk"

def create_schema():
    client = get_client()
    existing = client.schema.get()
    classes = [c["class"] for c in existing.get("classes", [])]
    if CLASS_NAME in classes:
        return

    schema = {
        "classes": [
            {
                "class": CLASS_NAME,
                "vectorizer": "none",
                "properties": [
                    {"name": "text", "dataType": ["text"]},
                    {"name": "tenant_id", "dataType": ["string"]},
                ],
            }
        ]
    }

    client.schema.create(schema)


def store_documents(chunks: List[str], embeddings: List[List[float]], tenant_id: str):
    client = get_client()
    with client.batch as batch:
        for txt, emb in zip(chunks, embeddings):
            batch.add_data_object(
                data_object={"text": txt, "tenant_id": tenant_id},
                class_name=CLASS_NAME,
                vector=emb,
            )


def query_embeddings(query_emb: List[float], top_k: int = 5, tenant_id:str = None) -> List[Dict[str, Any]]:
    client = get_client()
    q = (
        client.query
        .get(CLASS_NAME, ["text"])
        .with_near_vector({"vector": query_emb})
        .with_limit(top_k)
    )

    if tenant_id:
        q = q.with_where({
            "path": ["tenant_id"],
            "operator": "Equal",
            "valueString": tenant_id
        })

    result = q.do()
    return result.get("data", {}).get("Get", {}).get(CLASS_NAME, [])