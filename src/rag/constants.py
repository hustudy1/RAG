"""Default configuration values shared across the rag package."""

# Directory names to always prune during a folder walk, regardless of depth.
DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".cache",
    "target",
    ".tox",
}

# File extensions loaded as plain UTF-8 text.
TEXT_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".rst",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".sh", ".sql", ".html", ".css",
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
}

# File extensions requiring a dedicated extraction step.
PDF_EXTENSIONS = {".pdf"}

SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS

DEFAULT_MAX_FILE_SIZE_BYTES = 10_000_000  # 10 MB

DEFAULT_CHUNK_SIZE = 800  # characters
DEFAULT_CHUNK_OVERLAP = 150  # characters

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

DEFAULT_ANSWER_MODEL = "claude-opus-5-5"

# Name of the single Chroma collection stored per persist_dir.
CHROMA_COLLECTION_NAME = "chunks"

# Name of the manifest file tracking per-file indexing state.
MANIFEST_FILENAME = "manifest.json"

# Root of the central cache used when the caller doesn't supply persist_dir.
CACHE_DIR_NAME = "rag_lib"
