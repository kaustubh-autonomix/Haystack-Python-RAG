"""
Tenant-level monitoring utilities.
Tracks per-tenant ingestion count, query count, chunk volume, and timestamps.
"""

import json
import os
from datetime import datetime

MONITOR_FILE = os.path.join(os.path.dirname(__file__), "monitor_data.json")


def _load():
    if not os.path.exists(MONITOR_FILE):
        return {}
    with open(MONITOR_FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(MONITOR_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_ingestion(tenant_id: str, chunks: int, filename: str):
    data = _load()
    if tenant_id not in data:
        data[tenant_id] = {
            "ingestions": 0,
            "queries": 0,
            "chunks": 0,
            "last_ingest": None,
            "last_query": None,
            "jobs": {}
        }

    entry = data[tenant_id]
    entry["ingestions"] += 1
    entry["chunks"] += chunks
    entry["last_ingest"] = f"{datetime.utcnow().isoformat()} | {filename}"

    _save(data)


def log_query(tenant_id: str, query_text: str):
    data = _load()
    if tenant_id not in data:
        data[tenant_id] = {
            "ingestions": 0,
            "queries": 0,
            "chunks": 0,
            "last_ingest": None,
            "last_query": None,
            "jobs": {}
        }

    entry = data[tenant_id]
    entry["queries"] += 1
    entry["last_query"] = f"{datetime.utcnow().isoformat()} | {query_text[:80]}"

    _save(data)


def log_job_start(tenant_id: str, job_id: str, filename: str):
    data = _load()
    if tenant_id not in data:
        data[tenant_id] = {
            "ingestions": 0,
            "queries": 0,
            "chunks": 0,
            "last_ingest": None,
            "last_query": None,
            "jobs": {}
        }

    entry = data[tenant_id]
    if "jobs" not in entry:
        entry["jobs"] = {}

    entry["jobs"][job_id] = {
        "status": "running",
        "filename": filename,
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
        "error": None,
        "chunks": None,
    }

    _save(data)


def log_job_end(tenant_id: str, job_id: str, success: bool, error_message: str = None, chunks: int = None):
    data = _load()
    if tenant_id not in data or "jobs" not in data[tenant_id] or job_id not in data[tenant_id]["jobs"]:
        return

    job = data[tenant_id]["jobs"][job_id]
    job["finished_at"] = datetime.utcnow().isoformat()
    job["status"] = "completed" if success else "failed"
    job["error"] = error_message
    job["chunks"] = chunks

    _save(data)


def get_stats():
    return _load()