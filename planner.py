from tasks import get_active_tasks

def get_work_today():
    active_tasks = get_active_tasks()
    if not active_tasks:
        print("No active tasks pending")
        return
    print("Suggested Work:\n")
    for project,task in active_tasks:
        print(f"{project}-->{task}")

def process_planner_request(request):
    command = request.lower().strip()
    if("what should i work on today") in command:
        get_work_today()
        return
    print("Unknown Planner Command")

if __name__=="__main__":
    command = input("Enter your request")
    process_planner_request(command)