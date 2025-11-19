"""
Background ingestion worker.
Handles job queue, job status, and async ingestion execution.
basic shabdo me ingestion thoda fast krta hai.

"""

import threading
import queue
import uuid
import time
from datetime import datetime
from pipelines.ingestion import do_ingest
from pipelines.monitor import log_job_start, log_job_end
from pipelines.monitor import log_ingestion

# Job queue
_JOB_QUEUE = queue.Queue()

# In-memory job registry
JOBS = {}


def _worker_loop():
    while True:
        job = _JOB_QUEUE.get()
        if job is None:
            break
        job_id = job["job_id"]
        tenant_id = job["tenant_id"]
        path = job["path"]

        JOBS[job_id]["status"] = "running"
        JOBS[job_id]["started_at"] = datetime.utcnow().isoformat()

        log_job_start(tenant_id, job_id, path)

        try:
            res = do_ingest(path, tenant_id)
            log_ingestion(tenant_id, res.get("chunks", 0), path)
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["finished_at"] = datetime.utcnow().isoformat()
            log_job_end(tenant_id, job_id, True, chunks=res.get("chunks", 0))
        except Exception as e:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(e)
            JOBS[job_id]["finished_at"] = datetime.utcnow().isoformat()
            log_job_end(tenant_id, job_id, False, error_message=str(e))

        _JOB_QUEUE.task_done()


_worker_thread = None


def start_worker():
    global _worker_thread
    if _worker_thread is None:
        _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
        _worker_thread.start()


def submit_job(path: str, tenant_id: str):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "tenant_id": tenant_id,
        "path": path,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "error": None,
    }
    _JOB_QUEUE.put({"job_id": job_id, "tenant_id": tenant_id, "path": path})
    return job_id


def get_job(job_id: str):
    return JOBS.get(job_id)


def list_jobs(tenant_id: str = None):
    if tenant_id:
        return [job for job in JOBS.values() if job["tenant_id"] == tenant_id]
    return list(JOBS.values())