"""
KG Extractor this is just the extractor file
Uses Gemini to extract nodes & edges from full PDF text.
"""

import os
import google.generativeai as genai

KG_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["id", "label", "type"]
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "relation": {"type": "string"}
                },
                "required": ["source", "target", "relation"]
            }
        }
    },
    "required": ["nodes", "edges"]
}

# Configuration of Gemini client
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
MODEL = "models/gemini-2.5-flash"


def extract_kg(full_text: str) -> dict:

    prompt = """
You are a Knowledge Graph extraction engine.

Extract a clean Knowledge Graph from the FULL DOCUMENT TEXT below.
Identify all important entities (nodes) and meaningful relationships (edges).

### OUTPUT REQUIREMENTS
Return ONLY a valid JSON object in the following format:

{
  "nodes": [
    {"id": "unique_node_id", "label": "Readable Name", "type": "Category"}
  ],
  "edges": [
    {"source": "node_id", "target": "node_id", "relation": "relationship_type"}
  ]
}

### RULES
- The JSON MUST be valid.
- Use short unique node IDs (e.g., n1, n2, n3).
- Do NOT include explanations or markdown.
- If unsure about a relationship, omit it.
- Merge duplicate entities into a single node.

### DOCUMENT TEXT
-----------------{}
"""

    import re, json
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt.format(full_text))
        raw = response.text.strip()
    except Exception as e:
        raise RuntimeError("Gemini KG extraction failed: {}".format(e))

    # Extract JSON fragments for nodes and edges
    nodes_match = re.search(r'"nodes"\s*:\s*(\[[\s\S]*?\])', raw)
    edges_match = re.search(r'"edges"\s*:\s*(\[[\s\S]*?\])', raw)

    if not nodes_match or not edges_match:
        raise RuntimeError("Could not extract nodes/edges arrays from Gemini output: {}".format(raw[:200]))

    try:
        nodes = json.loads(nodes_match.group(1))
        edges = json.loads(edges_match.group(1))
    except Exception as e:
        raise RuntimeError("Failed to parse nodes/edges arrays: {}".format(e))

    return {"nodes": nodes, "edges": edges}
