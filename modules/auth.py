from modules.tenant_manager import verify_tenant_credentials

def verify_tenant(tenant_id: str, password: str) -> bool:
    return verify_tenant_credentials(tenant_id, password)