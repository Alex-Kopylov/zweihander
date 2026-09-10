"""The interview skill's decision log, which is also its progress counter.

Every count comes back out of the file the walk-through wrote, so an
interrupted run keeps its record and the bar cannot drift from the decisions
actually taken.
"""

import re
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SKILL_DIR = REPO_ROOT / "plugins" / "work-session-tools" / "skills" / "interview"
SCRIPT = SKILL_DIR / "scripts" / "decision_log.sh"
SKILL_TEMPLATE = SKILL_DIR / "SKILL.md.j2"
DIR_ENV = "INTERVIEW_DECISION_LOG_DIR"
DIR_NAME = "interview-decision-logs"


def sourced(script: str) -> str:
    """Run against the sourced script, so nothing is dispatched."""
    done = subprocess.run(
        ["bash", "-c", f'source "{SCRIPT}"; {script}'],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.rstrip("\n")


# Read from the script rather than restated here, so the two cannot drift apart.
BAR_WIDTH = int(sourced('printf "%s" "$BAR_WIDTH"'))


@pytest.fixture(autouse=True)
def log_dir(tmp_path, monkeypatch) -> Path:
    """Point every run at its own directory, through the documented override."""
    directory = tmp_path / "logs"
    monkeypatch.setenv(DIR_ENV, str(directory))
    return directory


def run(*argv: str) -> str:
    done = subprocess.run([SCRIPT, *argv], capture_output=True, text=True, check=True)
    return done.stdout.rstrip("\n")


def fails(*argv: str) -> str:
    """Run a call that must be rejected and return what it said on stderr."""
    done = subprocess.run([SCRIPT, *argv], capture_output=True, text=True)

    assert done.returncode == 1, f"expected a failure, got: {done.stdout!r}"
    return done.stderr


def bar(taken: int, total: int) -> str:
    return sourced(f"bar {taken} {total}")


def start(total: int = 10, name: str = "pr-68-review") -> Path:
    return Path(run("start", "--total", str(total), "--name", name).splitlines()[0])


class TestBar:
    def test_documented_shape_renders(self):
        assert bar(3, 10) == "▰▰▰▱▱▱▱▱▱▱  3/10"

    def test_one_cell_per_item_up_to_the_width(self):
        assert bar(0, 4) == "▱▱▱▱  0/4"
        assert bar(4, 4) == "▰▰▰▰  4/4"

    def test_long_queue_scales_to_the_width(self):
        cells, count = bar(25, 50).split("  ")

        assert len(cells) == BAR_WIDTH
        assert cells.count("▰") == BAR_WIDTH // 2
        assert count == "25/50"

    def test_an_unfinished_queue_keeps_a_cell_empty(self):
        cells = bar(49, 50).split("  ")[0]

        assert len(cells) == BAR_WIDTH
        assert cells.count("▱") == 1

    def test_the_first_decision_fills_a_cell(self):
        assert bar(1, 50).split("  ")[0].count("▰") == 1


class TestStart:
    def test_file_name_carries_timestamp_then_name(self):
        log = start(name="PR 68 review!")

        assert re.fullmatch(r"\d{8}-\d{6}-pr-68-review\.md", log.name)

    def test_missing_directory_is_created(self, log_dir):
        log = start()

        assert log.is_file()
        assert log.parent == log_dir

    def test_fresh_log_reports_an_empty_bar(self):
        printed = run("start", "--total", "4", "--name", "x")

        assert printed.splitlines()[1] == "▱▱▱▱  0/4"

    def test_nameless_name_fails_loudly(self):
        assert "file name" in fails("start", "--total", "4", "--name", "!!!")

    def test_total_below_one_fails_loudly(self):
        assert "items" in fails("start", "--total", "0", "--name", "x")

    def test_default_directory_falls_back_to_the_temp_directory(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.delenv(DIR_ENV)
        monkeypatch.setenv("TMPDIR", str(tmp_path / "systmp"))

        assert start().parent == tmp_path / "systmp" / DIR_NAME


class TestRecord:
    def test_one_item_appends_one_row(self):
        log = start()

        printed = run(
            "record",
            "--log",
            str(log),
            "--item",
            "#3 HIGH — Missing null check",
            "--decision",
            "Fix now",
            "--note",
            "add null check with default",
        )

        assert printed == (
            "#3 HIGH — Missing null check: **Fix now** (add null check with default)\n"
            "▰▱▱▱▱▱▱▱▱▱  1/10"
        )
        assert (
            "| #3 HIGH — Missing null check | Fix now | add null check with default |"
            in log.read_text(encoding="utf-8")
        )

    def test_grouped_items_share_one_decision_and_move_the_bar_once_per_item(self):
        log = start()

        printed = run(
            "record",
            "--log",
            str(log),
            "--item",
            "#2 MED — Unused import",
            "--item",
            "#5 MED — Unused variable",
            "--decision",
            "Fix now",
        )

        assert printed.splitlines()[-1] == "▰▰▱▱▱▱▱▱▱▱  2/10"
        assert log.read_text(encoding="utf-8").count("| Fix now |") == 2

    def test_count_comes_from_the_file_not_the_caller(self):
        log = start()
        for index in range(3):
            run("record", "--log", str(log), "--item", f"#{index}", "--decision", "Skip")

        printed = run("record", "--log", str(log), "--item", "#9", "--decision", "Skip")

        assert printed.splitlines()[-1] == "▰▰▰▰▱▱▱▱▱▱  4/10"

    def test_column_break_in_a_field_is_escaped(self):
        log = start()

        run("record", "--log", str(log), "--item", "#1 a | b", "--decision", "Fix\nnow")

        row = log.read_text(encoding="utf-8").splitlines()[-1]
        assert row == r"| #1 a \| b | Fix now |  |"

    def test_amending_an_already_recorded_item_does_not_move_the_bar(self):
        log = start(total=2)
        run("record", "--log", str(log), "--item", "#1", "--decision", "Fix now")

        printed = run("record", "--log", str(log), "--item", "#1", "--decision", "Skip")

        assert printed.splitlines()[-1] == "▰▱  1/2"
        assert log.read_text(encoding="utf-8").count("| #1 |") == 2

    def test_missing_log_fails_loudly(self, tmp_path):
        stderr = fails(
            "record",
            "--log",
            str(tmp_path / "absent.md"),
            "--item",
            "#1",
            "--decision",
            "Skip",
        )

        assert "start" in stderr


class TestExtend:
    def test_new_items_raise_the_total(self):
        log = start(total=3)
        run("record", "--log", str(log), "--item", "#1", "--decision", "Fix now")

        printed = run("extend", "--log", str(log), "--by", "2")

        assert printed == "▰▱▱▱▱  1/5"
        assert "total: 5" in log.read_text(encoding="utf-8")

    def test_extending_by_nothing_fails_loudly(self):
        log = start()

        assert "no items" in fails("extend", "--log", str(log), "--by", "0")


class TestShow:
    def test_log_prints_with_the_bar_last(self):
        log = start(total=2)
        run("record", "--log", str(log), "--item", "#1 Naming", "--decision", "Skip")

        printed = run("show", "--log", str(log))

        assert "| #1 Naming | Skip |  |" in printed
        assert printed.splitlines()[-1] == "▰▱  1/2"


def test_the_skill_runs_the_script_it_ships():
    """A shell script only runs if the tree carries its executable bit."""
    assert SCRIPT.stat().st_mode & 0o111, f"{SCRIPT} is not executable"
    assert "scripts/decision_log.sh" in SKILL_TEMPLATE.read_text(encoding="utf-8")


def test_skill_declares_the_same_default_directory():
    """The skill's declared default and the script's fallback stay one value."""
    declared = re.search(
        r"decision-log-dir: \"(?P<dir>[^\"]+)\"",
        SKILL_TEMPLATE.read_text(encoding="utf-8"),
    )

    assert declared, "SKILL.md must declare metadata.config.decision-log-dir"
    assert declared.group("dir") in SCRIPT.read_text(encoding="utf-8")
