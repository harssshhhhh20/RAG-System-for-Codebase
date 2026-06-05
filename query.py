import os
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
import shutil
import re

DB_PATH = "db"

EXPLAIN_KEYWORDS = [
    "explain",
    "describe",
    "understand",
    "walk through",
    "what does",
    "how does",
    "purpose",
    "analyze",
    "breakdown"
]
SUMMARY_KEYWORDS = [
    "summarize",
    "summary",
    "overview",
    "brief",
    "short explanation"
]
SHOW_KEYWORDS = [
    "show",
    "open",
    "display",
    "read"
]
REVIEW_KEYWORDS = [
    "review",
    "inspect",
    "evaluate",
    "check code",
    "audit"
]
IMPROVE_KEYWORDS = [
    "improve",
    "optimize",
    "refactor",
    "enhance",
    "clean up"
]
BUG_KEYWORDS = [
    "bug",
    "error",
    "issue",
    "problem",
    "debug",
    "fix"
]
EDIT_KEYWORDS = [
    "write",
    "create",
    "add",
    "modify",
    "edit",
    "change",
    "insert",
    "implement"
]

def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if(ext==".pdf"):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return "\n".join(
                page.page_content
                for page in pages
            )
        else:
            with open(file_path,"r",encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        return f"Exception in {e} file occured"

def write_file(file_path,content):
    try:
        with open(file_path,"w",encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(e)
        return False

def contains_keyword(question, keywords):
    return any(
        keyword in question.lower()
        for keyword in keywords
    )

def backup_file(file_path):
    backup_path = file_path + ".bak"
    shutil.copy(
        file_path,
        backup_path
    )
    return backup_path

def extract_file_name(question):
    matches = re.findall(
        r'[\w\-]+\.[a-zA-Z0-9]+',
        question
    )
    if matches:
        return matches[0]
    return None

embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-m3"
)

vector_store = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)

question = input("Ask your question: ")

target_filename = extract_file_name(question)
if target_filename:
    results = vector_store.similarity_search_with_score(
        target_filename,
        k=10
    )
    filename_matches = []
    for doc, score in results:
        if (
            doc.metadata.get("filename", "").lower()
            ==
            target_filename.lower()
        ):
            filename_matches.append(
                (doc, score)
            )
    if filename_matches:
        results = filename_matches
    else:
        results = vector_store.similarity_search_with_score(
            question,
            k=5
        )
else:
    results = vector_store.similarity_search_with_score(
        question,
        k=5
    )

is_show_file = contains_keyword(question,SHOW_KEYWORDS)
is_explain = contains_keyword(question,EXPLAIN_KEYWORDS)
is_summary = contains_keyword(question,SUMMARY_KEYWORDS)
is_review = contains_keyword(question,REVIEW_KEYWORDS)
is_bug = contains_keyword(question,BUG_KEYWORDS)
is_improve = contains_keyword(question,IMPROVE_KEYWORDS)
is_edit = contains_keyword(question,EDIT_KEYWORDS)




# print("\nRetrieved Documents:\n")

# for i, (doc, score) in enumerate(results, start=1):
#     print(f"\n--- Result {i} ---")
#     print(f"Score: {score}")
#     print(f"Source: {doc.metadata.get('source')}")
#     print("\nChunk Preview:")
#     print(doc.page_content[:300])


context = "\n\n".join([doc.page_content for doc,score in results])


llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

if is_edit:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    file_extension = os.path.splitext(file_path)[1]
    prompt = f"""
    You are a senior software engineer.
    The file being modified is:
    {os.path.basename(file_path)}
    File Extension:
    {file_extension}
    Maintain the same programming language,
    coding style, and project conventions.
    Return ONLY the complete updated file.
    User Request:
    {question}
    Current Code:
    {content}
    """
    response = llm.invoke(prompt)
    new_code = response.content
    print("\nProposed Changes:\n")
    print("=" * 80)
    print(new_code[:3000])
    choice = input("\nApply Changes(y/n)")
    if choice.lower()=="y":
        backup_path = backup_file(file_path)

        success = write_file(file_path, new_code)

        if success:
            print(f"Backup created: {backup_path}")
            print("File updated successfully")
        else:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            print("File update failed")
    else:
        print("Changes Discarded")
elif is_show_file:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    print(f"\nFile: {file_path}")
    print("\n" + "=" * 80)
    print(content)

    exit()
elif is_explain:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    prompt = f"""
    You are a senior software engineer.

    Explain the following file.

    Include:
    1. Purpose of the file
    2. Main workflow
    3. Important functions/classes
    4. Inputs and outputs
    5. How it fits into the project

    File Name:
    {os.path.basename(file_path)}

    Code:
    {content}
    """
    response = llm.invoke(prompt)

    print("\n" + "=" * 80)
    print(response.content)

    exit()
elif is_bug:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    prompt = f"""
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
    {os.path.basename(file_path)}

    Content:
    {content} """
    response = llm.invoke(prompt)
    print("\n" + "=" * 80)
    print(response.content)

    exit()
elif is_improve:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    prompt = f"""
    You are a principal software engineer.

    Your task is to improve this code.

    Analyze the file and suggest:

    1. Better design patterns
    2. Cleaner architecture
    3. Improved readability
    4. Better error handling
    5. Better maintainability
    6. Performance optimizations
    7. Scalability improvements
    8. Python best practices

    For each improvement provide:

    - Current issue
    - Why it should be improved
    - Exact code replacement if possible

    Prioritize practical improvements over theoretical ones.

    File Name:
    {os.path.basename(file_path)}

    Code:
    {content}
    """
    response = llm.invoke(prompt)
    print("\n" + "=" * 80)
    print(response.content)
    exit()
elif is_review:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    prompt = f"""
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
    {os.path.basename(file_path)}

    Code:
    {content}
    """
    response = llm.invoke(prompt)
    print("\n" + "=" * 80)
    print(response.content)
    exit()
elif is_summary:
    top_doc = results[0][0]
    file_path = top_doc.metadata.get("source")
    content = read_file(file_path)
    prompt = f"""
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
    {os.path.basename(file_path)}

    Code:
    {content}
    """
    response = llm.invoke(prompt)
    print("\n" + "=" * 80)
    print(response.content)
    exit()
else:
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
    exit()