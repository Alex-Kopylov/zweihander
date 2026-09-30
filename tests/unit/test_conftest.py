"""The shared mechanism's own tests, run in a throwaway pytest session.

Every other test in this repository takes `harness`, `rendered` and the two
markers on trust. These run the real `tests/conftest.py` over small probe
files through pytest's `pytester`, so what it does to a run is asserted rather
than assumed. The harness names come from `Harness`, as everywhere else.
"""

import pytest
from plugin_maintenance.paths import REPO_ROOT
from plugin_maintenance.render import Harness

FIRST, SECOND, *_ = Harness


@pytest.fixture
def probe(pytester: pytest.Pytester) -> pytest.Pytester:
    """A sub-session running the real shared conftest."""
    pytester.makeini((REPO_ROOT / "pytest.ini").read_text(encoding="utf-8"))
    pytester.makeconftest((REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8"))
    pytester.syspathinsert(REPO_ROOT)
    return pytester


def test_each_harness_tree_is_rendered_once(probe: pytest.Pytester) -> None:
    """Marker filtering across modules must not multiply session renders."""
    probe.makepyfile(
        test_a="""
        def test_every_harness(rendered):
            assert rendered.is_dir()
        """,
        test_b=f"""
        import pytest

        @pytest.mark.harness("{SECOND}")
        def test_second_only(rendered):
            assert rendered.is_dir()
        """,
        test_c="""
        def test_every_harness_again(rendered):
            assert rendered.is_dir()
        """,
        test_d=f"""
        import pytest

        @pytest.mark.harness("{FIRST}")
        def test_first_only(rendered):
            assert rendered.is_dir()
        """,
    )
    basetemp = probe.path / "basetemp"

    result = probe.runpytest_inprocess(f"--basetemp={basetemp}")

    result.assert_outcomes(passed=2 * len(Harness) + 2, deselected=2 * (len(Harness) - 1))
    trees = [
        path.name
        for path in basetemp.iterdir()
        if path.is_dir() and not path.is_symlink() and path.name.startswith("rendered-")
    ]
    assert sorted(trees) == sorted(f"rendered-{name}0" for name in Harness)


def test_llm_marked_test_waits_for_its_option(probe: pytest.Pytester) -> None:
    probe.makepyfile(
        test_probe="""
        import pytest

        @pytest.mark.llm
        def test_calls_a_model():
            pass
        """
    )

    probe.runpytest_inprocess().assert_outcomes(skipped=1)
    probe.runpytest_inprocess("--llm").assert_outcomes(passed=1)


def test_harness_option_excludes_every_other_harness(probe: pytest.Pytester) -> None:
    probe.makepyfile(
        test_probe="""
        def test_per_harness(harness, rendered):
            assert rendered.is_dir()

        def test_harness_independent():
            pass
        """
    )

    result = probe.runpytest_inprocess("--harness", FIRST, "--collect-only", "-q")

    collected = [line for line in result.outlines if line.startswith("test_probe.py::")]
    assert collected == [
        f"test_probe.py::test_per_harness[{FIRST}]",
        "test_probe.py::test_harness_independent",
    ]

    basetemp = probe.path / "basetemp"
    result = probe.runpytest_inprocess("--harness", FIRST, f"--basetemp={basetemp}")

    result.assert_outcomes(passed=2, deselected=len(Harness) - 1)
    trees = [path.name for path in basetemp.glob("rendered-*") if not path.is_symlink()]
    assert trees == [f"rendered-{FIRST}0"]


def test_unknown_harness_name_fails_the_run(probe: pytest.Pytester) -> None:
    probe.makepyfile(
        test_probe="""
        import pytest

        @pytest.mark.harness("Nope")
        def test_typo(harness):
            pass
        """
    )

    result = probe.runpytest_inprocess()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*ERROR: *unknown harness Nope*"])


@pytest.mark.parametrize("chosen", tuple(Harness))
def test_marker_and_option_select_only_their_intersection(probe: pytest.Pytester, chosen: str) -> None:
    probe.makepyfile(
        test_probe=f"""
        import pytest

        @pytest.mark.harness("{FIRST}")
        def test_first_only(harness):
            assert harness == "{FIRST}"

        def test_independent():
            pass
        """
    )

    result = probe.runpytest_inprocess("--harness", chosen)

    selected = int(chosen == FIRST)
    result.assert_outcomes(passed=1 + selected, deselected=len(Harness) - selected)


def test_unregistered_marker_fails_collection(probe: pytest.Pytester) -> None:
    probe.makepyfile(
        test_probe="""
        import pytest

        @pytest.mark.unregistered
        def test_typo():
            pass
        """
    )

    result = probe.runpytest_inprocess()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*'unregistered' not found in*markers*configuration option*"])
