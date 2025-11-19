"""
CLI entrypoint for Haystack-Python-RAG.
Supports:
  python haystackapp.py                       → interactive mode
  python haystackapp.py --file doc.pdf        → ingest only
  python haystackapp.py --query "text"        → query only
  python haystackapp.py --file doc.pdf --query "text" → ingest + answer
"""

from modules.weaviate_check import ensure_weaviate_running

import argparse
import subprocess
from pipelines.ingestion import ingest_pdf
from pipelines.querying import answer_query
from pipelines.monitor import get_stats
import tkinter as tk
from tkinter import filedialog
from modules.tenant_manager import verify_tenant_credentials as verify_tenant
from modules.worker import start_worker, submit_job, get_job, list_jobs
from modules.knowledge_base_manager import create_kb, list_kb, set_active_kb, get_active_kb

CURRENT_TENANT = None


def interactive_loop():
    global CURRENT_TENANT
    if not CURRENT_TENANT:
        while True:
            tenant = input("Enter tenant id: ").strip()
            password = input("Enter password: ").strip()
            if verify_tenant(tenant, password):
                CURRENT_TENANT = tenant
                break
            else:
                print("Invalid tenant id or password. Try again.")

    # ALWAYS show KB selection menu after login
    print("""
============================
   Haystack RAG CLI
============================
Select or create a Knowledge Base.
Commands:
  createkb <name>
  listkb
  usekb <kb_id>
  deletekb <kb_id>
  exit
----------------------------
""")

    while True:
        cmd = input("kb > ").strip()
        if cmd == "exit":
            return
        elif cmd.startswith("createkb "):
            name = cmd.replace("createkb ", "", 1).strip()
            kb_id = create_kb(CURRENT_TENANT, name)
            set_active_kb(CURRENT_TENANT, kb_id)
            print(f"Knowledge Base created and set active: {kb_id}")
            break
        elif cmd == "listkb":
            kbs = list_kb(CURRENT_TENANT)
            for k, info in kbs.items():
                status = "(active)" if info.get("active") else ""
                print(f"{k}: {info['kb_name']} {status}")
        elif cmd.startswith("usekb "):
            kb_input = cmd.replace("usekb ", "", 1).strip()
            kbs = list_kb(CURRENT_TENANT)

            # Direct ID match
            if kb_input in kbs:
                if set_active_kb(CURRENT_TENANT, kb_input):
                    print(f"Switched to KB: {kb_input}")
                else:
                    print("Failed to switch KB.")
                break

            # Name match
            matched_id = None
            for kid, info in kbs.items():
                if info.get("kb_name", "").lower() == kb_input.lower():
                    matched_id = kid
                    break

            if matched_id:
                if set_active_kb(CURRENT_TENANT, matched_id):
                    print(f"Switched to KB: {matched_id}")
                    break
                else:
                    print("Failed to switch KB.")
            else:
                print("No KB found with that ID or name.")
        elif cmd.startswith("deletekb "):
            kb_id = cmd.replace("deletekb ", "", 1).strip()
            kbs = list_kb(CURRENT_TENANT)
            if kb_id in kbs:
                del kbs[kb_id]
                from modules.knowledge_base_manager import _save, _load
                data = _load()
                data[CURRENT_TENANT] = kbs
                _save(data)
                print(f"Deleted KB: {kb_id}")
            else:
                print("Invalid KB ID.")
        else:
            print("Commands: createkb <name>, listkb, usekb <kb_id>, deletekb <kb_id>, exit")

    print("""
============================
       Haystack RAG CLI
============================
Commands:
  ingest
  ask <your question>
  stats
  back
  exit
----------------------------
Enter command:
""")
    while True:
        cmd = input("insert your query here > ").strip()
        if cmd.lower() == "exit":
            break
        if cmd.startswith("ingest"):
            parts = cmd.split(" ", 1)
            if len(parts) == 1:
                root = tk.Tk()
                root.withdraw()
                path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
                root.destroy()
                if not path:
                    print("No file selected.")
                    continue
            else:
                path = parts[1].strip()

            print("Ingestion started...")
            print("Knowledge base formation started...")
            job_id = submit_job(path, CURRENT_TENANT)

            import time
            while True:
                job = get_job(job_id)
                if job and job.get("status") in ["completed", "failed"]:
                    break
                time.sleep(1)

            job = get_job(job_id)
            if job.get("status") == "completed":
                print("Ingestion completed successfully.")
                print("Knowledge base created.")
            else:
                print("INGESTION FAILED — RAW JOB:")
                print(job)
        elif cmd.startswith("ask "):
            q = cmd.replace("ask ", "", 1).strip()
            ans = answer_query(q, CURRENT_TENANT)
            print(ans)

        elif cmd == "back":
            # Jump back to KB menu instead of exiting
            return interactive_loop()

        elif cmd == "stats":
            stats = get_stats()
            if CURRENT_TENANT in stats:
                print(stats[CURRENT_TENANT])
            else:
                print("No stats for this tenant.")
        else:
            print("Commands: ingest <file>, ask <query>, exit")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None, help="PDF path to ingest")
    parser.add_argument("--query", type=str, default=None, help="Query to ask")
    args = parser.parse_args()

    ensure_weaviate_running()
    start_worker()

    global CURRENT_TENANT
    if not CURRENT_TENANT:
        while True:
            tenant = input("Enter tenant id: ").strip()
            password = input("Enter password: ").strip()
            if verify_tenant(tenant, password):
                CURRENT_TENANT = tenant
                break
            else:
                print("Invalid tenant id or password. Try again.")

    active = get_active_kb(CURRENT_TENANT)
    if not active:
        print("No active knowledge base. Please create one using createkb <name> in interactive mode.")

    if not args.file and not args.query:
        interactive_loop()
        return

    if args.file:
        result = ingest_pdf(args.file, CURRENT_TENANT)
        print(f"Ingested: {result['chunks']} chunks")
        print("Ingestion completed successfully.")
        print("Knowledge base created.")

    if args.query:
        ans = answer_query(args.query, CURRENT_TENANT)
        print(ans)


if __name__ == "__main__":
    main()
