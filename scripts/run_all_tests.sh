#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Building InvariantQ Core ==="
"$REPO_ROOT/scripts/build_core.sh"

echo "=== Running InvariantQ Pytest Suite ==="
cd "$REPO_ROOT"
pytest tests/ -v

echo "=== Running CLI Sanity Checks ==="
invariantq --help > /dev/null
invariantq verify --metamorphic --fault-injection

echo "=== All Tests Passed Successfully! ==="
