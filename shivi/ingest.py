import os
import json
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from shivi.source import load_sources

DB_PATH = "db"
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

def ingest_data():
    sources = load_sources()
    if not sources:
        print("No sources found.")
        return

    documents = []
    filename_index = {}

    for source_path in sources:
        if not os.path.exists(source_path):
            print(f"Skipped missing source: {source_path}")
            continue

        if os.path.isfile(source_path):
            files_to_process = [source_path]
        else:
            files_to_process = []
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    files_to_process.append(
                        os.path.join(root, file)
                    )
        for file_path in files_to_process:
            file = os.path.basename(
                file_path
            )
            filename_index[
                file.lower()
            ] = file_path
            try:
                if file.endswith(".pdf"):
                    loader = PyPDFLoader(
                        file_path
                    )
                    for doc in loader.load():
                        doc.metadata["file_type"] = ".pdf"
                        doc.metadata["filename"] = file
                        doc.metadata["source_root"] = source_path
                        documents.append(
                            doc
                        )
                elif file.endswith(SUPPORTED_TEXT_FILES):
                    loader = TextLoader(
                        file_path,
                        encoding="utf-8"
                    )
                    for doc in loader.load():
                        doc.metadata["file_type"] = (
                            os.path.splitext(
                                file
                            )[1]
                        )
                        doc.metadata["filename"] = file
                        doc.metadata["source_root"] = source_path
                        documents.append(
                            doc
                        )
            except Exception as e:
                print(f"Skipped {file}: {e}")
    print(f"Loaded {len(documents)} documents")
    if not documents:
        print("No documents found.")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(
        documents
    )
    print(f"Created {len(chunks)} chunks")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3"
    )
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    print("Created VectorDB successfully")
    with open(
        "storage/filename_index.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            filename_index,
            f,
            indent=4
        )
    print("filename_index.json updated")
if __name__ == "__main__":
    ingest_data()