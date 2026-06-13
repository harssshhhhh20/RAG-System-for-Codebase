import json, os, subprocess

from shivi.config import PROJECTS_FILE

def normalize_project_name(name):
    return (
        name
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

def load_projects():

    if not os.path.exists(PROJECTS_FILE):
        return {}

    with open(
        PROJECTS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        try:
            return json.load(f)

        except json.JSONDecodeError:
            return {}

def save_projects(projects):

    with open(
        PROJECTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            projects,
            f,
            indent=4
        )

def add_project(path):

    path = os.path.abspath(path)

    if not os.path.exists(path):
        print("Path does not exist.")
        return False

    name = normalize_project_name(
        os.path.basename(path)
    )
    projects = load_projects()

    projects[name] = {
        "path": path,
        "status": "active"
    }

    save_projects(projects)

    print(
        f"Added project: {name}"
    )
    return True

def remove_project(name):

    projects = load_projects()

    if name not in projects:
        print("Project not found.")
        return

    del projects[name]

    save_projects(projects)

    print(
        f"Removed project: {name}"
    )

def get_project(name):

    name = normalize_project_name(name)
    projects = load_projects()

    return projects.get(
        name,
        None
    )

def list_projects():

    projects = load_projects()

    if not projects:
        print("No projects found.")
        return

    print("\nProjects:\n")

    for name, info in projects.items():

        print(
            f"- {name}"
        )

def open_project(name):

    project = get_project(name)

    if not project:
        print("Project not found.")
        return

    path = project["path"]

    os.system(
        f'open "{path}"'
    )

    print(
        f"Opened project: {name}"
    )

def process_project_request(command):

    command = command.lower().strip()

    if command == "what projects am i working on":

        list_projects()
        return

    if command.startswith("open project "):

        project_name = (
            command
            .replace(
                "open project ",
                ""
            )
            .strip()
        )

        open_project(
            project_name
        )

        return

    if command.startswith("remove project "):

        project_name = (
            command
            .replace(
                "remove project ",
                ""
            )
            .strip()
        )

        remove_project(
            project_name
        )

        return

    if command.startswith("add project "):

        project_path = (
            command
            .replace(
                "add project ",
                ""
            )
            .strip()
        )

        add_project(
            project_path
        )

        return

    if command in [
    "what projects am i working on",
    "show projects",
    "list projects",
    "what projects are listed",
    "which projects are listed"
    ]:
        list_projects()
        return

    if command.startswith("show project "):
        project_name = command.replace(
            "show project ",
            ""
        ).strip()

        project = get_project(
            project_name
        )

        if project:
            print(
                f"\nName: {project_name}"
            )
            print(
                f"Path: {project['path']}"
            )
            print(
                f"Status: {project['status']}"
            )

        return

    print(
        "Unknown project command."
    )