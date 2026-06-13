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

### Manage Tasks

```text
add task Build authentication

show tasks

complete task 1
```

### Manage Projects

```text
add project SHIVI

show projects
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

## Architecture

```text
User
 ↓
Intent Classification
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

## Author

Harsh Maurya

Built while exploring Retrieval-Augmented Generation, local LLMs, and AI-powered developer tools.

---

### SHIVI

Your Local AI Developer Assistant.
