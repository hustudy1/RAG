from pathlib import Path

import pytest


@pytest.fixture
def sample_source_dir(tmp_path: Path) -> Path:
    """A small folder mimicking a real 'point RAG at any folder' target.

    Contains a distinctive keyword per file, a git-ignored file that must
    never be indexed, and a binary file with a text extension that the
    loader must skip without crashing.
    """
    (tmp_path / "readme.md").write_text(
        "# Notes\n\nThe elephant remembered everything about the project.\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text(
        "Buy more bananas for the office kitchen.\n", encoding="utf-8"
    )

    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "ignored.md").write_text("should never be indexed\n", encoding="utf-8")

    binary_path = tmp_path / "binary.md"
    binary_path.write_bytes(b"\x00\x01\x02not really markdown")

    return tmp_path
