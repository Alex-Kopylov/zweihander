"""Full build: run stage-1 generators, then render every harness dist tree.

Usage: `uv run python -m plugin_maintenance.build`
"""

from pathlib import Path

from plugin_maintenance.generate import run_generators
from plugin_maintenance.render import DIST_DIRS, BuildError, render_tree


def build(repo_root: Path | None = None) -> None:
    repo_root = Path(repo_root) if repo_root else Path.cwd()
    run_generators()
    for harness, dist_dir in DIST_DIRS.items():
        render_tree(repo_root, harness, repo_root / dist_dir)


def main() -> None:
    try:
        build()
    except BuildError as error:
        raise SystemExit(f"error: {error}") from error
    for harness, dist_dir in DIST_DIRS.items():
        print(f"rendered {harness} -> {dist_dir}")


if __name__ == "__main__":
    main()
