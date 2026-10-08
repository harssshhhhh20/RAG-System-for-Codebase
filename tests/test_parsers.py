import os

from conftest import read_json
from shivi import memory, projects, source, tasks
from shivi.ingest import build_filename_index, collect_files


def test_memory_roundtrip(storage, capsys):
    memory.process_memory_request("remember my name is Harsh")
    assert read_json(memory.MEMORY_FILE) == {"my name": "harsh"}
    memory.process_memory_request("what is my name?")
    assert "my name: harsh" in capsys.readouterr().out
    memory.process_memory_request("forget my name")
    assert read_json(memory.MEMORY_FILE) == {}


def test_memory_recall_variants(storage, capsys):
    memory.remember("my editor", "vim")
    memory.process_memory_request("what's my editor")
    memory.process_memory_request("recall my editor")
    assert capsys.readouterr().out.count("my editor: vim") == 2


def test_source_add_keeps_path_case(storage, tmp_path):
    folder = tmp_path / "MyNotes"
    folder.mkdir()
    source.process_source_request(f"Add Source {folder}")
    assert read_json(source.SOURCE_FILE) == [str(folder)]
    source.process_source_request(f"remove source {folder}")
    assert read_json(source.SOURCE_FILE) == []


def test_project_and_task_flow(storage, tmp_path, capsys):
    folder = tmp_path / "Rag-Agent"
    folder.mkdir()
    projects.process_project_request(f"add project {folder}")
    assert read_json(projects.PROJECTS_FILE)["rag_agent"]["path"] == str(folder)

    tasks.process_task_request("add task write tests to rag_agent")
    tasks.process_task_request("add task write paper to rag_agent")
    tasks.process_task_request("complete task write tests in rag_agent")
    assert tasks.get_active_tasks() == [("rag_agent", "write paper")]

    tasks.process_task_request("show tasks")
    assert "rag_agent --> write paper" in capsys.readouterr().out

    tasks.process_task_request("remove task write paper from rag_agent")
    assert tasks.get_active_tasks() == []


def test_task_needs_existing_project(storage, capsys):
    tasks.process_task_request("add task x to missing")
    assert "Project does not exist" in capsys.readouterr().out


def test_filename_index_keeps_every_duplicate(tmp_path):
    for sub in ("a", "b"):
        (tmp_path / sub).mkdir()
        (tmp_path / sub / "main.py").write_text("")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.py").write_text("")
    (tmp_path / "a" / "main.py.bak").write_text("")

    files = [path for _, path in collect_files([str(tmp_path)])]
    index = build_filename_index(files)

    assert index["main.py"] == sorted([
        os.path.join(tmp_path, "a", "main.py"),
        os.path.join(tmp_path, "b", "main.py"),
    ])
    assert "config.py" not in index
    assert "main.py.bak" not in index
