"""Thin wrapper over a persistent, embedded Chroma collection.

Embeddings are always computed by our own Embedder and passed in explicitly
(never Chroma's bundled default embedding function), so indexing and query
time always use the exact same model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rag.constants import CHROMA_COLLECTION_NAME


class ChromaStore:
    def __init__(self, persist_dir: str | Path, collection_name: str = CHROMA_COLLECTION_NAME) -> None:
        import chromadb

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not ids:
            return
        self._collection.upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        self._collection.delete(ids=ids)

    def query(
        self, embedding: list[float], k: int, where: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(k, self._collection.count()),
            where=where,
        )
        rows: list[dict[str, Any]] = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for i, doc, meta, dist in zip(ids, documents, metadatas, distances, strict=True):
            rows.append({"id": i, "document": doc, "metadata": meta, "score": 1.0 - dist})
        return rows

    def wipe(self) -> None:
        self._client.delete_collection(name=self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
