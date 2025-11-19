import json
import os
import uuid

KB_FILE = "knowledge_bases.json"

# Load or init KB store
def _load():
    if not os.path.exists(KB_FILE):
        with open(KB_FILE, "w") as f:
            json.dump({}, f, indent=2)
    with open(KB_FILE, "r") as f:
        return json.load(f)

# Save KB stores
def _save(data):
    with open(KB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Create a KB for a tenant
def create_kb(tenant_id: str, kb_name: str) -> str:
    data = _load()
    kb_id = str(uuid.uuid4())

    if tenant_id not in data:
        data[tenant_id] = {}

    data[tenant_id][kb_id] = {
        "kb_name": kb_name,
        "active": False
    }

    _save(data)
    return kb_id

# List KBs for a tenant
def list_kb(tenant_id: str):
    data = _load()
    return data.get(tenant_id, {})

# Set an active KB
def set_active_kb(tenant_id: str, kb_id: str):
    data = _load()
    if tenant_id not in data or kb_id not in data[tenant_id]:
        return False

    for k in data[tenant_id]:
        data[tenant_id][k]["active"] = False

    data[tenant_id][kb_id]["active"] = True
    _save(data)
    return True

# Get active KB id
def get_active_kb(tenant_id: str) -> str | None:
    data = _load()
    if tenant_id not in data:
        return None
    for kb_id, info in data[tenant_id].items():
        if info.get("active"):
            return kb_id
    return None

# Generate a PDF ID for each ingested document
def generate_pdf_id() -> str:
    return str(uuid.uuid4())
