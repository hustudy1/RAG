"""Optional answer-generation backend for RAGIndex.answer().

`anthropic` is only ever imported inside generate_answer(), never at module
load time, so importing rag or calling RAGIndex.search()/build()/refresh()
never touches this dependency or requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

from rag.types import Chunk


def generate_answer(
    query: str, chunks: list[Chunk], model: str, max_tokens: int
) -> str:
    import anthropic  # local import -- see module docstring

    client = anthropic.Anthropic()  # resolves ANTHROPIC_API_KEY from env

    context = "\n\n".join(f"[{c.relative_path}]\n{c.text}" for c in chunks)
    prompt = (
        "Answer the question using only the context below. Cite the source "
        "file (in brackets) for each claim you make. If the context doesn't "
        "contain enough information to answer, say so explicitly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return next(block.text for block in response.content if block.type == "text")
