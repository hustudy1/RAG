import time
from pathlib import Path

from rag import RAGIndex


def test_refresh_detects_added_modified_deleted(
    sample_source_dir: Path, tmp_path: Path
) -> None:
    index = RAGIndex(source_dir=sample_source_dir, persist_dir=tmp_path / "idx")
    index.build()

    # Ensure the mtime of the modified file actually advances.
    time.sleep(0.01)

    # Modify notes.txt's content.
    (sample_source_dir / "notes.txt").write_text(
        "The kitchen is now fully stocked with mangoes instead.\n", encoding="utf-8"
    )
    # Add a brand new file.
    (sample_source_dir / "new_doc.md").write_text(
        "A giraffe wandered into the office by mistake.\n", encoding="utf-8"
    )
    # Delete an existing file.
    (sample_source_dir / "readme.md").unlink()

    stats = index.refresh()
    assert stats.added == 1
    assert stats.updated == 1
    assert stats.deleted == 1

    # The deleted file's content should no longer be retrievable.
    results = index.search("elephant", k=5)
    assert all(r.relative_path != "readme.md" for r in results)

    # The new file's content should be retrievable.
    results = index.search("giraffe", k=5)
    assert any(r.relative_path == "new_doc.md" for r in results)

    # The modified file's new content should be retrievable, old content gone.
    results = index.search("mangoes", k=5)
    assert any(r.relative_path == "notes.txt" for r in results)


def test_refresh_on_unbuilt_index_acts_as_full_build(
    sample_source_dir: Path, tmp_path: Path
) -> None:
    index = RAGIndex(source_dir=sample_source_dir, persist_dir=tmp_path / "idx")
    stats = index.refresh()
    assert stats.added == 2
    assert stats.updated == 0
    assert stats.deleted == 0


def test_refresh_is_idempotent_when_nothing_changed(
    sample_source_dir: Path, tmp_path: Path
) -> None:
    index = RAGIndex(source_dir=sample_source_dir, persist_dir=tmp_path / "idx")
    index.build()

    stats = index.refresh()
    assert stats.added == 0
    assert stats.updated == 0
    assert stats.deleted == 0
    assert stats.unchanged == 2
