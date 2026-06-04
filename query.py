from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

DB_PATH = "db"

embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-m3"
)

vector_store = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)

retriever = vector_store.as_retriever(
    search_kwargs = {"k":5}
)

question = input("Ask your question: ")

results = vector_store.similarity_search_with_score(
    question,
    k=10
)


print("\nRetrieved Documents:\n")

for i, (doc, score) in enumerate(results, start=1):
    print(f"\n--- Result {i} ---")
    print(f"Score: {score}")
    print(f"Source: {doc.metadata.get('source')}")
    print("\nChunk Preview:")
    print(doc.page_content[:300])


context = "\n\n".join([doc.page_content for doc,score in results])

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

prompt = f"""
You are a helpful AI assistant.

Answer the user's question using the provided context.

Rules:
1. Base your answer primarily on the retrieved context.
2. You may make reasonable inferences when they are clearly supported by the context.
3. If the context contains code, you may explain what the code does and infer its purpose from the implementation.
4. If the answer cannot be determined from the provided context, respond exactly with:
   "I don't know based on the provided documents."
5. Do not invent facts that are not supported by the context.

Context:
{context}

Question:
{question}
"""

response = llm.invoke(prompt)

print("\n" + "="*70)
print("Answer: ")
print(response.content)