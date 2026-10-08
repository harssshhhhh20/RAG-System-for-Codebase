import json
import os

from shivi import config, llm
from shivi.fileops import (
    backup_file,
    choose_file,
    clean_code,
    extract_file_name,
    read_file,
    resolve_file,
    run_file,
    show_changes,
    write_file,
)
from shivi.ollama_client import chat

CODE_INTENTS = (
    "edit", "rewrite", "show", "review", "summary",
    "bug", "run", "locate", "improve", "explain",
)

INTENT_PREFIXES = (
    ("find bug", "bug"),
    ("bug", "bug"),
    ("summarize", "summary"),
    ("summarise", "summary"),
    ("summary", "summary"),
    ("which file", "locate"),
    ("where is", "locate"),
    ("which module", "locate"),
    ("which script", "locate"),
) + tuple((intent, intent) for intent in CODE_INTENTS)


def load_filename_index():
    try:
        with open(config.FILENAME_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def llm_check_intent(question):
    prompt = (
        "Return the operation the user wants on a source file.\n"
        f"Options: {', '.join(CODE_INTENTS)}\n\n"
        f"Request: {question}"
    )
    schema = {
        "type": "object",
        "properties": {"intent": {"type": "string", "enum": list(CODE_INTENTS)}},
        "required": ["intent"],
    }
    content, _ = chat(config.LLM_MODEL, prompt, schema=schema, num_predict=32)
    try:
        return json.loads(content)["intent"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return "review"


def check_intent(command):
    command = command.lower().strip()
    for prefix, intent in INTENT_PREFIXES:
        if command.startswith(prefix):
            return intent
    return llm_check_intent(command)


def select_file(question):
    """Pick the file a request is about.

    Returns (file_path, retrieved_results). An explicit file name wins;
    otherwise the top semantic-search hit is used.
    """
    reference = extract_file_name(question)
    if reference:
        print(f"Extracted: {reference}")
        candidates = resolve_file(reference, load_filename_index())
        if not candidates:
            print("File not found in the index. Run 'ingest' after adding its source.")
            return None, []
        return choose_file(candidates), []

    results = llm.get_vector_store().similarity_search_with_score(question, k=3)
    if not results:
        print("No relevant documents found.")
        return None, []
    return results[0][0].metadata.get("source"), results


PROMPTS = {
    "rewrite": """
        You are a senior software engineer.

        Completely replace the file.

        Rules:

        1. Ignore the existing implementation.
        2. Build a completely new file that satisfies the user's request.
        3. Return ONLY the complete source code.
        4. No explanations.
        5. No markdown fences.

        User Request:
        {question}

        Existing File:
        {content}
        """,
    "edit": """
        You are a senior software engineer.

        Task:
        Modify the file according to the user's request.

        Rules:

        1. Preserve all existing functionality unless explicitly asked to change it.
        2. Make the smallest possible change that satisfies the request.
        3. Do not remove unrelated code.
        4. Do not rewrite the entire file unnecessarily.
        5. Maintain the same language and coding style.
        6. Return ONLY the complete updated file.
        7. Do not include explanations.
        8. Do not wrap the response in markdown fences.

        User Request:
        {question}

        Current Code:
        {content}
        """,
    "improve": """
        You are a principal software engineer.

        Your task is to improve the code while preserving its behavior.

        Rules:

        1. Preserve functionality.
        2. Improve readability.
        3. Improve maintainability.
        4. Improve error handling.
        5. Remove obvious bugs.
        6. Avoid unnecessary rewrites.
        7. Keep the same external behavior.
        8. Return ONLY the updated file.
        9. No explanations.
        10. No markdown fences.

        Current Code:
        {content}
        """,
    "explain": """
        You are a senior software engineer.

        Explain the following file.

        Include:
        1. Purpose of the file
        2. Main workflow
        3. Important functions/classes
        4. Inputs and outputs
        5. How it fits into the project

        File Name:
        {file_name}

        Code:
        {content}
        """,
    "bug": """
        You are a senior software engineer performing a code review.

        Analyze this file and identify:

        1. Bugs
        2. Potential runtime errors
        3. Bad coding practices
        4. Edge cases not handled
        5. Performance issues

        For each issue provide:
        - Problem
        - Why it is a problem
        - Suggested fix

        File Name:
        {file_name}

        Content:
        {content}
        """,
    "review": """
        You are a senior software engineer performing a professional code review.

        Analyze the file and identify:

        1. Bugs
        2. Runtime risks
        3. Code smells
        4. Security concerns
        5. Performance issues
        6. Maintainability issues
        7. Missing validations
        8. Edge cases

        For every issue provide:

        - Severity (Low/Medium/High)
        - Problem
        - Why it matters
        - Suggested fix

        Be critical and honest.
        Do not invent issues that are not present.

        File Name:
        {file_name}

        Code:
        {content}
        """,
    "summary": """
        You are an expert software engineer.

        Provide a concise summary of this file.

        Include:

        1. What the file does
        2. Its role in the project
        3. Main functions/classes
        4. Inputs and outputs
        5. Important dependencies

        Keep the summary under 300 words.

        File Name:
        {file_name}

        Code:
        {content}
        """,
}

EDITING_INTENTS = {"rewrite", "edit", "improve"}


def propose_and_apply(file_path, content, new_code, offer_run=False):
    """Show a diff, ask for confirmation, back up, then write."""
    print("\nProposed Changes:\n")
    print("=" * 80)
    diff_text = show_changes(content, new_code)
    if not diff_text.strip():
        print("\nNo changes detected.")
        return
    print(diff_text)
    if input("\nApply Changes(y/n): ").lower() != "y":
        print("Changes Discarded")
        return
    backup_path = backup_file(file_path)
    if not write_file(file_path, new_code):
        os.remove(backup_path)
        print("File update failed")
        return
    print(f"Backup created: {backup_path}")
    print("File updated successfully")
    if offer_run and input("You want to test the file(y/n): ").lower() == "y":
        _, result = run_file(file_path)
        print("Output:")
        print("=" * 80)
        print(result)


def process_code_request(question):
    file_path, results = select_file(question)
    if not file_path:
        return

    intent = check_intent(question)
    if intent not in CODE_INTENTS:
        intent = "review"

    if intent == "locate":
        print(f"\nFound in: {file_path}")
        return

    print(f"\nSelected File: {file_path}")

    if intent == "run":
        success, result = run_file(file_path)
        print("Output Expected:")
        print("=" * 80)
        print(result if success else f"Error in execution:\n{result}")
        return

    try:
        content = read_file(file_path)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"Could not read {file_path}: {e}")
        return

    if intent == "show":
        print(f"\nFile: {file_path}")
        print("\n" + "=" * 80)
        print(content)
        return

    prompt = PROMPTS[intent].format(
        question=question,
        content=content,
        file_name=os.path.basename(file_path),
    )
    response = llm.ask(prompt)

    if intent in EDITING_INTENTS:
        propose_and_apply(
            file_path,
            content,
            clean_code(response),
            offer_run=(intent == "improve"),
        )
        return

    print("\n" + "=" * 80)
    print(response)


if __name__ == "__main__":
    config.ensure_storage()
    process_code_request(input("Enter your query: "))
