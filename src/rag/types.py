"""Public data types returned by the rag package."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    """A single retrieved piece of text with its provenance and relevance score."""

    text: str
    source_path: str
    relative_path: str
    chunk_index: int
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BuildStats:
    """Counts describing what a build()/refresh() call did."""

    added: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    total_chunks: int = 0


@dataclass(frozen=True)
class Answer:
    """Result of RAGIndex.answer(): a generated answer plus the chunks it cited."""

    text: str
    chunks: list[Chunk]
