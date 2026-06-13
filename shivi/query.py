import os, sys, subprocess, shutil, re, difflib, json
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from shivi.config import DB_PATH, FILENAME_INDEX_FILE

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

def show_changes(old_content, new_content):
    diff = difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        fromfile="Original",
        tofile="Modified",
        lineterm=""
    )
    return "\n".join(diff)

def run_file(exec_file):
    ext = os.path.splitext(exec_file)[1].lower()
    commands = {
        ".py": [sys.executable, exec_file],
        ".js": ["node", exec_file],
        ".java": ["java", exec_file]
    }
    if ext not in commands:
        return (
            False,
            f"Execution not supported for {ext}"
        )
    try:
        result = subprocess.run(
            commands[ext],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        error = result.stderr
        return(
            result.returncode==0,
            output if output else error
        )
    except Exception as e:
        return(
            False,
            str(e)
        )


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

def load_filename_index():
    with open(
        FILENAME_INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)

def process_code_request(question):

    file_selected_by_index = False
    filename_index = load_filename_index()
    target_filename = extract_file_name(question)
    print(f"Extracted: {target_filename}")
    if (
        target_filename and
        target_filename.lower()
        in filename_index
    ):
        file_selected_by_index = True
        file_path = filename_index[
            target_filename.lower()
        ]
        print(
            f"\nSelected File: {file_path}"
        )
        content = read_file(file_path)
        context = content
    if file_selected_by_index:
        results = []
    elif target_filename:
        print("File Not Found")
        return
    else:
        results = vector_store.similarity_search_with_score(
            question,
            k=3
        )
    if not file_selected_by_index:

        if not results:
            print("No relevant documents found.")
            return

        top_doc = results[0][0]

        file_path = top_doc.metadata.get("source")

        print(f"\nSelected File: {file_path}")

        content = read_file(file_path)

    if not file_selected_by_index:
        context = "\n\n".join(
            doc.page_content
            for doc, score in results
        )

    def llm_check_intent(question,llm):
        prompt = f"""
            Return one label only:

            show
            run
            review
            bug
            improve
            edit
            rewrite
            summary
            explain
            locate

            Question:
            {question}
            """
        response = llm.invoke(prompt)
        intent = response.content.lower().strip()

        if not intent:
            return "review"

        return intent.split()[0]

    def check_intent(command):
        command = command.lower().strip()

        if command.startswith("show"):
            return "show"

        if command.startswith("run"):
            return "run"

        if command.startswith("review"):
            return "review"

        if command.startswith("summarize"):
            return "summary"

        if command.startswith("summary"):
            return "summary"

        if command.startswith("explain"):
            return "explain"

        if command.startswith("improve"):
            return "improve"

        if command.startswith("edit"):
            return "edit"

        if command.startswith("rewrite"):
            return "rewrite"

        if command.startswith("locate"):
            return "locate"

        if command.startswith("find bug"):
            return "bug"

        if command.startswith("find bugs"):
            return "bug"

        if command.startswith("bug"):
            return "bug"
        if command.startswith("which file"):
            return "locate"

        if command.startswith("where is"):
            return "locate"

        if command.startswith("which module"):
            return "locate"

        if command.startswith("which script"):
            return "locate"
        
        return llm_check_intent(command,llm)
    
    intent = check_intent(question)

    VALID_INTENTS = {
        "edit",
        "rewrite",
        "show",
        "review",
        "summary",
        "bug",
        "run",
        "locate",
        "improve",
        "explain",
    }

    if intent not in VALID_INTENTS:
        intent = "review"

    if intent == "rewrite":

        prompt = f"""
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
        """
        response = llm.invoke(prompt)
        new_code = response.content.strip()
        if new_code.startswith("```"):
            lines = new_code.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            new_code = "\n".join(lines)
        print("\nProposed Changes:\n")
        print("=" * 80)
        diff_text = show_changes(
            content,
            new_code
        )
        if not diff_text.strip():
            print("\nNo changes detected.")
            return
        print(diff_text)
        choice = input("\nApply Changes(y/n): ")
        if choice.lower() == "y":
            backup_path = backup_file(
                file_path
            )
            success = write_file(
                file_path,
                new_code
            )
            if success:
                print(f"Backup created: {backup_path}")
                print("File updated successfully")
            else:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                print("File update failed")
        else:
            print("Changes Discarded")
        return
    if intent=="edit":
        file_extension = os.path.splitext(file_path)[1]
        prompt = f"""
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
        """
        response = llm.invoke(prompt)
        new_code = response.content.strip()
        if new_code.startswith("```"):
            lines = new_code.splitlines()

            lines = lines[1:]

            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]

            new_code = "\n".join(lines)
        print("\nProposed Changes:\n")
        print("=" * 80)
        diff_text = show_changes(content,new_code)
        if not diff_text.strip():
            print("\nNo changes detected.")
            return
        print(diff_text)
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
    elif intent=="show":
        print(f"\nFile: {file_path}")
        print("\n" + "=" * 80)
        print(content)

        return
    elif intent=="explain":
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

        return
    elif intent=="bug":
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

        return
    elif intent=="improve":
        file_extension = os.path.splitext(file_path)[1]
        prompt = f"""
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
        """
        response = llm.invoke(prompt)
        new_code = response.content.strip()
        if new_code.startswith("```"):
            lines = new_code.splitlines()  
            lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
                new_code = "\n".join(lines)
        print("\nProposed Changes:\n")
        print("=" * 80)
        diff_text = show_changes(content,new_code)
        if not diff_text.strip():
            print("\nNo changes detected.")
            return
        print(diff_text)
        choice = input("\nApply Changes(y/n): ")
        if choice.lower()=="y":
            backup_path = backup_file(file_path)
        
            success = write_file(file_path, new_code)
        
            if success:
                print(f"Backup created: {backup_path}")
                print("File updated successfully")
                want_to_run = input("You want to test the file(y/n): ")
                if want_to_run.lower() == "y":
                    run_success,result = run_file(file_path)
                    print("Output:")
                    print("="*80)
                    print(result)
                    return
                else:
                    print("Changes made but user declined the test run")
            else:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                print("File update failed")
        else:
            print("Changes Discarded")
    elif intent=="review":
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
        return
    elif intent=="summary":
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
        return
    elif intent == "run" :
        success,result = run_file(file_path)
        print("Output Expected:")
        print("="*80)
        if success:
            print(result)
        else:
            print(f"Error in excecution:\n{result}")
        return
    elif intent == "locate":
        top_doc = results[0][0]
        file_path = top_doc.metadata.get(
            "source",
            "unknown"
        )
        print(f"\nFound in: {file_path}")
        return

if __name__ == "__main__":
    question = input("Enter your query")
    process_code_request(question)