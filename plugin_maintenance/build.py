"""Full build: run stage-1 generators, then render every harness dist tree.

Usage: `uv run python -m plugin_maintenance.build`
"""

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.generate import run_generators
from plugin_maintenance.render import DIST_DIRS, BuildError, render_tree


def build() -> None:
    run_generators()
    for harness, dist_dir in DIST_DIRS.items():
        render_tree(REPO_ROOT, harness, REPO_ROOT / dist_dir)


def main() -> None:
    try:
        build()
    except BuildError as error:
        raise SystemExit(f"error: {error}") from error
    for harness, dist_dir in DIST_DIRS.items():
        print(f"rendered {harness} -> {dist_dir}")


if __name__ == "__main__":
    main()
