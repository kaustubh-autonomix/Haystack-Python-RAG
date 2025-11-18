"""
Tenant Manager Module
Manages tenant creation, deletion, password updates, and listing.
Backed by a simple JSON file.
"""

import json
import os

# Path to the tenant storage JSON file
tenant_store_file = os.path.join(os.path.dirname(__file__), "tenants_store.json")


def _load():
    if not os.path.exists(tenant_store_file):
        return {}
    with open(tenant_store_file, "r") as f:
        return json.load(f)


def _save(data):
    with open(tenant_store_file, "w") as f:
        json.dump(data, f, indent=2)


def create_tenant(tenant_id: str, password: str) -> bool:
    """
    Returns True if created successfully, False if tenant already exists.
    """
    tenants = _load()
    if tenant_id in tenants:
        return False

    tenants[tenant_id] = {
        "password": password,
        "active": True
    }
    _save(tenants)
    return True


def delete_tenant(tenant_id: str) -> bool:
    """
    Returns True if tenant existed and was deleted.
    """
    tenants = _load()
    if tenant_id not in tenants:
        return False

    del tenants[tenant_id]
    _save(tenants)
    return True


def update_password(tenant_id: str, new_password: str) -> bool:
    tenants = _load()
    if tenant_id not in tenants:
        return False

    tenants[tenant_id]["password"] = new_password
    _save(tenants)
    return True


def list_tenants():
    tenants = _load()
    return list(tenants.keys())


def verify_tenant_credentials(tenant_id: str, password: str) -> bool:
    tenants = _load()
    if tenant_id not in tenants:
        return False
    return tenants[tenant_id]["password"] == password


if __name__ == "__main__":
    print("\n===== Tenant Manager CLI =====")
    print("1. Create Tenant")
    print("2. Delete Tenant")
    print("3. Update Tenant Password")
    print("4. List Tenants")
    print("5. Exit")

    while True:
        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            tenant_id = input("Enter new tenant id: ").strip()
            password = input("Enter password: ").strip()
            if create_tenant(tenant_id, password):
                print("Tenant created successfully.")
            else:
                print("Tenant already exists.")

        elif choice == "2":
            tenant_id = input("Enter tenant id to delete: ").strip()
            if delete_tenant(tenant_id):
                print("Tenant deleted.")
            else:
                print("Tenant not found.")

        elif choice == "3":
            tenant_id = input("Enter tenant id: ").strip()
            new_pw = input("Enter new password: ").strip()
            if update_password(tenant_id, new_pw):
                print("Password updated.")
            else:
                print("Tenant not found.")

        elif choice == "4":
            tenants = list_tenants()
            if tenants:
                print("\nRegistered Tenants:")
                for t in tenants:
                    print(" -", t)
            else:
                print("No tenants found.")

        elif choice == "5":
            print("Exiting Tenant Manager.")
            break

        else:
            print("Invalid option. Please choose between 1-5.")