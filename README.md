# 🔍 RAG System for Codebase

A Retrieval-Augmented Generation (RAG) system that lets you query, understand, and edit your codebase using natural language. Built with LangChain, ChromaDB, and HuggingFace embeddings.

---

## 🚀 What It Does

- **Ingests** your codebase (Python, JS, TS, Java, HTML, CSS, Markdown, JSON, YAML, PDF, TXT) into a local vector database
- **Understands** your queries using semantic search over embedded code chunks
- **Routes** your intent automatically — explain, summarize, review, debug, or directly edit files
- **Backs up** files before making any edits, so your code is always safe

---

## 🧠 Tech Stack

| Component | Tool |
|---|---|
| Embeddings | `BAAI/bge-m3` via HuggingFace |
| Vector Store | ChromaDB (local persistence) |
| LLM Framework | LangChain |
| Document Loaders | LangChain Community (TextLoader, PyPDFLoader) |
| Text Splitting | RecursiveCharacterTextSplitter |

---

## 📁 Project Structure

```
RAG-System-for-Codebase/
├── data/               # Put your codebase/files here
├── db/                 # Auto-generated ChromaDB vector store
├── ingest.py           # Loads, chunks, and embeds documents into ChromaDB
├── query.py            # Query the vector store with natural language
├── test.py             # Test/utility scripts
└── .gitignore
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/harssshhhhh20/RAG-System-for-Codebase.git
cd RAG-System-for-Codebase
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install langchain langchain-community langchain-huggingface langchain-chroma chromadb sentence-transformers pypdf
```

### 4. Add your codebase

Place all the files you want to query inside the `data/` folder. Supported formats: `.py`, `.js`, `.ts`, `.java`, `.html`, `.css`, `.json`, `.yaml`, `.yml`, `.md`, `.txt`, `.pdf`

---

## 🏃 Usage

### Step 1 — Ingest your codebase

```bash
python ingest.py
```

This will load all files from `data/`, split them into chunks, generate embeddings using `BAAI/bge-m3`, and persist everything to the local `db/` folder.

**Output:**
```
Loaded 42 documents
Created 310 chunks
Created VectorDB successfully
```

### Step 2 — Query your codebase

```bash
python query.py
```

Then type a natural language query, for example:

```
> Explain how authentication works in this codebase
> Summarize the main entry point
> Debug the error in utils.py
> Review the database connection logic
```

The system automatically detects your intent and responds accordingly.

---

## 💡 Supported Query Types

| Intent | Example Query |
|---|---|
| **Explain** | "Explain how the login function works" |
| **Summarize** | "Summarize what this project does" |
| **Review** | "Review the error handling in api.py" |
| **Debug** | "Debug why the database query is failing" |
| **Edit** | "Edit the config file to add a timeout" |

---

## 📝 Notes

- The `db/` folder is auto-created on first ingest — do not delete it between queries
- Re-run `ingest.py` whenever you add new files to `data/`
- Files are backed up automatically before any edits are made
- First run will download the `BAAI/bge-m3` model (~1.1GB) — internet connection required

---

## 🔮 Future Improvements

- [ ] Add `requirements.txt` for one-command install
- [ ] Modularize `query.py` into separate retriever/intent/prompt modules
- [ ] Add a simple Streamlit or Gradio UI
- [ ] Support incremental re-ingestion (only process changed files)
- [ ] Improve intent detection with an LLM classifier

---

## 👨‍💻 Author

**Harsh** — 3rd Year CS Student  
[GitHub](https://github.com/harssshhhhh20)
