from automation_agent import process_automation
from query import process_code_request
from memory import process_memory_request
from langchain_ollama import ChatOllama
from projects import process_project_request

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
    qa
    project

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

    Request:
    {command}
    """
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    return intent

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

    else:

        print(
            "General QA module not implemented yet."
        )

def main():
    print("SHIVI started")
    print("Type 'exit' to quit")
    while True:
        request = input("SHIVI > ")
        if request.lower() in ["exit","quit"]:
            print("\nGoodBye")
            break
        intent = classify_request(request)
        route_requests(request,intent)

if __name__ == "__main__":
    main()


