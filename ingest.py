import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from collections import Counter

DATA_PATH = "data"
DB_PATH = "db"

documents = []

for root, dirs, files in os.walk(DATA_PATH):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            if file.endswith(".pdf"):
               loader = PyPDFLoader(file_path)
               for doc in loader.load():
                   doc.metadata["file_type"] = ".pdf"
                   documents.append(doc)
            elif file.endswith((".txt",".py",".md")):
                loader = TextLoader(
                    file_path,
                    encoding= "utf-8"
                )
                for doc in loader.load():
                    doc.metadata["file_type"] = os.path.splitext(file)[1]
                    documents.append(doc)
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
    model_name = "BAAI/bge-m3"
)

vectore_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_PATH
)

print(f"Created VectorDB successfully")