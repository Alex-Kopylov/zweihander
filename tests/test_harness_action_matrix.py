"""Schema contract for the harness action matrix.

The matrix is the only source of callable names for the stage-2 renderer:
every action carries a `callable` flag, callable actions map to exactly one
name per assistant, and each assistant stores exactly one invocation wrapper.
"""

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = (
    REPO_ROOT
    / "plugins"
    / "ai-assistant-ops"
    / "skills"
    / "adapt-skill-for-ai-harness"
    / "references"
    / "harness-action-matrix.json"
)


@pytest.fixture(scope="module")
def matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def assistants(matrix) -> dict:
    return matrix["assistants"]


@pytest.fixture(scope="module")
def actions(matrix) -> dict:
    return matrix["actions"]


def test_lookup_order_is_action_then_assistant(matrix):
    assert matrix["lookup_order"] == ["action", "assistant"]


def test_every_action_declares_a_callable_flag(actions):
    for key, action in actions.items():
        assert isinstance(action.get("callable"), bool), key


def test_callable_actions_map_one_name_per_assistant(actions, assistants):
    for key, action in actions.items():
        if not action["callable"]:
            continue
        for assistant in assistants:
            name = action[assistant].get("name")
            assert isinstance(name, str) and name, f"{key}/{assistant}"


def test_reference_actions_are_non_callable(actions):
    assert actions["PluginManifest"]["callable"] is False
    assert actions["SlashCommand"]["callable"] is False


def test_single_wrapper_per_assistant(assistants, actions):
    for key, assistant in assistants.items():
        wrapper = assistant.get("invocation_wrapper")
        assert isinstance(wrapper, str) and wrapper.count("{name}") == 1, key

    for key, action in actions.items():
        for value in action.values():
            if isinstance(value, dict):
                assert "invocation_wrapper" not in value, key
                assert "invocations" not in value, key


def test_action_keys_never_equal_callable_names(actions, assistants):
    callable_names = {
        action[assistant]["name"]
        for action in actions.values()
        if action["callable"]
        for assistant in assistants
    }

    assert not callable_names & set(actions)


def test_task_tracking_splits_per_operation(actions):
    """Only the write half of the task list reaches a real Codex tool.

    `update_plan` creates and updates a plan item, so those two actions map to
    it. Reading one item, listing the plan, and stopping a tracked task have no
    Codex tool at all, so they fall back to the Claude Code name rather than
    name a tool that does not do the job.
    """
    expected = {
        "CreateTask": ("TaskCreate", "update_plan"),
        "UpdateTask": ("TaskUpdate", "update_plan"),
        "GetTask": ("TaskGet", "TaskGet"),
        "ListTasks": ("TaskList", "TaskList"),
        "StopTask": ("TaskStop", "TaskStop"),
    }

    for action_key, (claude_name, codex_name) in expected.items():
        assert actions[action_key]["callable"] is True, action_key
        assert actions[action_key]["ClaudeCode"]["name"] == claude_name
        assert actions[action_key]["Codex"]["name"] == codex_name


def test_codex_task_fallbacks_record_why(actions):
    """A fallback row states that Codex has no counterpart.

    The name alone cannot show the difference between a mapping and a
    fallback, so the reason travels with the entry and survives the next edit.
    """
    for action_key in ("GetTask", "ListTasks", "StopTask"):
        codex = actions[action_key]["Codex"]
        assert codex["name"] == actions[action_key]["ClaudeCode"]["name"], action_key
        assert "No Codex counterpart" in codex.get("note", ""), action_key


@pytest.mark.parametrize(
    ("action_key", "claude_name", "codex_name"),
    [
        ("AskUser", "AskUserQuestion", "request_user_input"),
        ("CreateAgent", "Agent", "spawn_agent"),
    ],
)
def test_mapped_mechanism_names(actions, action_key, claude_name, codex_name):
    assert actions[action_key]["ClaudeCode"]["name"] == claude_name
    assert actions[action_key]["Codex"]["name"] == codex_name


def test_dropped_legacy_fields_are_absent(matrix, actions):
    assert "InvokeSkill" not in actions

    raw = json.dumps(matrix)
    for legacy_key in ('"surface"', '"terms"'):
        assert legacy_key not in raw
