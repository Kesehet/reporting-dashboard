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

echo "Installing production and chart-contract dependencies"
"$PYTHON_EXEC" -m pip install -r requirements.txt -r tests/contracts/requirements.txt
"$PYTHON_EXEC" -m pip install pyinstaller
npm ci --no-audit --no-fund

build_failed=0
test_failed=0
echo "Building frontend production assets first"
CI=false npm run build || build_failed=1
echo "Packaging standalone Python executables"
"$PYTHON_EXEC" api-server/build/generate_build.py || build_failed=1
mkdir -p dist
if compgen -G "exe_dist/*" > /dev/null; then
  find exe_dist -maxdepth 1 -type f -exec cp {} dist/ \; || build_failed=1
else
  echo "WARNING: no Python executable artifact produced"
  build_failed=1
fi
echo "Builds are retained even when subsequent tests fail."

echo "Generating real backend chart contracts before testing"
"$PYTHON_EXEC" scripts/run_chart_contracts.py || test_failed=1
echo "Running all backend regressions"
"$PYTHON_EXEC" -m unittest discover -s tests -p 'test_*.py' -v || test_failed=1
"$PYTHON_EXEC" -m unittest discover -s tests/contracts -p 'test_*.py' -v || test_failed=1
echo "Running complete frontend regression suite (no skipped chart contracts)"
CI=true CHART_CONTRACTS_REQUIRED=1 npm run test:nocov -- --runInBand || test_failed=1

if (( build_failed )); then echo "ERROR: build failed (successful artifacts retained)." >&2; fi
if (( test_failed )); then echo "ERROR: regression tests failed (build artifacts retained)." >&2; fi
if (( build_failed || test_failed )); then exit 1; fi
echo "All builds and tests passed. Artifacts: build/ and dist/"
