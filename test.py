from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

response = llm.invoke("Answer in one sentence: What is RAG?")

print(response.content)