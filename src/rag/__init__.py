"""rag -- a local, general-purpose retrieval-augmented generation library.

    from rag import RAGIndex

    index = RAGIndex(source_dir="/path/to/any/folder")
    index.build()
    chunks = index.search("query", k=5)

Core indexing/retrieval never requires an API key or network access beyond
a one-time embedding-model download. RAGIndex.answer() is an optional
convenience that requires the `rag[answer]` extra and ANTHROPIC_API_KEY.
"""

from rag.index import RAGIndex
from rag.types import Answer, BuildStats, Chunk

__version__ = "0.1.0"

__all__ = ["RAGIndex", "Chunk", "BuildStats", "Answer", "__version__"]
