"""Intent routing: deterministic rules first, LLM fallback second.

rule_route() is a pure function so it can be unit-tested and evaluated
without a model. llm_route() is the exact fallback the CLI uses, with the
prompt style and decoding mode exposed as parameters for experiments.
"""
import json
import re

from shivi import ollama_client

LABELS = (
    "automation",
    "memory",
    "code",
    "task",
    "qa",
    "source",
    "ingest",
    "project",
    "planner",
)

LABEL_DEFINITIONS = {
    "automation": "open or launch a desktop app, website or folder (e.g. Chrome, VS Code, YouTube)",
    "memory": "store, recall or forget a personal fact (\"remember my X is Y\", \"what is my X\", \"forget X\")",
    "code": "perform an operation on a specific source file: show, run, edit, rewrite, improve, review, find bugs in, summarize or explain it",
    "task": "add, list, complete or remove a to-do task of a project",
    "qa": "a question to be answered from the indexed documents or codebase",
    "source": "add, remove or list knowledge sources (folders or files to index)",
    "ingest": "(re)build the search index from the registered sources",
    "project": "add, remove, list, open or show tracked projects",
    "planner": "ask what to work on next or plan the day from open tasks",
}

# Few-shot examples. These are deliberately NOT taken from the evaluation
# set; the harness checks for overlap and refuses to run if any appear.
FEW_SHOT_EXAMPLES = (
    ("bring up spotify", "automation"),
    ("please note that my editor is neovim", "memory"),
    ("tidy up the error handling in loader.js", "code"),
    ("put write release notes on the todo list for website", "task"),
    ("how are embeddings cached in this repo?", "qa"),
    ("index the folder ~/work/notes as well", "source"),
    ("refresh the knowledge base", "ingest"),
    ("start tracking ~/code/blog as a project", "project"),
    ("help me plan my day", "planner"),
)

# --- deterministic rules -------------------------------------------------

CODE_EXTENSIONS = (
    "py", "js", "ts", "tsx", "jsx", "java", "c", "cpp", "h", "go", "rs",
    "rb", "md", "txt", "json", "yaml", "yml", "html", "css", "sh", "pdf",
)
FILE_PATTERN = re.compile(
    r"[\w\-./]*[\w\-]\.(?:" + "|".join(CODE_EXTENSIONS) + r")\b",
    re.IGNORECASE,
)

QA_PREFIXES = ("how", "what", "why", "when", "where", "which", "who")
INGEST_COMMANDS = {"ingest", "reingest", "re-ingest", "reindex", "re-index"}
SOURCE_PREFIXES = (
    "add source", "remove source", "delete source",
    "show sources", "list sources", "show source", "list source",
)
PROJECT_PREFIXES = (
    "add project", "remove project", "delete project",
    "show project", "list project", "open project",
)
PROJECT_QUESTIONS = (
    "what projects am i working on",
    "what projects are listed",
    "which projects are listed",
)
TASK_ACTIONS = ("add", "show", "list", "remove", "delete", "complete", "finish")
MEMORY_PREFIXES = ("remember", "forget", "recall", "what is my ", "what's my ")
PLANNER_PHRASES = ("what should i work on", "plan my day", "plan for today")
AUTOMATION_VERBS = ("open", "launch", "start")
CODE_VERBS = (
    "show", "run", "review", "summarize", "summarise", "summary",
    "explain", "improve", "edit", "rewrite", "refactor", "fix", "debug",
)


def _first_word(command):
    parts = command.split(maxsplit=1)
    return parts[0] if parts else ""


RULE_PROFILES = ("full", "precise")


def rule_route(command, profile="full"):
    """Return a label if a rule fires, else None.

    Rules are ordered from most to least specific. Earlier versions
    checked broad keyword matches first, which sent e.g.
    "add source ~/projects/x" to the project handler.

    profile="precise" drops the two broad heuristics (question word ->
    qa, open/launch/start -> automation) and leaves those requests to the
    fallback. It is an ablation: it was added after inspecting errors on
    the dev set, so its numbers must be confirmed on held-out data.
    """
    if profile not in RULE_PROFILES:
        raise ValueError(f"Unknown rule profile: {profile}")
    command = command.lower().strip()
    if not command:
        return None
    first = _first_word(command)

    if command in INGEST_COMMANDS:
        return "ingest"

    if command.startswith(SOURCE_PREFIXES):
        return "source"

    if command.startswith(PROJECT_PREFIXES) or command in PROJECT_QUESTIONS:
        return "project"

    if first in TASK_ACTIONS and re.search(r"\btasks?\b", command):
        return "task"

    if any(phrase in command for phrase in PLANNER_PHRASES):
        return "planner"

    if command.startswith(MEMORY_PREFIXES):
        return "memory"

    if profile == "full" and first in QA_PREFIXES:
        return "qa"

    if (
        profile == "full"
        and first in AUTOMATION_VERBS
        and not FILE_PATTERN.search(command)
    ):
        return "automation"

    if FILE_PATTERN.search(command) or (
        first in CODE_VERBS and re.search(r"\b(file|code|script|module)\b", command)
    ):
        return "code"

    return None


# --- LLM fallback --------------------------------------------------------

LABEL_SCHEMA = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": list(LABELS)}},
    "required": ["label"],
}


def build_prompt(command, style="few_shot"):
    if style == "zero_shot":
        # The original SHIVI prompt, kept verbatim as the baseline.
        labels = "\n    ".join(LABELS)
        return f"""
    Classify the request.

    Labels:
    {labels}

    Request: {command}

    Answer with only one label.
    """

    definitions = "\n".join(
        f"- {label}: {LABEL_DEFINITIONS[label]}" for label in LABELS
    )
    prompt = (
        "You route requests for a local developer assistant.\n"
        "Pick the single label that best describes the request.\n\n"
        f"Labels:\n{definitions}\n"
    )
    if style == "few_shot":
        examples = "\n".join(
            f"Request: {text}\nLabel: {label}" for text, label in FEW_SHOT_EXAMPLES
        )
        prompt += f"\nExamples:\n{examples}\n"
    elif style != "definitions":
        raise ValueError(f"Unknown prompt style: {style}")
    prompt += f"\nRequest: {command}\nLabel:"
    return prompt


THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


def parse_label(text):
    """Extract a label from model output (JSON or free text)."""
    text = THINK_BLOCK.sub("", text or "").strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict) and value.get("label") in LABELS:
            return value["label"]
    except (json.JSONDecodeError, TypeError):
        pass
    lowered = text.lower()
    # Prefer the last label mentioned: free-form reasoning usually ends
    # with the answer.
    found = [
        (match.start(), label)
        for label in LABELS
        for match in re.finditer(rf"\b{label}\b", lowered)
    ]
    if found:
        return max(found)[1]
    return None


def llm_route(command, model, *, style="few_shot", constrained=True,
              think=False, num_predict=None):
    """Classify with the LLM. Returns (label or None, meta)."""
    prompt = build_prompt(command, style)
    content, meta = ollama_client.chat(
        model,
        prompt,
        schema=LABEL_SCHEMA if constrained else None,
        think=think,
        num_predict=num_predict if num_predict is not None else (32 if constrained else None),
    )
    meta["raw"] = content
    return parse_label(content), meta


def classify_request(command, model, *, style="few_shot", constrained=True):
    """Hybrid router used by the CLI. Returns (label, decided_by)."""
    label = rule_route(command)
    if label is not None:
        return label, "rules"
    label, _ = llm_route(command, model, style=style, constrained=constrained)
    return label or "qa", "llm"
