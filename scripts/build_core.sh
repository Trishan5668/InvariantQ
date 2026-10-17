#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Building InvariantQ Core C++ Shared Library ==="
cd "$REPO_ROOT/core"
make clean
make -j$(nproc 2>/dev/null || echo 2)

cp libinvariantq.so "$REPO_ROOT/invariantq/core/"
echo "Successfully built and installed libinvariantq.so to invariantq/core/"
