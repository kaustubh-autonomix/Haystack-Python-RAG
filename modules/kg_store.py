"""
KG Store
Creates Weaviate schema for KG nodes & edges and stores extracted graphs.
"""

import weaviate
import os
from modules.store_weaviate import get_client


# ---------- SCHEMA CREATION ----------

def create_kg_schema():
    client = get_client()

    schema = client.schema.get()

    existing = [c["class"] for c in schema.get("classes", [])]

    if "KG_Node" not in existing:
        client.schema.create_class({
            "class": "KG_Node",
            "vectorizer": "none",
            "properties": [
                {"name": "node_id", "dataType": ["text"]},
                {"name": "label", "dataType": ["text"]},
                {"name": "type", "dataType": ["text"]},
                {"name": "tenant_id", "dataType": ["text"]},
                {"name": "kb_id", "dataType": ["text"]},
                {"name": "pdf_id", "dataType": ["text"]},
                {"name": "pdf_name", "dataType": ["text"]},
            ],
        })

    if "KG_Edge" not in existing:
        client.schema.create_class({
            "class": "KG_Edge",
            "vectorizer": "none",
            "properties": [
                {"name": "source", "dataType": ["text"]},
                {"name": "target", "dataType": ["text"]},
                {"name": "relation", "dataType": ["text"]},
                {"name": "tenant_id", "dataType": ["text"]},
                {"name": "kb_id", "dataType": ["text"]},
                {"name": "pdf_id", "dataType": ["text"]},
                {"name": "pdf_name", "dataType": ["text"]},
            ],
        })


# ---------- STORE KG DATA ----------

def store_kg(kg: dict, tenant_id: str, pdf_name: str, kb_id: str, pdf_id: str):
    """
    Stores nodes & edges in Weaviate for a given tenant and PDF.
    """
    client = get_client()
    create_kg_schema()

    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

    # Store nodes
    for n in nodes:
        data = {
            "node_id": n.get("id"),
            "label": n.get("label"),
            "type": n.get("type"),
            "tenant_id": tenant_id,
            "kb_id": kb_id,
            "pdf_id": pdf_id,
            "pdf_name": pdf_name,
        }
        client.data_object.create(data, class_name="KG_Node")

    # Store edges
    for e in edges:
        data = {
            "source": e.get("source"),
            "target": e.get("target"),
            "relation": e.get("relation"),
            "tenant_id": tenant_id,
            "kb_id": kb_id,
            "pdf_id": pdf_id,
            "pdf_name": pdf_name,
        }
        client.data_object.create(data, class_name="KG_Edge")

    return {"nodes": len(nodes), "edges": len(edges)}
