import json
import os

from shivi import config, llm
from shivi.source import load_sources

SUPPORTED_TEXT_FILES = (
    ".txt",
    ".py",
    ".md",
    ".java",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml"
)

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".vscode",
    "build",
    "dist",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
}

IGNORE_FILES = {
    ".DS_Store"
}

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Extensions that get a syntax-aware splitter (splits on function/class
# boundaries before falling back to characters).
LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "js",
    ".ts": "ts",
    ".java": "java",
    ".md": "markdown",
    ".html": "html",
}


def collect_files(sources):
    """Yield (source_root, file_path) for every indexable file."""
    for source_path in sources:
        if not os.path.exists(source_path):
            print(f"Skipped missing source: {source_path}")
            continue
        if os.path.isfile(source_path):
            yield source_path, source_path
            continue
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS and not d.startswith(".")
            ]
            for file in files:
                if file in IGNORE_FILES or file.startswith(".") or file.endswith(".bak"):
                    continue
                yield source_path, os.path.join(root, file)


def build_filename_index(file_paths):
    """Map lowercase basename -> sorted list of every path with that name."""
    index = {}
    for file_path in file_paths:
        index.setdefault(os.path.basename(file_path).lower(), []).append(file_path)
    return {name: sorted(set(paths)) for name, paths in index.items()}


def load_documents(files):
    from langchain_community.document_loaders import PyPDFLoader, TextLoader

    documents = []
    for source_root, file_path in files:
        file = os.path.basename(file_path)
        ext = os.path.splitext(file)[1].lower()
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext in SUPPORTED_TEXT_FILES:
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            continue
        try:
            for doc in loader.load():
                doc.metadata["file_type"] = ext
                doc.metadata["filename"] = file
                doc.metadata["source_root"] = source_root
                documents.append(doc)
        except Exception as e:
            print(f"Skipped {file}: {e}")
    return documents


def split_documents(documents):
    from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

    default = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    splitters = {
        ext: RecursiveCharacterTextSplitter.from_language(
            Language(language),
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        for ext, language in LANGUAGE_BY_EXTENSION.items()
    }
    chunks = []
    for doc in documents:
        splitter = splitters.get(doc.metadata.get("file_type"), default)
        chunks.extend(splitter.split_documents([doc]))
    return chunks


def ingest_data():
    sources = load_sources()
    if not sources:
        print("No sources found.")
        return

    print("\nSources Being Ingested:\n")
    for source in sources:
        print(source)

    files = list(collect_files(sources))
    filename_index = build_filename_index(path for _, path in files)

    documents = load_documents(files)
    print(f"Loaded {len(documents)} documents")
    if not documents:
        print("No documents found.")
        return

    chunks = split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    # Rebuild from scratch: adding to the old collection would duplicate
    # every chunk on each ingest and keep chunks of deleted files.
    vector_store = llm.get_vector_store()
    vector_store.delete_collection()
    vector_store = llm.get_vector_store()
    vector_store.add_documents(chunks)
    print("Created VectorDB successfully")

    with open(
        config.FILENAME_INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            filename_index,
            f,
            indent=4
        )
    print("filename_index.json updated")
    print("Knowledge base updated.")


if __name__ == "__main__":
    config.ensure_storage()
    ingest_data()
