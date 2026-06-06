import json, os

MEMORY_FILE="memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_memory(memory):
    #saving data
    with open(MEMORY_FILE,"w",encoding="utf-8") as f:
        json.dump(memory,f,indent=4)
    print("Memory Updated")

def remember(key,value):
    memory = load_memory()
    memory[key]=value
    save_memory(memory)

def erase_memory(key):
    memory = load_memory()
    if key in memory:
        del memory[key]
        save_memory(memory)
        return True
    return False

def get_memory(key):
    print("Here's what I found")
    memory = load_memory()
    return memory.get(
        key,
        None
    )
def process_memory_request(command):
    command = command.lower().strip()
    if command.startswith("remember"):
        text = command[8:].strip()
        if " is " not in text:
            print("Use format: remember my key is value")
            return
        key,value = text.split(
            " is ",
            1
        )
        remember(key.strip(),value.strip())
        print(f"Remembered {key} = {value}")
    elif command.lower().startswith("what is"):

        key = command[7:].strip()

        value = get_memory(key)

        if value:
            print(
                f"{key}: {value}"
            )
        else:
            print(
                "No memory found."
            )

    elif command.lower().startswith("forget"):

        key = command[6:].strip()

        if erase_memory(key):
            print(
                f"Forgot: {key}"
            )
        else:
            print(
                "Memory not found."
            )

    else:

        print(
            "Unknown memory command."
        )

