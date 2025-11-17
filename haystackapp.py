"""
CLI entrypoint for Haystack-Python-RAG.
Supports:
  python haystackapp.py                  → interactive mode
  python haystackapp.py --file doc.pdf   → ingest only
  python haystackapp.py --query "text"   → query only
  python haystackapp.py --file doc.pdf --query "text" → ingest + answer
"""

import argparse
from pipelines.ingestion import ingest_pdf
from pipelines.querying import answer_query


def interactive_loop():
    print("Haystack RAG CLI (type 'exit' to quit)")
    while True:
        cmd = input("> ").strip()
        if cmd.lower() == "exit":
            break
        if cmd.startswith("ingest "):
            path = cmd.replace("ingest ", "", 1).strip()
            result = ingest_pdf(path)
            print(f"Ingested: {result['chunks']} chunks")
        elif cmd.startswith("ask "):
            q = cmd.replace("ask ", "", 1).strip()
            ans = answer_query(q)
            print(ans)
        else:
            print("Commands: ingest <file>, ask <query>, exit")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None, help="PDF path to ingest")
    parser.add_argument("--query", type=str, default=None, help="Query to ask")
    args = parser.parse_args()

    if not args.file and not args.query:
        interactive_loop()
        return

    if args.file:
        result = ingest_pdf(args.file)
        print(f"Ingested: {result['chunks']} chunks")

    if args.query:
        ans = answer_query(args.query)
        print(ans)


if __name__ == "__main__":
    main()
