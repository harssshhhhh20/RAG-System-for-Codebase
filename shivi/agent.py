import os, shutil, subprocess, sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama

MAX_ATTEMPT = 3
llm = ChatOllama(
    model="qwen3:4b",
    temperature=0
)

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

def clean_code(code):
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        lines = lines[1:]
        if(
            lines and lines[-1].startswith("```")
        ):
            lines = lines[:-1]
        code = "\n".join(lines)
    return code

def fix_file(file_path,error_msg):
    content = read_file(file_path)
    prompt = f"""
        You are a senior software engineer.

        The following file failed during execution.

        File:
        {file_path}

        Code:
        {content}

        Execution Error:
        {error_msg}

        Fix the error.

        Rules:

        1. Preserve functionality.
        2. Make minimal changes.
        3. Return ONLY the corrected code.
        4. No explanations.
        5. No markdown fences.
    """
    response = llm.invoke(prompt)
    new_code = clean_code(response.content)
    success = write_file(file_path, new_code)
    return success

def agent_loop(file_path):
    print("\nCreating Backup")
    backup_path = backup_file(file_path)
    print("Backup Created")
    for attempt in range(1,MAX_ATTEMPT+1):
        print(f"Attempt: {attempt}")
        success, output = run_file(file_path)
        if success:
            print("Program Executed Successfully")
            print("="*80)
            print(output)
            return
        print("Execution failed")
        print(output)
        print("Retrying...")
        fixed = fix_file(file_path,output)
        if not fixed:
            print("Unable to write file")
            return
    print(f"Failed after {attempt} attempts")


def main():
    if len(sys.argv)!=2:
        print("Usage: python agent.py <file_path>")
        return
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print("File not found")
        return
    agent_loop(file_path)

if __name__ == "__main__":
    main()
    

