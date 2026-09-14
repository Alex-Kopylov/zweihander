#!/usr/bin/env bash
set -euo pipefail
workspace=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
exec uv run --script "$workspace/application_records.py"
