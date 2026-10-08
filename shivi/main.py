import subprocess

from shivi import config, llm
from shivi.automation_agent import process_automation
from shivi.fileops import choose_file, extract_file_name, read_file, resolve_file
from shivi.ingest import ingest_data
from shivi.memory import process_memory_request
from shivi.planner import process_planner_request
from shivi.projects import process_project_request
from shivi.query import load_filename_index, process_code_request
from shivi.router import classify_request
from shivi.source import process_source_request
from shivi.tasks import process_task_request

FILE_LOCATION_PHRASES = (
    "which file",
    "where is",
    "which module",
    "which script",
)


def answer_about_file(question, file_path):
    try:
        content = read_file(file_path)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"Could not read {file_path}: {e}")
        return
    prompt = f"""
        You are SHIVI's code assistant.

        Explain this file clearly based on the question asked.

        Question:
        {question}

        File:
        {file_path}

        Code:
        {content}

        Answer:
        """
    print(llm.ask(prompt))


def answer_qa(question):
    reference = extract_file_name(question)
    candidates = resolve_file(reference, load_filename_index())
    if candidates:
        file_path = choose_file(candidates)
        if file_path:
            print(f"\nSelected File: {file_path}")
            answer_about_file(question, file_path)
        return

    results = llm.get_vector_store().similarity_search_with_score(question, k=5)
    if not results:
        print("No relevant documents found. Did you run 'ingest'?")
        return

    if any(phrase in question.lower() for phrase in FILE_LOCATION_PHRASES):
        # Rank files by their best chunk (lower distance is better).
        best = {}
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            best[source] = min(score, best.get(source, score))
        print("\nMost likely files:")
        for source, score in sorted(best.items(), key=lambda item: item[1]):
            print(f"- {source} (distance {score:.3f})")
        return

    context = "\n\n".join(
        f"FILE:\n{doc.metadata.get('source', 'unknown')}\n\nCONTENT:\n{doc.page_content}"
        for doc, _ in results
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
    print(llm.ask(prompt))


HANDLERS = {
    "automation": process_automation,
    "memory": process_memory_request,
    "code": process_code_request,
    "project": process_project_request,
    "task": process_task_request,
    "planner": process_planner_request,
    "qa": answer_qa,
    "source": process_source_request,
    "ingest": lambda request: ingest_data(),
}


def route_requests(request, intent):
    print(f"Intent: {intent}")
    handler = HANDLERS.get(intent)
    if handler is None:
        print(f"Unknown Intent: {intent}")
        return
    handler(request)


def check_ollama():
    try:
        subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            check=True
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def main():
    if not check_ollama():
        print("\nOllama not found or not running.")
        print("\nInstall Ollama:")
        print("https://ollama.com")
        print("\nThen run:")
        print(f"ollama pull {config.LLM_MODEL}")
        return

    config.ensure_storage()

    print(r"""
    ███████╗██╗  ██╗██╗██╗   ██╗██╗
    ██╔════╝██║  ██║██║██║   ██║██║
    ███████╗███████║██║██║   ██║██║
    ╚════██║██╔══██║██║╚██╗ ██╔╝██║
    ███████║██║  ██║██║ ╚████╔╝ ██║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝

    Smart Hybrid Interface for Voice & Intelligence
    """)
    print("🙂 SHIVI Online.")
    print("Type 'exit' to quit.")
    print("To ingest simply bash 'ingest'.")
    while True:
        try:
            request = input("SHIVI >>> ").strip()
        except (EOFError, KeyboardInterrupt):
            request = "exit"
        if not request:
            continue
        if request.lower() in ["exit", "quit"]:
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
        intent, decided_by = classify_request(request, config.LLM_MODEL)
        if decided_by == "llm":
            print("(routed by LLM)")
        route_requests(request, intent)


if __name__ == "__main__":
    main()
