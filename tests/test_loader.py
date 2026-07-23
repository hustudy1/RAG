from pathlib import Path

from rag.loader import iter_documents


def test_ignores_git_directory(sample_source_dir: Path) -> None:
    seen_relative_paths = {
        str(path.relative_to(sample_source_dir))
        for path, _text, _meta in iter_documents(sample_source_dir)
    }
    assert not any(p.startswith(".git") for p in seen_relative_paths)


def test_skips_binary_file_without_crashing(sample_source_dir: Path) -> None:
    seen_relative_paths = {
        str(path.relative_to(sample_source_dir))
        for path, _text, _meta in iter_documents(sample_source_dir)
    }
    assert "binary.md" not in seen_relative_paths


def test_loads_valid_text_files(sample_source_dir: Path) -> None:
    docs = list(iter_documents(sample_source_dir))
    by_name = {path.name: text for path, text, _meta in docs}
    assert "elephant" in by_name["readme.md"]
    assert "banana" in by_name["notes.txt"]


def test_metadata_has_expected_fields(sample_source_dir: Path) -> None:
    _path, _text, meta = next(iter_documents(sample_source_dir))
    assert set(meta.keys()) == {"file_type", "mtime", "size"}
