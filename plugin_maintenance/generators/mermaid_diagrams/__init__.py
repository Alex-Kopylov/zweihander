"""Stage-1 generator for the mermaid-diagrams plugin.

`generate()` rebuilds the generated docs from the bundled references, offline.
The upstream fetch lives in `sync.py`, invoked by the weekly workflow outside
the build.
"""

PLUGIN_NAME = "mermaid-diagrams"


def generate() -> None:
    from plugin_maintenance.generators.mermaid_diagrams.generated_docs import (
        update_generated_docs,
    )

    update_generated_docs()
