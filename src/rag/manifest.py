"""Per-file manifest tracking what's currently indexed, driving incremental refresh().

The manifest maps a file's path (relative to source_dir) to its last-seen
mtime/size (a cheap pre-check), a content hash (the real "did this change"
signal -- guards against a `touch` bumping mtime with no content change),
and the list of chunk ids currently stored for that file (so a shrinking
file's now-stale trailing chunks can be deleted precisely).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict

from rag.constants import MANIFEST_FILENAME


class FileRecord(TypedDict):
    mtime: float
    size: int
    content_hash: str
    chunk_ids: list[str]


Manifest = dict[str, FileRecord]


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(persist_dir: str | Path) -> Manifest:
    path = Path(persist_dir) / MANIFEST_FILENAME
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save(persist_dir: str | Path, manifest: Manifest) -> None:
    path = Path(persist_dir) / MANIFEST_FILENAME
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def exists(persist_dir: str | Path) -> bool:
    return (Path(persist_dir) / MANIFEST_FILENAME).exists()


def chunk_id_for(relative_path: str, chunk_index: int) -> str:
    prefix = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}::{chunk_index}"


def is_unchanged(record: FileRecord | None, mtime: float, size: int) -> bool:
    """Fast pre-check: True if mtime/size match the manifest, no hashing needed."""
    if record is None:
        return False
    return record["mtime"] == mtime and record["size"] == size


def has_same_content(record: FileRecord | None, text: str) -> bool:
    """Real check: True if the file's actual content hash matches the manifest."""
    if record is None:
        return False
    return record["content_hash"] == content_hash(text)
