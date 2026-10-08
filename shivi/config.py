import os
from pathlib import Path

ROOT_DIR = Path(os.environ.get("SHIVI_HOME", Path.home() / ".shivi"))

DB_PATH = ROOT_DIR / "db"
STORAGE_DIR = ROOT_DIR / "storage"

MEMORY_FILE = STORAGE_DIR / "memory.json"
TASKS_FILE = STORAGE_DIR / "tasks.json"
PROJECTS_FILE = STORAGE_DIR / "projects.json"
SOURCE_FILE = STORAGE_DIR / "source.json"
FILENAME_INDEX_FILE = STORAGE_DIR / "filename_index.json"

# Model settings. Override with environment variables so experiments can
# swap models without editing code.
LLM_MODEL = os.environ.get("SHIVI_LLM_MODEL", "qwen3:4b")
EMBEDDING_MODEL = os.environ.get("SHIVI_EMBEDDING_MODEL", "BAAI/bge-m3")
# qwen3:4b reasons before answering whether or not thinking is requested;
# with thinking off, Ollama returns that reasoning inside the answer text.
# Keeping it on puts the reasoning in a separate field so answers and code
# edits stay clean. Intent routing is unaffected: it uses schema-constrained
# decoding (see shivi/router.py), which skips the reasoning entirely.
LLM_THINKING = os.environ.get("SHIVI_LLM_THINKING", "1") == "1"

COLLECTION_NAME = "shivi"

DEFAULT_CONTENT = {
    MEMORY_FILE: "{}",
    TASKS_FILE: "{}",
    PROJECTS_FILE: "{}",
    SOURCE_FILE: "[]",
    FILENAME_INDEX_FILE: "{}"
}


def ensure_storage():
    DB_PATH.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    for file, content in DEFAULT_CONTENT.items():
        if not file.exists():
            file.write_text(
                content,
                encoding="utf-8"
            )
