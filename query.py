from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

DB_PATH = 'db'

embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-small-en-v1.5"
)

vector_store = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)

retriever = vector_store.as_retriever(
    search_kwargs = {"k":3}
)

question = input("Ask your question: ")

docs = retriever.invoke(question)

print("\nRetrieved Sources:\n")

for doc in docs:
    print(doc.metadata.get("source"))

print("\nRetrieved Chunks:\n")

for doc in docs:
    print("=" * 60)
    print(doc.page_content[:500])

context = "\n\n".join([doc.page_content for doc in docs])

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

prompt = f"""
You are a question-answering assistant.

Answer ONLY from the provided context.

If the answer is not present in the context,
reply with:

"I don't know based on the provided documents."

Context:
{context}

Question:
{question}
"""

response = llm.invoke(prompt)

print("Answer:\n")
print(response.content)