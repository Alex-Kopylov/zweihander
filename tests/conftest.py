"""The shared mechanism every test in this repository runs on.

A test validates the artifact a user installs, not the authored source it was
rendered from: plugin content is reached through `rendered`, a fresh
distribution-stage render of the current sources for the harness under test.
The single exception is `tests/unit/plugin_maintenance/`, whose subject matter
is the authored tree and the template rules.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.render import Harness, render_tree


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--harness",
        choices=tuple(Harness),
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
    cover that harness. A marker naming a harness that does not exist is a
    typo rather than a narrowing, so it fails the run instead.
    """
    if "harness" not in metafunc.fixturenames:
        return

    selected = tuple(Harness)
    marker = metafunc.definition.get_closest_marker("harness")
    if marker:
        unknown = sorted(set(marker.args) - set(Harness))
        if unknown:
            raise pytest.UsageError(
                f"{metafunc.definition.nodeid}: unknown harness "
                f"{', '.join(unknown)} in @pytest.mark.harness; "
                f"supported harnesses: {', '.join(Harness)}"
            )
        selected = tuple(name for name in selected if name in marker.args)
    chosen = metafunc.config.getoption("--harness")
    if chosen:
        selected = tuple(name for name in selected if name == chosen)

    metafunc.parametrize("harness", selected, indirect=True)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--llm"):
        return

    skip = pytest.mark.skip(reason="needs --llm")
    for item in items:
        if item.get_closest_marker("llm"):
            item.add_marker(skip)


@pytest.fixture
def harness(request: pytest.FixtureRequest) -> str:
    """The harness under test, one parameter per supported harness."""
    return request.param


@pytest.fixture(scope="session")
def _rendered_trees(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str], Path]:
    """A per-harness cache of rendered trees, filled on first request.

    The cache is what makes "once per harness" true. A session-scoped
    parametrized fixture would render once per harness only as long as pytest
    never revisits a parameter, and it does: narrowing shifts parameter
    indices, so the reordering that groups them stops grouping them.

    Stage 1 is deliberately not run: it writes into the authored tree, which a
    test run must not do, and the CI gate runs the full build before the tests.
    """
    trees: dict[str, Path] = {}

    def tree_for(name: str) -> Path:
        if name not in trees:
            tree = tmp_path_factory.mktemp(f"rendered-{name}")
            render_tree(REPO_ROOT, name, tree)
            trees[name] = tree
        return trees[name]

    return tree_for


@pytest.fixture
def rendered(harness: str, _rendered_trees: Callable[[str], Path]) -> Path:
    """A fresh render of the current sources for `harness`, built once."""
    return _rendered_trees(harness)
