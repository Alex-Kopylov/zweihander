"""The interview skill's decision log, which is also its progress counter.

Every count comes back out of the file the walk-through wrote, so an
interrupted run keeps its record and the bar cannot drift from the decisions
actually taken.
"""

import importlib.util
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "plugins" / "work-session-tools" / "skills" / "interview"
SCRIPT_PATH = SKILL_DIR / "scripts" / "decision_log.py"
SKILL_TEMPLATE = SKILL_DIR / "SKILL.md.j2"


def load_module():
    spec = importlib.util.spec_from_file_location("decision_log", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


decision_log = load_module()


def run(*argv: str) -> str:
    args = decision_log.parse(list(argv))
    return args.run(args)


def start(directory: Path, total: int = 10, name: str = "pr-68-review") -> Path:
    printed = run(
        "start", "--total", str(total), "--name", name, "--dir", str(directory)
    )
    return Path(printed.splitlines()[0])


class TestBar:
    def test_documented_shape_renders(self):
        assert decision_log.bar(3, 10) == "▰▰▰▱▱▱▱▱▱▱  3/10"

    def test_one_cell_per_item_up_to_the_width(self):
        assert decision_log.bar(0, 4) == "▱▱▱▱  0/4"
        assert decision_log.bar(4, 4) == "▰▰▰▰  4/4"

    def test_long_queue_scales_to_the_width(self):
        rendered = decision_log.bar(25, 50)

        cells, count = rendered.split("  ")
        assert len(cells) == decision_log.BAR_WIDTH
        assert cells.count("▰") == decision_log.BAR_WIDTH // 2
        assert count == "25/50"

    def test_an_unfinished_queue_keeps_a_cell_empty(self):
        cells = decision_log.bar(49, 50).split("  ")[0]

        assert len(cells) == decision_log.BAR_WIDTH
        assert cells.count("▱") == 1

    def test_the_first_decision_fills_a_cell(self):
        cells = decision_log.bar(1, 50).split("  ")[0]

        assert cells.count("▰") == 1


class TestStart:
    def test_file_name_carries_timestamp_then_name(self, tmp_path):
        log = start(tmp_path, name="PR 68 review!")

        assert re.fullmatch(r"\d{8}-\d{6}-pr-68-review\.md", log.name)

    def test_missing_directory_is_created(self, tmp_path):
        log = start(tmp_path / "nested" / "logs")

        assert log.is_file()

    def test_fresh_log_reports_an_empty_bar(self, tmp_path):
        printed = run("start", "--total", "4", "--name", "x", "--dir", str(tmp_path))

        assert printed.splitlines()[1] == "▱▱▱▱  0/4"

    def test_nameless_name_fails_loudly(self, tmp_path):
        with pytest.raises(decision_log.LogError, match="file name"):
            run("start", "--total", "4", "--name", "!!!", "--dir", str(tmp_path))

    def test_total_below_one_fails_loudly(self, tmp_path):
        with pytest.raises(decision_log.LogError, match="items"):
            run("start", "--total", "0", "--name", "x", "--dir", str(tmp_path))

    def test_default_directory_follows_the_environment(self, tmp_path, monkeypatch):
        monkeypatch.setenv(decision_log.DIR_ENV, str(tmp_path / "chosen"))

        assert decision_log.default_dir() == tmp_path / "chosen"

    def test_default_directory_falls_back_to_the_temp_directory(self, monkeypatch):
        monkeypatch.delenv(decision_log.DIR_ENV, raising=False)

        assert decision_log.default_dir().name == decision_log.DIR_NAME


class TestRecord:
    def test_one_item_appends_one_row(self, tmp_path):
        log = start(tmp_path)

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

    def test_grouped_items_share_one_decision_and_move_the_bar_once_per_item(
        self, tmp_path
    ):
        log = start(tmp_path)

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

    def test_count_comes_from_the_file_not_the_caller(self, tmp_path):
        log = start(tmp_path)
        for index in range(3):
            run(
                "record", "--log", str(log), "--item", f"#{index}", "--decision", "Skip"
            )

        printed = run("record", "--log", str(log), "--item", "#9", "--decision", "Skip")

        assert printed.splitlines()[-1] == "▰▰▰▰▱▱▱▱▱▱  4/10"

    def test_column_break_in_a_field_is_escaped(self, tmp_path):
        log = start(tmp_path)

        run(
            "record",
            "--log",
            str(log),
            "--item",
            "#1 a | b",
            "--decision",
            "Fix\nnow",
        )

        row = log.read_text(encoding="utf-8").splitlines()[-1]
        assert row == r"| #1 a \| b | Fix now |  |"

    def test_missing_log_fails_loudly(self, tmp_path):
        with pytest.raises(decision_log.LogError, match="start"):
            run(
                "record",
                "--log",
                str(tmp_path / "absent.md"),
                "--item",
                "#1",
                "--decision",
                "Skip",
            )


class TestExtend:
    def test_new_items_raise_the_total(self, tmp_path):
        log = start(tmp_path, total=3)
        run("record", "--log", str(log), "--item", "#1", "--decision", "Fix now")

        printed = run("extend", "--log", str(log), "--by", "2")

        assert printed == "▰▱▱▱▱  1/5"
        assert "total: 5" in log.read_text(encoding="utf-8")

    def test_extending_by_nothing_fails_loudly(self, tmp_path):
        log = start(tmp_path)

        with pytest.raises(decision_log.LogError, match="no items"):
            run("extend", "--log", str(log), "--by", "0")


class TestShow:
    def test_log_prints_with_the_bar_last(self, tmp_path):
        log = start(tmp_path, total=2)
        run("record", "--log", str(log), "--item", "#1 Naming", "--decision", "Skip")

        printed = run("show", "--log", str(log))

        assert "| #1 Naming | Skip |  |" in printed
        assert printed.splitlines()[-1] == "▰▱  1/2"


def test_skill_declares_the_same_default_directory():
    """The skill's declared default and the script's fallback stay one value."""
    text = SKILL_TEMPLATE.read_text(encoding="utf-8")

    declared = re.search(r"decision-log-dir: \"(?P<dir>[^\"]+)\"", text)
    assert declared, "SKILL.md must declare metadata.config.decision-log-dir"
    assert declared.group("dir").endswith(f"/{decision_log.DIR_NAME}")
    assert "TMPDIR" in declared.group("dir")
