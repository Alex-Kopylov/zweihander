"""The shared mechanism every test in this repository runs on.

A test validates the artifact a user installs, not the authored source it was
rendered from: plugin content is reached through `rendered`, a fresh
distribution-stage render of the current sources for the harness under test.
The single exception is `tests/unit/plugin_maintenance/`, whose subject matter
is the authored tree and the template rules.
"""

from pathlib import Path

import pytest
from plugin_maintenance.paths import REPO_ROOT
from plugin_maintenance.render import Harness, render_tree


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the --harness and --llm options."""
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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Filter harness cases before fixtures run; keep their parameter indices."""
    chosen = config.getoption("--harness")
    skip_llm = pytest.mark.skip(reason="needs --llm")
    selected, deselected = [], []
    for item in items:
        marker = item.get_closest_marker("harness")
        if marker:
            unknown = sorted(set(marker.args) - set(Harness))
            if unknown:
                raise pytest.UsageError(
                    f"{item.nodeid}: unknown harness {', '.join(unknown)} "
                    f"in @pytest.mark.harness; supported harnesses: {', '.join(Harness)}"
                )
        callspec = getattr(item, "callspec", None)
        name = callspec.params.get("harness") if callspec else None
        if name is not None and ((chosen and name != chosen) or (marker and name not in marker.args)):
            deselected.append(item)
            continue
        if not config.getoption("--llm") and item.get_closest_marker("llm"):
            item.add_marker(skip_llm)
        selected.append(item)

    items[:] = selected
    if deselected:
        config.hook.pytest_deselected(items=deselected)


@pytest.fixture(scope="session", params=tuple(Harness))
def harness(request: pytest.FixtureRequest) -> str:
    """The harness under test, one parameter per supported harness."""
    return request.param


@pytest.fixture(scope="session")
def rendered(harness: str, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Render once per harness; stage 1 belongs to the build, not the tests."""
    tree = tmp_path_factory.mktemp(f"rendered-{harness}")
    render_tree(REPO_ROOT, harness, tree)
    return tree
