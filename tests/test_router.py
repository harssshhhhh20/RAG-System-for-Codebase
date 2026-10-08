import json

import pytest

from shivi.router import (
    FEW_SHOT_EXAMPLES,
    LABELS,
    build_prompt,
    parse_label,
    rule_route,
)


@pytest.mark.parametrize("command, label", [
    ("ingest", "ingest"),
    ("add source ~/notes", "source"),
    ("show sources", "source"),
    ("add project ~/code/shivi", "project"),
    ("open project shivi", "project"),
    ("add task write tests to shivi", "task"),
    ("show tasks", "task"),
    ("what should i work on today", "planner"),
    ("remember my name is harsh", "memory"),
    ("what is my name", "memory"),
    ("forget my birthday", "memory"),
    ("how does ingestion work?", "qa"),
    ("open chrome", "automation"),
    ("explain query.py", "code"),
    ("run hello.py", "code"),
])
def test_canonical_commands(command, label):
    assert rule_route(command) == label


@pytest.mark.parametrize("command, label", [
    # Used to hit the project rule because the path contains "project".
    ("add source ~/projects/api", "source"),
    # Used to hit automation because "open" was matched anywhere.
    ("open project rag_agent", "project"),
    # "start" inside another word must not trigger automation.
    ("restart the task runner", None),
    # A file name wins over open/launch/start.
    ("open query.py and explain it", "code"),
    # Recall used to be shadowed by the generic "what" question rule.
    ("what is my github username", "memory"),
    # Paths in task names are still tasks.
    ("add task fix query.py to shivi", "task"),
])
def test_regressions(command, label):
    assert rule_route(command) == label


def test_unmatched_request_falls_through():
    assert rule_route("i need the browser") is None
    assert rule_route("") is None


def test_precise_profile_drops_broad_rules():
    assert rule_route("which projects do i have?", profile="full") == "qa"
    assert rule_route("which projects do i have?", profile="precise") is None
    assert rule_route("open my rag_agent project", profile="precise") is None
    assert rule_route("add source ~/notes", profile="precise") == "source"


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        rule_route("ingest", profile="loose")


@pytest.mark.parametrize("text, label", [
    (json.dumps({"label": "task"}), "task"),
    ("<think>maybe memory... no</think>\nautomation", "automation"),
    ("The answer is: qa", "qa"),
    ("It mentions project but the label is source", "source"),
    ("no idea", None),
    ("", None),
])
def test_parse_label(text, label):
    assert parse_label(text) == label


@pytest.mark.parametrize("style", ["zero_shot", "definitions", "few_shot"])
def test_prompts_mention_every_label(style):
    prompt = build_prompt("open chrome", style)
    assert "open chrome" in prompt
    assert all(label in prompt for label in LABELS)


def test_unknown_prompt_style_rejected():
    with pytest.raises(ValueError):
        build_prompt("x", "chain_of_thought")


def test_few_shot_examples_use_valid_labels():
    assert {label for _, label in FEW_SHOT_EXAMPLES} == set(LABELS)
