@echo off

REM Run Python build script
python ./api-server/build/generate_build.py

REM Run npm build
npm run build

REM Commit generated build files
git add .
git commit -m "Generated build files after successful npm and Python build"

REM Push to remote
git push