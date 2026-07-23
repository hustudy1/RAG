"""Walks an arbitrary source directory and yields loadable document text.

Never raises on a single bad file — a corrupt PDF, a binary file with a text
extension, or an encoding error should only cause that one file to be
skipped, not abort indexing of the rest of the folder.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from rag.constants import (
    DEFAULT_IGNORE_DIRS,
    DEFAULT_MAX_FILE_SIZE_BYTES,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
)

logger = logging.getLogger(__name__)


def _is_probably_binary(path: Path) -> bool:
    """Cheap binary sniff: read a small prefix and look for a NUL byte."""
    try:
        with path.open("rb") as f:
            prefix = f.read(8192)
    except OSError:
        return True
    return b"\x00" in prefix


def _load_text_file(path: Path) -> str | None:
    if _is_probably_binary(path):
        logger.debug("skipping binary-looking file with text extension: %s", path)
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.debug("failed to read file even with errors=replace: %s", path)
            return None
    except OSError:
        logger.debug("failed to read file: %s", path)
        return None


def _load_pdf_file(path: Path) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover - pypdf is a core dependency
        logger.warning("pypdf not installed; skipping PDF file: %s", path)
        return None

    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001 - a single bad page must not abort the file
                logger.debug("failed to extract text from a page in: %s", path)
        text = "\n\f\n".join(pages)
        return text if text.strip() else None
    except Exception:  # noqa: BLE001 - corrupt/encrypted PDFs must not crash the walk
        logger.debug("failed to read PDF: %s", path)
        return None


def _should_prune_dir(name: str, ignore_patterns: set[str]) -> bool:
    if name in ignore_patterns:
        return True
    return name.startswith(".")


def iter_documents(
    source_dir: str | Path,
    ignore_patterns: set[str] | None = None,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    exclude_dirs: set[Path] | None = None,
) -> Iterator[tuple[Path, str, dict[str, Any]]]:
    """Walk source_dir and yield (absolute_path, text, metadata) for each loadable file.

    metadata contains: file_type (extension without the dot), mtime, size.

    `exclude_dirs` prunes specific absolute directory paths regardless of
    name -- used to keep an index's own persist_dir out of its source walk
    when a caller points persist_dir inside source_dir.
    """
    source_dir = Path(source_dir).resolve()
    patterns = set(DEFAULT_IGNORE_DIRS)
    if ignore_patterns:
        patterns |= ignore_patterns
    excluded = {Path(p).resolve() for p in (exclude_dirs or set())}

    for root, dirnames, filenames in os.walk(source_dir):
        root_path = Path(root)
        # Prune in place so os.walk doesn't descend into ignored directories.
        dirnames[:] = [
            d
            for d in dirnames
            if not _should_prune_dir(d, patterns) and (root_path / d).resolve() not in excluded
        ]

        for filename in filenames:
            path = root_path / filename
            ext = path.suffix.lower()

            if ext not in TEXT_EXTENSIONS and ext not in PDF_EXTENSIONS:
                continue

            try:
                stat = path.stat()
            except OSError:
                continue

            if stat.st_size > max_file_size_bytes:
                logger.debug("skipping oversized file (%d bytes): %s", stat.st_size, path)
                continue
            if stat.st_size == 0:
                continue

            if ext in PDF_EXTENSIONS:
                text = _load_pdf_file(path)
            else:
                text = _load_text_file(path)

            if not text or not text.strip():
                continue

            metadata: dict[str, Any] = {
                "file_type": ext.lstrip("."),
                "mtime": stat.st_mtime,
                "size": stat.st_size,
            }
            yield path, text, metadata
