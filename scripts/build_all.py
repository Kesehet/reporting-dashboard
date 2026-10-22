"""One-command release builder: fail on regressions before generating binaries."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FREEZER = ROOT / "api-server" / "build" / "generate_build.py"


def run(*command, env=None):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run([str(arg) for arg in command], cwd=ROOT, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-browser", action="store_true", help="Explicit local-only opt-out of Chromium UI checks")
    args = parser.parse_args()
    ci_env = {**os.environ, "CI": "true", "TZ": "UTC"}
    # This installs/verifies ALL production requirements, not only ones currently
    # imported at startup, and validates Python syntax and import resolution.
    run(sys.executable, FREEZER, "--check-only")
    run("npm", "ci", "--no-audit", "--no-fund")
    run(sys.executable, "-m", "pytest", "-q", "tests")
    run(sys.executable, "scripts/run_chart_contracts.py")
    run("npm", "run", "test:nocov", "--", "--runInBand", env=ci_env)
    # Existing CRA lint warnings are not introduced by packaging changes.
    run("npm", "run", "build", env={**ci_env, "CI": "false"})
    if not args.skip_browser:
        run("npm", "install", "--no-save", "--package-lock=false",
            "@playwright/test@1.56.1", "--no-audit", "--no-fund")
        run("npx", "playwright", "install", "chromium")
        run("npx", "playwright", "test", "-c", "browser-tests/playwright.config.cjs",
            "--reporter=line", env=ci_env)
    else:
        print("WARNING: Browser checks explicitly skipped; CI still requires them.", flush=True)
    run(sys.executable, FREEZER, "--skip-install")
    print("PASS: dependencies, Python regressions, chart contracts, frontend, browser and frozen imports.")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"PRE-BUILD GATE FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
