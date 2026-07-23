"""Local embedding model wrapper.

No network access or API key is required after the model's weights have
been downloaded once (sentence-transformers pulls them from Hugging Face
Hub into ~/.cache/huggingface on first use of a given model name).
"""

from __future__ import annotations

from rag.constants import DEFAULT_EMBEDDING_MODEL


class Embedder:
    """Wraps a sentence-transformers model for text -> vector encoding."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return vectors.tolist()
