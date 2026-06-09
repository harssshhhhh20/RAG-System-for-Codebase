from automation_agent import process_automation
from query import process_code_request, extract_file_name, read_file
from memory import process_memory_request
from langchain_ollama import ChatOllama
from projects import process_project_request
from tasks import process_task_request
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from planner import process_planner_request
from normalizer import normalize_request
import json
DB_PATH = "db"

embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-m3"
)

vector_store = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

def classify_request(command):
    prompt = f"""
    Return ONLY one label.

    Labels:

    automation
    memory
    code
    task
    qa
    project
    planner

    Examples:

    open vscode
    automation

    open chrome
    automation

    open youtube
    automation

    open whatsapp
    automation

    remember my favorite language is python
    memory

    what should i work on today
    planner

    what should i do today
    planner

    what is my next task
    planner

    add task build planner to rag_agent
    task

    show tasks for rag_agent
    task

    complete task build planner in rag_agent
    task

    remove task build planner from rag_agent
    task

    what is my favorite language
    memory

    forget my favorite language
    memory

    show hello.py
    code

    explain query.py
    code

    review auth.py
    code

    improve hello.py
    code

    run hello.py
    code

    fix broken.py
    code

    add project /harsh/desktop/rag-agent
    project

    what project i am working on
    project

    what are the projects listed
    project 

    what is rag
    qa

    explain vector databases
    qa

    which file trains the model
    qa

    where is the lstm model trained
    qa

    which file trains the lstm model
    qa

    where is the model trained
    qa

    which file handles training
    qa

    where is the lstm model defined
    qa

    which file creates embeddings
    qa

    where is memory stored
    qa

    which file handles wake words
    qa

    which file contains the planner
    qa

    how does the task system work
    qa

    which file handles wake words
    qa

    where is memory stored
    qa

    which file creates embeddings
    qa

    how is the model trained
    qa

    how does the wake word system work
    qa

    what is retrieval augmented generation
    qa

    Request:
    {command}
    """
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    return intent

with open("filename_index.json","r",encoding="utf-8") as f:
    filename_index = json.load(f)

def answer_qa(question):
    target_filename = extract_file_name(
        question
    )

    question_lower = question.lower()

    if (
        target_filename
        and
        target_filename.lower()
        in filename_index
    ):
        file_path = filename_index[
            target_filename.lower()
        ]

        print(
            f"\nSelected File: {file_path}"
        )

        content = read_file(
            file_path
        )

        prompt = f"""
        You are SHIVI's code assistant.

        Explain this file clearly based on the question asked.

        Question:
        {question}

        File:
        {target_filename}

        Code:
        {content}

        Answer:
        """

        response = llm.invoke(
            prompt
        )

        print(
            response.content
        )

        return

    results = (
        vector_store
        .similarity_search_with_score(
            question,
            k=5
        )
    )

    if not results:
        print(
            "No relevant documents found."
        )
        return

    FILE_LOCATION_PHRASES = [
        "which file",
        "where is",
        "which module",
        "which script"
    ]

    if any(
        phrase in question_lower
        for phrase in FILE_LOCATION_PHRASES
    ):
        best_doc, best_score = results[0]

        return

    print(
        "\nRetrieved Documents:\n"
    )

    context_parts = []

    for doc, score in results:

        source = doc.metadata.get(
            "source",
            "unknown"
        )

        context_parts.append(
            f"""
        FILE:
        {source}

        CONTENT:
        {doc.page_content}
        """
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
    You are SHIVI's knowledge assistant.

    Your job is to answer questions using ONLY the provided context.

    Rules:

    1. Use information from the context whenever possible.
    2. Do not invent files, functions, projects, tasks, or features.
    3. If the question is about code, explain it clearly and simply.
    4. If multiple pieces of context are relevant, combine them into a coherent answer.
    5. Keep answers concise but informative.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    response = llm.invoke(
        prompt
    )
    print(
        response.content
    )

def route_requests(request,intent):
    print(f"Intent: {intent}")
    if intent == "automation":
        process_automation(
            request
        )

    elif intent == "memory":
        process_memory_request(
            request
        )

    elif intent == "code":
        process_code_request(
            request
        )

    elif intent == "project":
        process_project_request(request)

    elif intent == "task":
        process_task_request(request)

    elif intent =="planner":
        process_planner_request(request)

    elif intent=="qa":
        answer_qa(request)

    else:
        print(f"Unknown Intent: {intent}")

def main():
    print(r"""
    ███████╗██╗  ██╗██╗██╗   ██╗██╗
    ██╔════╝██║  ██║██║██║   ██║██║
    ███████╗███████║██║██║   ██║██║
    ╚════██║██╔══██║██║╚██╗ ██╔╝██║
    ███████║██║  ██║██║ ╚████╔╝ ██║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝

    Smart Hybrid Interface for Voice & Intelligence
    """)
    print("🙂 SHIVI Online")
    print("Type 'exit' to quit")
    while True:
        request = input("SHIVI >>> ")
        if request.lower() in ["exit","quit"]:
            print(r"""
            ██████╗  ██████╗  ██████╗ ██████╗
            ██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗
            ██║  ███╗██║   ██║██║   ██║██║  ██║
            ██║   ██║██║   ██║██║   ██║██║  ██║
            ╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝
            ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝

            ██████╗ ██╗   ██╗███████╗
            ██╔══██╗╚██╗ ██╔╝██╔════╝
            ██████╔╝ ╚████╔╝ █████╗
            ██╔══██╗  ╚██╔╝  ██╔══╝
            ██████╔╝   ██║   ███████╗
            ╚═════╝    ╚═╝   ╚══════╝
            """)
            print("😴 SHIVI Going To Sleep...")
            break
        intent = classify_request(request)
        if intent in [
            "task",
            "project",
            "memory",
            "automation",
            "planner"
        ]:
            request = normalize_request(request,intent)
        route_requests(request,intent)

if __name__ == "__main__":
    main()


