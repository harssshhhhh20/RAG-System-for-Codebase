import json
import os

from shivi.projects import (
    normalize_project_name,
    get_project
)

from shivi.config import TASKS_FILE

def load_tasks():

    if not os.path.exists(
        TASKS_FILE
    ):
        return {}

    with open(
        TASKS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        try:
            return json.load(f)

        except json.JSONDecodeError:
            return {}

def save_tasks(tasks):

    with open(
        TASKS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            tasks,
            f,
            indent=4
        )

def add_task(project,task):
    project = normalize_project_name(project)
    if not get_project(project):
        print("Project does not exist.")
        return
    tasks = load_tasks()
    if project not in tasks:
        tasks[project] = []
    for existing_task in tasks[project]:
        if (
            existing_task["task"]
            .lower()
            ==
            task.lower()
        ):
            print("Task already exists.")
            return
    tasks[project].append(
        {
            "task": task,
            "status": "todo"
        }
    )

    save_tasks(tasks)

    print(
        f"Added task to {project}"
    )

def list_tasks(project):

    project = normalize_project_name(
        project
    )

    tasks = load_tasks()

    if project not in tasks:

        print(
            "Project not found."
        )

        return

    print(
        f"\nTasks for {project}:\n"
    )

    for index, item in enumerate(
        tasks[project],
        start=1
    ):

        print(
            f"{index}. "
            f"{item['task']} "
            f"[{item['status']}]"
        )

def complete_task(
    project,
    task_name
):

    project = normalize_project_name(
        project
    )

    tasks = load_tasks()

    if project not in tasks:
        return False

    for task in tasks[project]:

        if (
            task["task"]
            .lower()
            ==
            task_name.lower()
        ):

            task["status"] = "done"

            save_tasks(tasks)

            print(
                f"Completed: {task_name}"
            )

            return True

    return False

def remove_task(
    project,
    task_name
):

    project = normalize_project_name(
        project
    )

    tasks = load_tasks()

    if project not in tasks:
        return False

    original_count = len(
        tasks[project]
    )

    tasks[project] = [
        task
        for task in tasks[project]
        if task["task"].lower()
        !=
        task_name.lower()
    ]

    if (
        len(tasks[project])
        ==
        original_count
    ):
        return False

    save_tasks(tasks)

    print(
        f"Removed: {task_name}"
    )

    return True

def get_active_tasks():

    tasks = load_tasks()

    active = []

    for project in tasks:

        for task in tasks[project]:

            if (
                task["status"]
                !=
                "done"
            ):

                active.append(
                    (
                        project,
                        task["task"]
                    )
                )

    return active

def process_task_request(command):

    command = command.strip().lower()

    if command.startswith(
        "show tasks for "
    ):

        project = (
            command
            .replace(
                "show tasks for ",
                ""
            )
            .strip()
        )

        list_tasks(project)

        return

    if command.startswith(
        "add task "
    ):

        text = (
            command
            .replace(
                "add task ",
                ""
            )
            .strip()
        )

        if " to " not in text:

            print(
                "Use: add task <task> to <project>"
            )

            return

        task_name, project = text.rsplit(
            " to ",
            1
        )

        add_task(
            project.strip(),
            task_name.strip()
        )

        return

    if command.startswith(
        "complete task "
    ):

        text = (
            command
            .replace(
                "complete task ",
                ""
            )
            .strip()
        )

        if " in " not in text:
            print(
                "Use: complete task <task> in <project>"
            )
            return
        task_name, project = text.rsplit(
            " in ",
            1
        )
        complete_task(
            project.strip(),
            task_name.strip()
        )
        return
    if command.startswith(
        "remove task "
    ):
        text = (
            command
            .replace(
                "remove task ",
                ""
            )
            .strip()
        )
        if " from " not in text:

            print(
                "Use: remove task <task> from <project>"
            )

            return

        task_name, project = text.rsplit(
            " from ",
            1
        )

        remove_task(
            project.strip(),
            task_name.strip()
        )

        return

    print(
        "Unknown task command."
    )