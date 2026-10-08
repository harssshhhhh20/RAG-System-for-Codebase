"""File helpers shared by the code assistant and the self-repair agent."""
import difflib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

FILE_REFERENCE = re.compile(r"[\w\-./~]*[\w\-]\.[a-zA-Z0-9]+")


def read_file(file_path):
    """Read a text or PDF file. Raises OSError/ValueError on failure.

    Errors are raised rather than returned as text so an error message can
    never be mistaken for file content and written back to disk.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        pages = PyPDFLoader(file_path).load()
        return "\n".join(page.page_content for page in pages)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except OSError as e:
        print(e)
        return False


def backup_file(file_path):
    """Copy file to a timestamped .bak so earlier backups are never overwritten."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = f"{file_path}.{stamp}.bak"
    shutil.copy2(file_path, backup_path)
    return backup_path


def extract_file_name(question):
    """Return the first thing that looks like a file name or path, or None."""
    match = FILE_REFERENCE.search(question)
    return match.group(0) if match else None


def resolve_file(reference, filename_index):
    """Map a user file reference to indexed paths.

    The index maps lowercase basenames to a list of paths (older indexes
    stored a single string). A reference containing a directory, e.g.
    "shivi/query.py", narrows the candidates by path suffix.
    """
    if not reference:
        return []
    key = os.path.basename(reference).lower()
    candidates = filename_index.get(key, [])
    if isinstance(candidates, str):
        candidates = [candidates]
    if "/" in reference:
        suffix = os.path.normpath(reference).lower()
        narrowed = [
            path for path in candidates
            if os.path.normpath(path).lower().endswith(suffix)
        ]
        if narrowed:
            return narrowed
    return list(candidates)


def choose_file(candidates):
    """Ask the user to pick when a name matches several files."""
    if len(candidates) <= 1:
        return candidates[0] if candidates else None
    print("\nSeveral files match:")
    for number, path in enumerate(candidates, start=1):
        print(f"  {number}. {path}")
    choice = input("Pick a number (blank to cancel): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
        return candidates[int(choice) - 1]
    return None


def show_changes(old_content, new_content):
    diff = difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        fromfile="Original",
        tofile="Modified",
        lineterm=""
    )
    return "\n".join(diff)


THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


def clean_code(code):
    """Strip <think> blocks and a surrounding markdown fence from LLM output."""
    code = THINK_BLOCK.sub("", code).strip()
    if code.startswith("```"):
        lines = code.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines)
    return code


RUN_COMMANDS = {
    ".py": lambda path: [sys.executable, path],
    ".js": lambda path: ["node", path],
    ".java": lambda path: ["java", path],
}


def run_file(exec_file, timeout=30):
    """Run a script. Returns (succeeded, output or error text).

    This executes arbitrary code on the user's machine; callers must only
    run files the user explicitly asked to run.
    """
    ext = os.path.splitext(exec_file)[1].lower()
    if ext not in RUN_COMMANDS:
        return False, f"Execution not supported for {ext}"
    try:
        result = subprocess.run(
            RUN_COMMANDS[ext](exec_file),
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    output = result.stdout if result.returncode == 0 else (result.stderr or result.stdout)
    return result.returncode == 0, output
