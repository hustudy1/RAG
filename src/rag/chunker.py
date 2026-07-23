"""A small, dependency-free recursive text splitter.

Deliberately not a wrapper around langchain-text-splitters -- this is a
~60-line algorithm and doesn't warrant pulling in an extra dependency tree.
Splits on paragraph boundaries first, then falls back to lines, sentences,
words, and finally raw characters -- a single strategy that works reasonably
for both prose and source code.
"""

from __future__ import annotations

from rag.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE

_DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks of at most `chunk_size` characters."""
    if not text or not text.strip():
        return []
    pieces = _recursive_split(text, _DEFAULT_SEPARATORS, chunk_size)
    return _merge_with_overlap(pieces, chunk_size, chunk_overlap)


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Split text into pieces no longer than chunk_size, preferring earlier separators."""
    if len(text) <= chunk_size:
        return [text] if text else []
    if not separators:
        return [text]

    sep, *rest = separators

    if sep == "":
        # Last resort: raw character slicing guarantees termination.
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    if sep not in text:
        return _recursive_split(text, rest, chunk_size)

    parts = text.split(sep)
    pieces: list[str] = []
    for i, part in enumerate(parts):
        # Re-append the separator (except after the last part) to preserve
        # the original text's structure in the resulting chunks.
        piece = part + sep if i < len(parts) - 1 else part
        if not piece:
            continue
        if len(piece) <= chunk_size:
            pieces.append(piece)
        else:
            pieces.extend(_recursive_split(piece, rest, chunk_size))
    return pieces


def _merge_with_overlap(
    pieces: list[str], chunk_size: int, chunk_overlap: int
) -> list[str]:
    """Greedily pack small pieces into chunks up to chunk_size, carrying overlap."""
    if not pieces:
        return []

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) > chunk_size:
            chunks.append(current)
            overlap_text = current[-chunk_overlap:] if chunk_overlap > 0 else ""
            current = overlap_text + piece
        else:
            current += piece
    if current.strip():
        chunks.append(current)
    return [c for c in chunks if c.strip()]
