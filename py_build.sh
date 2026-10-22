#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  if [ -x .venv/bin/python ]; then PYTHON=.venv/bin/python
  elif command -v python3 >/dev/null 2>&1; then PYTHON=python3
  else PYTHON=python
  fi
fi
echo "Running dependency, regression and visual pre-build checks..."
"$PYTHON" scripts/build_all.py "$@"
echo "Build completed. Platform-native binaries are in exe_dist/."
