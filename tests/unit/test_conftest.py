"""The shared mechanism's own tests, run in a throwaway pytest session.

Every other test in this repository takes `harness`, `rendered` and the two
markers on trust. These run the real `tests/conftest.py` over small probe
files through pytest's `pytester`, so what it does to a run is asserted rather
than assumed. The harness names come from `HARNESSES`, as everywhere else.
"""

import pytest

from plugin_maintenance import HARNESSES, REPO_ROOT


FIRST, SECOND = HARNESSES[0], HARNESSES[1]
INI = """\
[pytest]
markers =
    harness(name): run this test only for the named harness
    llm: calls an LLM; skipped unless --llm is given
"""


@pytest.fixture
def probe(pytester: pytest.Pytester) -> pytest.Pytester:
    """A sub-session running the real shared conftest."""
    pytester.makeini(INI)
    pytester.makeconftest(
        (REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    )
    pytester.syspathinsert(REPO_ROOT)
    return pytester


def test_each_harness_tree_is_rendered_once(probe: pytest.Pytester) -> None:
    """The regression: narrowing must not multiply renders.

    A session-scoped parametrized `harness` fixture renders a harness again
    every time pytest revisits its parameter, and marker narrowing makes it
    revisit. One temporary tree per harness is the proof it does not.
    """
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

    result.assert_outcomes(passed=6)
    trees = [
        path.name
        for path in basetemp.iterdir()
        if path.is_dir() and not path.is_symlink() and path.name.startswith("rendered-")
    ]
    assert sorted(trees) == sorted(f"rendered-{name}0" for name in HARNESSES)


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
        def test_per_harness(harness):
            pass

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

    assert result.ret != 0
    result.stdout.fnmatch_lines(["*UsageError: *unknown harness Nope*"])
