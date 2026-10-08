# SHIVI

### Your Local AI Developer Assistant

SHIVI is a local AI-powered developer assistant that understands, edits, and manages entire codebases.

Instead of manually searching through files, SHIVI lets you ask questions, edit code, manage projects, and work with repositories using natural language — all while running completely locally.

---

## Features

### Codebase Understanding

* Explain source files
* Summarize modules
* Review code quality
* Locate files and functionality
* Answer architecture questions

### Code Editing

* Edit files using natural language
* Rewrite files completely
* Preview changes with unified diffs
* Automatic backup creation before modifications

### RAG-Powered Search

* Semantic search across repositories
* Local vector database using ChromaDB
* Context-aware answers grounded in your code

### Source Management

* Add repositories dynamically
* Remove repositories
* Ingest multiple codebases
* Persistent source tracking

### Project Management

* Add projects
* Track project status
* Persistent project storage

### Task Management

* Add tasks
* Complete tasks
* Delete tasks
* View active tasks

### Memory System

* Store notes and information
* Persistent memory across sessions

### Local First

* Runs completely locally
* Uses Ollama-hosted LLMs
* No cloud dependency

---

## Tech Stack

| Component           | Technology        |
| ------------------- | ----------------- |
| LLM                 | Ollama + Qwen     |
| Framework           | LangChain         |
| Embeddings          | BAAI/bge-m3       |
| Vector Database     | ChromaDB          |
| Document Processing | LangChain Loaders |
| Language            | Python            |

---

## Installation

### Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull the model:

```bash
ollama pull qwen3:4b
```

### Install SHIVI

```bash
pip install shivi-agent
```

Launch:

```bash
shivi
```

---

## Quick Start

### Add a Repository

```text
add source /Users/username/project
```

### Ingest Files

```text
ingest
```

### Ask Questions

```text
which file handles authentication?

explain planner.py

summarize query.py
```

### Edit Code

```text
add logging to query.py

rewrite test.py as a calculator
```

### Manage Projects

```text
add project /Users/username/my_project

show projects

open project my_project
```

### Manage Tasks

Tasks belong to a tracked project.

```text
add task build authentication to my_project

show tasks

show tasks for my_project

complete task build authentication in my_project

remove task build authentication from my_project
```

### Memory

```text
remember my editor is vim

what is my editor

forget my editor
```

---

## Example Workflow

```text
add source /Users/username/my_project

ingest

which file handles authentication?

explain auth.py

add logging to auth.py
```

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SHIVI_LLM_MODEL` | `qwen3:4b` | Ollama chat model |
| `SHIVI_EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding model for search |
| `SHIVI_LLM_THINKING` | `1` | Keep the model's reasoning separate from its answer; `0` only for non-thinking models |
| `SHIVI_HOME` | `~/.shivi` | Where the vector DB and JSON state live |

> Upgrading from 0.1: the vector store now uses a named collection, so run `ingest` once after upgrading.

---

## Architecture

```text
User
 ↓
Intent Classification (keyword rules → LLM fallback with constrained output)
 ↓
┌───────────────┬───────────────┐
│ Command Tools │ RAG Retrieval │
└───────────────┴───────────────┘
 ↓
Qwen (Ollama)
 ↓
Response / Code Changes
```

---

## Roadmap

### Completed

* Codebase RAG
* Semantic Search
* Source Management
* File Editing
* Diff Viewer
* Automatic Backups
* Task Management
* Project Management
* Persistent Memory
* CLI Packaging

### In Progress

* Terminal Command Execution

### Planned

* Multi-file Editing
* Git Integration
* Automatic Error Fix Loops
* Agent Workflows

---

## Development

```bash
pip install -e ".[dev,eval]"
python -m pytest
```

---

## Research

SHIVI doubles as a testbed for studying assistants that run on small local models. The [evaluation harness](eval/README.md) contains:

* **Intent routing.** Keyword rules vs. a local LLM vs. rules→LLM hybrids, across prompt styles and decoding modes, with latency, confidence intervals and paired significance tests.
* **File retrieval.** Character vs. syntax-aware chunking, BM25 vs. dense vs. fused retrieval, with and without a filename index.

Pilot results are in [`results/`](results/). The study plan and draft paper are in [`paper/`](paper/).

---

## Author

Harsh Maurya

Built while exploring Retrieval-Augmented Generation, local LLMs, and AI-powered developer tools.

---

### SHIVI

Your Local AI Developer Assistant.
