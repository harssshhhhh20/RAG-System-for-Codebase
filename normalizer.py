from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

def normalize_request(request,intent):
    prompt = f"""
    You are a command normalizer.

    Convert the user's request into a canonical command.

    Rules:

    - Return ONLY the normalized command.
    - Do not explain.
    - Do not add extra text.
    - Keep project names unchanged.

    Intent:
    {intent}

    Examples:

    User:
    can you add build planner as a task for rag_agent

    Output:
    add task build planner to rag_agent

    User:
    please complete build planner in rag_agent

    Output:
    complete task build planner in rag_agent

    User:
    show me the tasks for rag_agent

    Output:
    show tasks for rag_agent

    User:
    what projects am i working on

    Output:
    what projects are listed

    User:
    open visual studio code

    Output:
    open vscode

    User:
    launch chrome browser

    Output:
    open chrome

    Request:
    {request}

    Output:
    """

    response = llm.invoke(
        prompt
    )

    return (
        response.content
        .strip()
    )