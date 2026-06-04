import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv

DATA_PATH = "data"
DB_PATH = "db"

documents = []

for root, dirs, files in os.walk(DATA_PATH):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif file.endswith((".txt", ".py", ".md", ".json")):
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
        except Exception as e:
            print(f"Skipped {file}: {e}")
print(f"Loaded {len(documents)} documents")

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 200
)

chunks = splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks")


embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-small-en-v1.5"
)

vectore_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_PATH
)

print(f"Created VectorDB successfully")