from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_every_agents_file_has_claude_import() -> None:
    agents_files = sorted(
        path
        for path in REPO_ROOT.rglob("AGENTS.md")
        if ".git" not in path.parts
    )

    assert agents_files, "expected at least one AGENTS.md file"

    missing_or_invalid = []
    for agents_file in agents_files:
        claude_file = agents_file.with_name("CLAUDE.md")
        if not claude_file.exists():
            missing_or_invalid.append(f"{claude_file.relative_to(REPO_ROOT)} missing")
            continue

        import_lines = [
            line.strip()
            for line in claude_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if "@AGENTS.md" not in import_lines:
            missing_or_invalid.append(
                f"{claude_file.relative_to(REPO_ROOT)} missing @AGENTS.md import"
            )

    assert not missing_or_invalid, "\n".join(missing_or_invalid)
