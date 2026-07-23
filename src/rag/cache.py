"""Resolves where a source directory's persisted index lives.

Defaults to a central cache directory (~/.cache/rag_lib/<hash>) keyed by a
hash of the resolved source path, rather than an in-folder .rag_index/ --
the source folder may be read-only, someone else's codebase, or under
version control where an accidental cache-dir commit is an easy foot-gun.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rag.constants import CACHE_DIR_NAME


def _cache_root() -> Path:
    return Path.home() / ".cache" / CACHE_DIR_NAME


def resolve_persist_dir(source_dir: str | Path) -> Path:
    resolved = Path(source_dir).resolve()
    key = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:16]
    persist_dir = _cache_root() / key
    persist_dir.mkdir(parents=True, exist_ok=True)

    # Purely for human debugging -- lets you find which folder a cache entry
    # under ~/.cache/rag_lib belongs to.
    origin_file = persist_dir / "source.json"
    if not origin_file.exists():
        origin_file.write_text(
            json.dumps({"source_dir": str(resolved)}, indent=2), encoding="utf-8"
        )

    return persist_dir
