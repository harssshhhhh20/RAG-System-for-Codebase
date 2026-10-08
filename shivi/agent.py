"""Self-repair loop: run a script, and on failure ask the LLM to fix it.

Usage: python -m shivi.agent <file_path>
"""
import os
import sys

from shivi import llm
from shivi.fileops import backup_file, clean_code, read_file, run_file, write_file

MAX_ATTEMPT = 3


def fix_file(file_path, error_msg):
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
    new_code = clean_code(llm.ask(prompt))
    return write_file(file_path, new_code)


def agent_loop(file_path, max_attempts=MAX_ATTEMPT):
    """Returns the number of fix attempts used, or None if never fixed."""
    print("\nCreating Backup")
    backup_path = backup_file(file_path)
    print(f"Backup Created: {backup_path}")
    for attempt in range(max_attempts + 1):
        success, output = run_file(file_path)
        if success:
            print("Program Executed Successfully")
            print("=" * 80)
            print(output)
            return attempt
        print("Execution failed")
        print(output)
        if attempt == max_attempts:
            break
        print(f"Fix attempt {attempt + 1}/{max_attempts}...")
        if not fix_file(file_path, output):
            print("Unable to write file")
            return None
    print(f"Failed after {max_attempts} fix attempts. Original kept at {backup_path}")
    return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m shivi.agent <file_path>")
        return
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print("File not found")
        return
    agent_loop(file_path)


if __name__ == "__main__":
    main()
