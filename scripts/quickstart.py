#!/usr/bin/env python3
"""Manual end-to-end demo of the rag library.

Usage:
    uv run python scripts/quickstart.py --source <folder> --query "<question>" [--k N] [--answer]

Indexes --source (incrementally, so re-running is cheap), then prints the
top-k retrieved chunks. With --answer and ANTHROPIC_API_KEY set, also asks
Claude to generate a cited answer from those chunks.
"""

from __future__ import annotations

import argparse
import sys

from rag import RAGIndex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Folder to index")
    parser.add_argument("--query", required=True, help="Question to search for")
    parser.add_argument("--k", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument(
        "--answer",
        action="store_true",
        help="Also generate a cited answer via Claude (requires rag[answer] + ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

    index = RAGIndex(source_dir=args.source)
    stats = index.refresh()
    print(
        f"[index] added={stats.added} updated={stats.updated} "
        f"deleted={stats.deleted} unchanged={stats.unchanged} "
        f"total_chunks={stats.total_chunks}",
        file=sys.stderr,
    )

    chunks = index.search(args.query, k=args.k)
    if not chunks:
        print("No results.")
        return 0

    print(f"\nTop {len(chunks)} result(s) for: {args.query!r}\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"--- [{i}] {chunk.relative_path} (score={chunk.score:.3f}) ---")
        print(chunk.text.strip())
        print()

    if args.answer:
        print("=== Answer ===\n")
        answer = index.answer(args.query, k=args.k)
        print(answer.text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
