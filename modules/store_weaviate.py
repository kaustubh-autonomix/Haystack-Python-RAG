

"""
Minimal local Weaviate store helper for Haystack-Python-RAG.
Provides create_schema(), store_documents(docs), and query_embeddings().
"""

import os
import weaviate
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

client = weaviate.Client(url=WEAVIATE_URL)

CLASS_NAME = "DocumentChunk"


def create_schema():
    if client.schema.contains(CLASS_NAME):
        return

    schema = {
        "classes": [
            {
                "class": CLASS_NAME,
                "vectorizer": "none",
                "properties": [
                    {"name": "text", "dataType": ["text"]},
                ],
            }
        ]
    }

    client.schema.create(schema)


def store_documents(chunks: List[str], embeddings: List[List[float]]):
    with client.batch as batch:
        for txt, emb in zip(chunks, embeddings):
            batch.add_data_object(
                data_object={"text": txt},
                class_name=CLASS_NAME,
                vector=emb,
            )


def query_embeddings(query_emb: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    result = (
        client.query
        .get(CLASS_NAME, ["text"])
        .with_near_vector({"vector": query_emb})
        .with_limit(top_k)
        .do()
    )

    return result.get("data", {}).get("Get", {}).get(CLASS_NAME, [])