"""Full build: run stage-1 generators, then render every harness dist tree.

Usage: `uv run python -m plugin_maintenance.build [--check]`
"""

import sys
import tempfile
from pathlib import Path

from plugin_maintenance import REPO_ROOT
from plugin_maintenance.generate import run_generators
from plugin_maintenance.render import (
    DIST_DIRS,
    BuildError,
    render_tree,
    tree_snapshot,
)


def build() -> None:
    run_generators()
    for harness, dist_dir in DIST_DIRS.items():
        render_tree(REPO_ROOT, harness, REPO_ROOT / dist_dir)


def stale_paths() -> list[str]:
    """Committed `dist/` paths a fresh render of `plugins/` disagrees with.

    Stage 2 only, and it writes nothing. CI still runs the full build and
    diffs the whole tree, which is what covers stage-1 output.
    """
    stale = []
    with tempfile.TemporaryDirectory(prefix="dist-check-") as temporary:
        for harness, dist_dir in DIST_DIRS.items():
            fresh = Path(temporary) / harness
            render_tree(REPO_ROOT, harness, fresh)
            committed = tree_snapshot(REPO_ROOT / dist_dir)
            rendered = tree_snapshot(fresh)
            stale += [f"{dist_dir}/{name}" for name in committed.keys() ^ rendered.keys()]
            stale += [
                f"{dist_dir}/{name}"
                for name in committed.keys() & rendered.keys()
                if committed[name] != rendered[name]
            ]
    return sorted(stale)


def main() -> None:
    try:
        if "--check" in sys.argv[1:]:
            stale = stale_paths()
            if stale:
                raise SystemExit(
                    "dist is stale:\n  "
                    + "\n  ".join(stale)
                    + "\n\nrun `uv run python -m plugin_maintenance.build`"
                )
            print("dist matches plugins/")
            return
        build()
    except BuildError as error:
        raise SystemExit(f"error: {error}") from error
    for harness, dist_dir in DIST_DIRS.items():
        print(f"rendered {harness} -> {dist_dir}")


if __name__ == "__main__":
    main()
