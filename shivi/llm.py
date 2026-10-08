"""Shared, lazily created model clients.

Loading the embedding model takes seconds and gigabytes of memory, so it
happens once, on first use, instead of at import time in every module.
"""
from functools import lru_cache

from shivi import config
from shivi.fileops import THINK_BLOCK


@lru_cache(maxsize=None)
def get_llm():
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=config.LLM_MODEL,
        temperature=0,
        reasoning=config.LLM_THINKING,
    )


@lru_cache(maxsize=None)
def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)


def get_vector_store():
    # Not cached: ingest rebuilds the collection and callers must see it.
    from langchain_chroma import Chroma
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.DB_PATH),
        embedding_function=get_embeddings(),
    )


def ask(prompt):
    """Invoke the chat model and return text with any <think> block removed."""
    response = get_llm().invoke(prompt)
    return THINK_BLOCK.sub("", response.content).strip()
