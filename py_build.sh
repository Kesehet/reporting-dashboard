#!/usr/bin/env bash
set -e

LOG_FILE=build_log.txt

echo "Starting to build dashboard FE and BE"
echo "Temporarily building frontend and backend together. Please wait..." > "$LOG_FILE"

echo "Building frontend..." >> "$LOG_FILE" 2>&1
npm run build >> "$LOG_FILE" 2>&1 &
FRONTEND_PID=$!

echo "Checking Python virtualenv and PyInstaller..." >> "$LOG_FILE" 2>&1
PYTHON_EXEC=""
if [ -x "./.venv/Scripts/python.exe" ]; then
  PYTHON_EXEC="./.venv/Scripts/python.exe"
elif [ -x "./.venv/bin/python" ]; then
  PYTHON_EXEC="./.venv/bin/python"
elif [ -x "./.venv/bin/python3" ]; then
  PYTHON_EXEC="./.venv/bin/python3"
else
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_EXEC="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_EXEC="python"
  else
    echo "ERROR: Python interpreter not found. Activate or create the virtualenv first." >> "$LOG_FILE" 2>&1
    exit 1
  fi
fi

echo "Using Python interpreter: $PYTHON_EXEC" >> "$LOG_FILE" 2>&1

echo "Installing PyInstaller if missing..." >> "$LOG_FILE" 2>&1
$PYTHON_EXEC -m pip install --quiet pyinstaller >> "$LOG_FILE" 2>&1

echo "Generating the build files" >> "$LOG_FILE"
$PYTHON_EXEC ./api-server/build/generate_build.py >> "$LOG_FILE" 2>&1

echo "Waiting for frontend build..." >> "$LOG_FILE" 2>&1
wait "$FRONTEND_PID"


echo "Moving all exe to dist folder..." >> "$LOG_FILE" 2>&1
mkdir -p dist
mv ./exe_dist/*.exe ./dist >> "$LOG_FILE" 2>&1

echo "Cleaning up build artifacts..." >> "$LOG_FILE" 2>&1
rm -rf ./exe_build >> "$LOG_FILE" 2>&1
rm -rf ./exe_dist >> "$LOG_FILE" 2>&1
find . -name "*.spec" -type f -delete >> "$LOG_FILE" 2>&1
find . -name "*.pyc" -type f -delete >> "$LOG_FILE" 2>&1
find . -name "*.db" -type f -delete >> "$LOG_FILE" 2>&1
find . -name "__pycache__" -type d -exec rm -rf {} + >> "$LOG_FILE" 2>&1
rm -rf ./.cache_requests/* >> "$LOG_FILE" 2>&1

# Remove all blank directory from all directories
find . -type d -empty -delete >> "$LOG_FILE" 2>&1

echo "Build completed successfully." >> "$LOG_FILE" 2>&1
