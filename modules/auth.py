

import json
import os

# Path to tenants.json stored at project root
TENANTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tenants.json")


def load_tenants():
    if not os.path.exists(TENANTS_FILE):
        return {}
    with open(TENANTS_FILE, "r") as f:
        return json.load(f)


def verify_tenant(tenant_id: str, password: str) -> bool:
    tenants = load_tenants()
    if tenant_id not in tenants:
        return False
    return tenants[tenant_id] == password