"""Stage-1 generator packages, one per generated plugin.

Each generator is a package named for its plugin (underscores instead of
hyphens) exposing a zero-argument `generate()` that is offline, idempotent,
and deterministic. Fetching external content happens outside the build.
"""
