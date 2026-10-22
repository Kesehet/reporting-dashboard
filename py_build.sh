#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
LOG_FILE="${BUILD_LOG_FILE:-build_log.txt}"
exec > >(tee "$LOG_FILE") 2>&1
trap 'echo "Build failed at line $LINENO; see $LOG_FILE" >&2' ERR
PYTHON_EXEC=python3
if [[ -x .venv/bin/python ]]; then PYTHON_EXEC=.venv/bin/python
elif [[ -x .venv/Scripts/python.exe ]]; then PYTHON_EXEC=.venv/Scripts/python.exe
elif ! command -v python3 >/dev/null 2>&1; then PYTHON_EXEC=python; fi

echo "Installing declared Python dependencies"
"$PYTHON_EXEC" -m pip install -r requirements.txt
"$PYTHON_EXEC" -m pip install pyinstaller
echo "Preflight: dependency health and Python syntax"
"$PYTHON_EXEC" api-server/build/generate_build.py --check
echo "Preflight: backend regressions"
"$PYTHON_EXEC" -m unittest discover -s tests -p 'test_*.py'
echo "Preflight: frontend regressions"
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
npm ci --no-audit --no-fund
CI=true npm run test:nocov -- --runInBand
CI=true npm run build
echo "Packaging backend"
"$PYTHON_EXEC" api-server/build/generate_build.py
mkdir -p dist
find exe_dist -maxdepth 1 -type f -exec cp {} dist/ \;
echo "Build complete: dist/ (no source or database files were removed)"
