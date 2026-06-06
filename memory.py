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