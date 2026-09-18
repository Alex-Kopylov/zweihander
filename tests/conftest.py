"""The shared mechanism every test in this repository runs on.

A test validates the artifact a user installs, not the authored source it was
rendered from: plugin content is reached through `rendered`, a fresh
distribution-stage render of the current sources for the harness under test.
The single exception is `tests/unit/plugin_maintenance/`, whose subject matter
is the authored tree and the template rules.
"""

from pathlib import Path

import pytest

from plugin_maintenance import HARNESSES, REPO_ROOT
from plugin_maintenance.render import render_tree


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--harness",
        choices=HARNESSES,
        default=None,
        help="run harness-dependent tests for this harness only",
    )
    parser.addoption(
        "--llm",
        action="store_true",
        default=False,
        help="run tests marked `llm`, which call a model",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize the harness a test runs for, narrowed by marker and option.

    A test whose marker names a harness the option excludes ends up with an
    empty parameter set and is reported skipped: the run was asked not to
    cover that harness.
    """
    if "harness" not in metafunc.fixturenames:
        return

    selected = HARNESSES
    marker = metafunc.definition.get_closest_marker("harness")
    if marker:
        selected = tuple(name for name in selected if name in marker.args)
    chosen = metafunc.config.getoption("--harness")
    if chosen:
        selected = tuple(name for name in selected if name == chosen)

    metafunc.parametrize("harness", selected, indirect=True, scope="session")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--llm"):
        return

    skip = pytest.mark.skip(reason="needs --llm")
    for item in items:
        if item.get_closest_marker("llm"):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def harness(request: pytest.FixtureRequest) -> str:
    """The harness under test, one parameter per supported harness."""
    return request.param


@pytest.fixture(scope="session")
def rendered(harness: str, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A fresh render of the current sources for `harness`.

    Session-scoped, so the tree is built once per harness. Stage 1 is
    deliberately not run: it writes into the authored tree, which a test run
    must not do, and the CI gate runs the full build before the tests.
    """
    tree = tmp_path_factory.mktemp("rendered") / harness
    render_tree(REPO_ROOT, harness, tree)
    return tree
