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
import json, time

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

def llm_request(command):
    prompt = f"""
    Classify the request.

    Labels:
    automation
    memory
    code
    task
    qa
    project
    planner

    Request: {command}

    Answer with only one label.
    """
    start = time.time()
    response = llm.invoke(prompt)
    print(f"LLM Request time : {time.time()-start:.2f}s")
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

def classify_request(command):

    command = command.lower()

    if any(word in command for word in [
        "open",
        "launch",
        "start"
    ]):
        return "automation"

    TASK_COMMANDS = [
    "add task",
    "show tasks",
    "remove task",
    "complete task"
    ]

    if any(
        command.startswith(x)
        for x in TASK_COMMANDS
    ):
        return "task"

    PROJECT_COMMANDS = [
    "add project",
    "show projects",
    "list projects",
    "remove project",
    "delete project",
    "what projects",
    "which projects"
    ]

    if any(
        command.startswith(x)
        for x in PROJECT_COMMANDS
    ):
        return "project"

    if any(word in command for word in [
        "remember",
        "forget"
    ]):
        return "memory"

    if any(word in command for word in [
        ".py",
        "file",
        "code"
    ]):
        return "code"

    return llm_request(command)

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
        # if intent in [
        #     "task",
        #     "project",
        #     "memory",
        #     "automation",
        #     "planner"
        # ]:
        #     request = normalize_request(request,intent)
        route_requests(request,intent)

if __name__ == "__main__":
    main()


