from pathlib import Path

ROOT_DIR = Path.home() / ".shivi"

ROOT_DIR.mkdir(exist_ok=True)

DB_PATH = ROOT_DIR / "db"
STORAGE_DIR = ROOT_DIR / "storage"

DB_PATH.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)


MEMORY_FILE = STORAGE_DIR / "memory.json"
TASKS_FILE = STORAGE_DIR / "tasks.json"
PROJECTS_FILE = STORAGE_DIR / "projects.json"
SOURCE_FILE = STORAGE_DIR / "source.json"
FILENAME_INDEX_FILE = STORAGE_DIR / "filename_index.json"

FILES = [
    MEMORY_FILE,
    TASKS_FILE,
    PROJECTS_FILE,
    SOURCE_FILE,
    FILENAME_INDEX_FILE
]

for file in FILES:
    if not file.exists():
        file.write_text("{}")