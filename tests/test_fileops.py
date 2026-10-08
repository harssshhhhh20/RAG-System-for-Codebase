import pytest

from shivi.fileops import (
    backup_file,
    clean_code,
    extract_file_name,
    read_file,
    resolve_file,
    run_file,
    show_changes,
)


def test_clean_code_strips_fence_and_think():
    raw = "<think>plan</think>\n```python\nprint(1)\n```"
    assert clean_code(raw) == "print(1)"


def test_clean_code_unclosed_fence():
    # The improve path used to keep the opening fence in this case.
    assert clean_code("```python\nprint(1)") == "print(1)"


def test_clean_code_plain():
    assert clean_code("  x = 1  \n") == "x = 1"


def test_backups_do_not_overwrite_each_other(tmp_path):
    target = tmp_path / "a.py"
    target.write_text("v1")
    first = backup_file(str(target))
    target.write_text("v2")
    second = backup_file(str(target))
    assert first != second
    assert open(first).read() == "v1"
    assert open(second).read() == "v2"


def test_read_file_raises_instead_of_returning_error_text(tmp_path):
    with pytest.raises(OSError):
        read_file(str(tmp_path / "missing.py"))


def test_extract_file_name():
    assert extract_file_name("explain query.py please") == "query.py"
    assert extract_file_name("review shivi/router.py") == "shivi/router.py"
    assert extract_file_name("how does ingestion work") is None


def test_resolve_file_handles_duplicate_names():
    index = {"main.py": ["/a/main.py", "/b/pkg/main.py"]}
    assert resolve_file("main.py", index) == ["/a/main.py", "/b/pkg/main.py"]
    assert resolve_file("pkg/main.py", index) == ["/b/pkg/main.py"]
    assert resolve_file("other.py", index) == []


def test_resolve_file_accepts_legacy_string_index():
    assert resolve_file("main.py", {"main.py": "/a/main.py"}) == ["/a/main.py"]


def test_show_changes():
    diff = show_changes("a\nb", "a\nc")
    assert "-b" in diff and "+c" in diff


def test_run_file_reports_stderr_on_failure(tmp_path):
    script = tmp_path / "fail.py"
    script.write_text("print('partial')\nraise SystemExit('boom')\n")
    ok, output = run_file(str(script))
    assert not ok
    assert "boom" in output


def test_run_file_success(tmp_path):
    script = tmp_path / "ok.py"
    script.write_text("print('hi')\n")
    assert run_file(str(script)) == (True, "hi\n")


def test_run_file_unsupported(tmp_path):
    ok, output = run_file(str(tmp_path / "x.rb"))
    assert not ok and "not supported" in output
