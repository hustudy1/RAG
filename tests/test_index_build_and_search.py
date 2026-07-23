from pathlib import Path

from rag import RAGIndex


def test_build_then_search_returns_relevant_chunk(
    sample_source_dir: Path, tmp_path: Path
) -> None:
    index = RAGIndex(source_dir=sample_source_dir, persist_dir=tmp_path / "idx")

    stats = index.build()
    assert stats.added == 2  # readme.md, notes.txt (binary + .git skipped)
    assert stats.total_chunks >= 2

    results = index.search("elephant", k=3)
    assert len(results) > 0
    assert results[0].relative_path == "readme.md"
    assert isinstance(results[0].score, float)


def test_build_is_noop_on_second_call_without_force(
    sample_source_dir: Path, tmp_path: Path
) -> None:
    index = RAGIndex(source_dir=sample_source_dir, persist_dir=tmp_path / "idx")
    index.build()

    second_stats = index.build()
    assert second_stats == type(second_stats)()  # zero stats, nudges toward refresh()


def test_search_can_find_second_file(sample_source_dir: Path, tmp_path: Path) -> None:
    index = RAGIndex(source_dir=sample_source_dir, persist_dir=tmp_path / "idx")
    index.build()

    results = index.search("banana", k=3)
    assert any(r.relative_path == "notes.txt" for r in results)
