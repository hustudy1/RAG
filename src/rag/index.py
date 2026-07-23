"""RAGIndex -- the public entry point tying loader + chunker + embedder + store
+ manifest together into build()/refresh()/search()/answer().
"""

from __future__ import annotations

from pathlib import Path

from rag import chunker, loader, manifest
from rag.cache import resolve_persist_dir
from rag.constants import (
    CHROMA_COLLECTION_NAME,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MAX_FILE_SIZE_BYTES,
)
from rag.embeddings import Embedder
from rag.store import ChromaStore
from rag.types import Answer, BuildStats, Chunk


class RAGIndex:
    """A searchable, incrementally-updated index over an arbitrary source folder.

    Usage:
        index = RAGIndex(source_dir="/path/to/any/folder")
        index.build()                       # first-time full index
        index.refresh()                     # incremental re-index on later runs
        chunks = index.search("query", k=5)
        answer = index.answer("query")      # optional; requires rag[answer]
    """

    def __init__(
        self,
        source_dir: str | Path,
        persist_dir: str | Path | None = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        collection_name: str = CHROMA_COLLECTION_NAME,
        ignore_patterns: set[str] | None = None,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        self.source_dir = Path(source_dir).resolve()
        self.persist_dir = (
            Path(persist_dir).resolve() if persist_dir else resolve_persist_dir(self.source_dir)
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        self.ignore_patterns = ignore_patterns
        self.max_file_size_bytes = max_file_size_bytes
        self._embedding_model_name = embedding_model

        self._embedder: Embedder | None = None
        self._store: ChromaStore | None = None

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder(self._embedding_model_name)
        return self._embedder

    @property
    def store(self) -> ChromaStore:
        if self._store is None:
            self._store = ChromaStore(self.persist_dir, self.collection_name)
        return self._store

    def build(self, force: bool = False) -> BuildStats:
        """First-time index build.

        If a manifest already exists and force=False, this is a no-op --
        use refresh() for subsequent runs. If force=True, wipes the
        collection and manifest and rebuilds from scratch.
        """
        manifest_exists = manifest.exists(self.persist_dir)
        if manifest_exists and not force:
            return BuildStats()
        if manifest_exists and force:
            self.store.wipe()
            manifest.save(self.persist_dir, {})
        return self._reindex()

    def refresh(self) -> BuildStats:
        """Incremental re-index: only processes added/modified/deleted files.

        Safe to call on a never-built index -- behaves like build() then.
        """
        return self._reindex()

    def _reindex(self) -> BuildStats:
        old_manifest = manifest.load(self.persist_dir)
        new_manifest: manifest.Manifest = {}
        seen_paths: set[str] = set()

        added = updated = unchanged = 0
        ids_to_delete: list[str] = []
        ids_to_upsert: list[str] = []
        embeddings_to_upsert: list[list[float]] = []
        documents_to_upsert: list[str] = []
        metadatas_to_upsert: list[dict] = []

        for path, text, meta in loader.iter_documents(
            self.source_dir,
            self.ignore_patterns,
            self.max_file_size_bytes,
            exclude_dirs={self.persist_dir},
        ):
            rel_path = str(path.relative_to(self.source_dir))
            seen_paths.add(rel_path)
            old_record = old_manifest.get(rel_path)

            if manifest.is_unchanged(old_record, meta["mtime"], meta["size"]):
                new_manifest[rel_path] = old_record  # type: ignore[assignment]
                unchanged += 1
                continue

            if manifest.has_same_content(old_record, text):
                # mtime/size changed (e.g. a touch) but content is identical.
                new_manifest[rel_path] = {
                    **old_record,  # type: ignore[dict-item]
                    "mtime": meta["mtime"],
                    "size": meta["size"],
                }
                unchanged += 1
                continue

            if old_record is not None:
                ids_to_delete.extend(old_record["chunk_ids"])
                updated += 1
            else:
                added += 1

            chunks = chunker.chunk_text(text, self.chunk_size, self.chunk_overlap)
            chunk_ids = [manifest.chunk_id_for(rel_path, i) for i in range(len(chunks))]
            if chunks:
                vectors = self.embedder.encode(chunks)
                for cid, chunk, vector in zip(chunk_ids, chunks, vectors, strict=True):
                    ids_to_upsert.append(cid)
                    embeddings_to_upsert.append(vector)
                    documents_to_upsert.append(chunk)
                    metadatas_to_upsert.append(
                        {
                            "source_path": str(path),
                            "relative_path": rel_path,
                            "file_type": meta["file_type"],
                        }
                    )

            new_manifest[rel_path] = {
                "mtime": meta["mtime"],
                "size": meta["size"],
                "content_hash": manifest.content_hash(text),
                "chunk_ids": chunk_ids,
            }

        deleted = 0
        for rel_path, record in old_manifest.items():
            if rel_path not in seen_paths:
                ids_to_delete.extend(record["chunk_ids"])
                deleted += 1

        if ids_to_delete:
            self.store.delete(ids_to_delete)
        if ids_to_upsert:
            self.store.upsert(
                ids_to_upsert, embeddings_to_upsert, documents_to_upsert, metadatas_to_upsert
            )

        manifest.save(self.persist_dir, new_manifest)

        total_chunks = sum(len(record["chunk_ids"]) for record in new_manifest.values())
        return BuildStats(
            added=added,
            updated=updated,
            deleted=deleted,
            unchanged=unchanged,
            total_chunks=total_chunks,
        )

    def search(self, query: str, k: int = 5, where: dict | None = None) -> list[Chunk]:
        query_vector = self.embedder.encode([query])[0]
        rows = self.store.query(query_vector, k, where)
        chunks: list[Chunk] = []
        for row in rows:
            meta = row["metadata"]
            chunk_index = int(row["id"].split("::")[-1])
            chunks.append(
                Chunk(
                    text=row["document"],
                    source_path=meta["source_path"],
                    relative_path=meta["relative_path"],
                    chunk_index=chunk_index,
                    score=row["score"],
                    metadata=meta,
                )
            )
        return chunks

    def answer(
        self,
        query: str,
        k: int = 5,
        model: str = DEFAULT_ANSWER_MODEL,
        max_tokens: int = 1024,
    ) -> Answer:
        """Retrieve top-k chunks and ask Claude to answer, citing sources.

        Requires the `rag[answer]` extra and ANTHROPIC_API_KEY. `anthropic`
        is imported lazily inside this method only -- search()/build()/
        refresh() never touch it.
        """
        from rag.generation import generate_answer

        chunks = self.search(query, k)
        text = generate_answer(query, chunks, model=model, max_tokens=max_tokens)
        return Answer(text=text, chunks=chunks)
