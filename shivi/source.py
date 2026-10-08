import json, os
from shivi.config import SOURCE_FILE

def load_sources():
    if not os.path.exists(SOURCE_FILE):
        return []
    with open(
        SOURCE_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        try:
            data = json.load(f)
            if not isinstance(data,list):
                return []
            return data
        except json.JSONDecodeError:
            return []

def save_sources(sources):
    with open(SOURCE_FILE,"w",encoding="utf-8") as f:
        json.dump(
            sources,
            f,
            indent=4
        )

def add_sources(path):
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(path):
        print("Path does not exist")
        return
    sources = load_sources()
    if path in sources:
        print("Source already exists")
        return
    sources.append(path)
    save_sources(sources)
    print(f"Added - {path}")

def remove_source(path):
    path = os.path.abspath(os.path.expanduser(path))
    sources = load_sources()
    if path not in sources:
        print("Source NOT found")
        return
    sources.remove(path)
    save_sources(sources)
    print(f"Removed source: {path}")

def list_sources():
    sources = load_sources()
    if not sources:
        print("NO source added")
        return
    print("Sources:\n")
    for source in sources:
        print(f"- {source}")

def process_source_request(command):
    command = command.strip()
    lowered = command.lower()
    if lowered.startswith(("show source", "list source")):
        list_sources()
        return
    if lowered.startswith("add source"):
        path = command[len("add source"):].strip()
        add_sources(path)
        return
    if lowered.startswith(("remove source ", "delete source ")):
        path = command.split(maxsplit=2)[2].strip()
        remove_source(path)
        return
    print("Unknown source command.")
