import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Point every storage module at an empty temporary directory."""
    from shivi import memory, projects, source, tasks

    files = {
        (memory, "MEMORY_FILE"): "{}",
        (tasks, "TASKS_FILE"): "{}",
        (projects, "PROJECTS_FILE"): "{}",
        (source, "SOURCE_FILE"): "[]",
    }
    for (module, attribute), content in files.items():
        path = tmp_path / f"{attribute.lower()}.json"
        path.write_text(content)
        monkeypatch.setattr(module, attribute, path)
    return tmp_path


def read_json(path):
    return json.loads(path.read_text())
