

"""
Weaviate readiness and auto-start helper.
Used to ensure local Weaviate (Docker) is running before pipeline starts.
"""

import subprocess
import time
import requests

WEAVIATE_PORT = 4560
WEAVIATE_URL = f"http://localhost:{WEAVIATE_PORT}"


def is_weaviate_ready():
    try:
        r = requests.get(f"{WEAVIATE_URL}/v1/.well-known/live", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def ensure_weaviate_running():
    # Check if container is running
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--filter", "name=weaviate", "--filter", "status=running", "--format", "{{.Names}}"],
            text=True,
        ).strip()
    except Exception:
        print("Docker not found or not available.")
        return False

    # If not running → start it
    if out != "weaviate":
        print("Starting Weaviate Docker container...")
        subprocess.run(
            [
                "docker", "run", "-d", "--name", "weaviate", "-p", f"{WEAVIATE_PORT}:8080",
                "semitechnologies/weaviate:1.24.8",
            ],
            check=False,
        )

    # Wait for readiness
    print("Waiting for Weaviate to become ready...")
    for _ in range(20):  # up to ~20 seconds
        if is_weaviate_ready():
            print("Weaviate is ready.")
            return True
        time.sleep(1)

    print("Weaviate did not start up in time.")
    return False