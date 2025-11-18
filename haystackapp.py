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
    print("""
============================
       Haystack RAG CLI
============================
Commands:
  ingest 
  ask <your question>
  stats
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

            result = ingest_pdf(path, CURRENT_TENANT)
            print(f"Ingested: {result['chunks']} chunks")
        elif cmd.startswith("ask "):
            q = cmd.replace("ask ", "", 1).strip()
            ans = answer_query(q, CURRENT_TENANT)
            print(ans)
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

    if not args.file and not args.query:
        interactive_loop()
        return

    if args.file:
        result = ingest_pdf(args.file, CURRENT_TENANT)
        print(f"Ingested: {result['chunks']} chunks")

    if args.query:
        ans = answer_query(args.query, CURRENT_TENANT)
        print(ans)


if __name__ == "__main__":
    main()
