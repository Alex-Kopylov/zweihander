"""Schema contract for the harness frontmatter matrix.

The matrix is the only source of frontmatter placement for the stage-2
renderer: every key carries a value form and one placement per assistant, and
the renderer registers one template global per placed key.
"""

import json
from pathlib import Path

import pytest

from plugin_maintenance.render import (
    FRONTMATTER_MATRIX_NAME,
    MATRIX_PATH,
    PLACEMENTS,
    VALUE_FORMS,
    VERBATIM_FORM,
    BuildError,
    load_frontmatter_matrix,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER_MATRIX_PATH = (REPO_ROOT / MATRIX_PATH).with_name(FRONTMATTER_MATRIX_NAME)


@pytest.fixture(scope="module")
def matrix() -> dict:
    return json.loads(FRONTMATTER_MATRIX_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def keys(matrix) -> dict:
    return matrix["keys"]


@pytest.fixture(scope="module")
def assistants(matrix) -> dict:
    return matrix["assistants"]


def test_matrix_sits_beside_the_action_matrix():
    assert FRONTMATTER_MATRIX_PATH.is_file()


def test_lookup_order_is_key_then_assistant(matrix):
    assert matrix["lookup_order"] == ["key", "assistant"]


def test_every_key_declares_a_documented_form(matrix, keys):
    for key, entry in keys.items():
        assert entry["form"] in matrix["forms"], key


def test_every_placed_form_is_one_the_renderer_can_write(keys):
    for key, entry in keys.items():
        if entry["form"] == VERBATIM_FORM:
            continue
        assert entry["form"] in VALUE_FORMS, key


def test_every_key_places_itself_for_every_assistant(keys, assistants):
    for key, entry in keys.items():
        for assistant in assistants:
            assert entry[assistant]["placement"] in PLACEMENTS, f"{key}/{assistant}"


def test_the_portable_pair_is_verbatim_and_top_level_everywhere(keys, assistants):
    """`name` and `description` are the two keys every harness documents."""
    for key in ("name", "description"):
        assert keys[key]["form"] == VERBATIM_FORM
        for assistant in assistants:
            assert keys[key][assistant]["placement"] == "top-level"


def test_claude_code_only_keys_travel_in_codex_metadata(keys):
    for key in ("allowed-tools", "argument-hint", "arguments"):
        assert keys[key]["ClaudeCode"]["placement"] == "top-level"
        assert keys[key]["Codex"]["placement"] == "metadata"


def test_every_key_records_its_intent(keys):
    for key, entry in keys.items():
        assert isinstance(entry.get("intent"), str) and entry["intent"], key


def test_a_metadata_placement_records_why(keys):
    """A key a harness does not read carries the note saying so."""
    for key, entry in keys.items():
        for assistant, placement in entry.items():
            if not isinstance(placement, dict):
                continue
            if placement["placement"] == "metadata":
                assert placement.get("note"), f"{key}/{assistant}"


def test_every_assistant_records_where_the_facts_came_from(assistants):
    for key, assistant in assistants.items():
        assert assistant["source_urls"], key


def test_namespaces_and_placed_keys_never_collide(matrix, keys):
    """A placed key already names a `metadata` entry; a namespace may not."""
    placed = {key for key, entry in keys.items() if entry["form"] != VERBATIM_FORM}

    assert not placed & set(matrix["metadata_namespaces"])


class TestLoaderRejects:
    def write(self, tmp_path: Path, matrix: dict) -> Path:
        path = tmp_path / FRONTMATTER_MATRIX_NAME
        path.write_text(json.dumps(matrix), encoding="utf-8")
        return path

    def test_missing_file_names_the_path(self, tmp_path):
        with pytest.raises(BuildError, match=FRONTMATTER_MATRIX_NAME):
            load_frontmatter_matrix(tmp_path / FRONTMATTER_MATRIX_NAME)

    def test_empty_keys_section_fails(self, tmp_path, matrix):
        broken = {**matrix, "keys": {}}

        with pytest.raises(BuildError, match="non-empty"):
            load_frontmatter_matrix(self.write(tmp_path, broken))

    def test_form_the_matrix_does_not_document_fails(self, tmp_path, matrix):
        broken = json.loads(json.dumps(matrix))
        broken["keys"]["arguments"]["form"] = "prose"

        with pytest.raises(BuildError, match="undocumented form"):
            load_frontmatter_matrix(self.write(tmp_path, broken))

    def test_form_the_renderer_cannot_write_fails(self, tmp_path, matrix):
        broken = json.loads(json.dumps(matrix))
        broken["forms"]["prose"] = "Documented but unimplemented."
        broken["keys"]["arguments"]["form"] = "prose"

        with pytest.raises(BuildError, match="cannot write"):
            load_frontmatter_matrix(self.write(tmp_path, broken))

    def test_unknown_placement_fails(self, tmp_path, matrix):
        broken = json.loads(json.dumps(matrix))
        broken["keys"]["arguments"]["Codex"]["placement"] = "footer"

        with pytest.raises(BuildError, match="footer"):
            load_frontmatter_matrix(self.write(tmp_path, broken))

    def test_missing_placement_for_one_assistant_fails(self, tmp_path, matrix):
        broken = json.loads(json.dumps(matrix))
        del broken["keys"]["arguments"]["Codex"]

        with pytest.raises(BuildError, match="arguments"):
            load_frontmatter_matrix(self.write(tmp_path, broken))
