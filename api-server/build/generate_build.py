"""Build and verify the three standalone reporting-dashboard workers.

Run from any working directory. Build artifacts are deliberately not committed or
pushed by this script; a failed dependency or frozen-import check stops the build.
"""
from __future__ import annotations

import argparse
import ast
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "api-server"
BUILD_DIR = ROOT / "exe_build"
DIST_DIR = ROOT / "exe_dist"
ENTRYPOINTS = ("serve", "cache_gen", "csvLoader")
ENVIRONMENTS = ("qa", "prod", "dev")
# These modules are imported dynamically in some execution paths (notably
# Excel, character decoding and legacy/new encryption). Do not rely only on
# PyInstaller's analysis of the default startup path.
DYNAMIC_IMPORTS = (
    "openpyxl", "openpyxl.reader.excel", "openpyxl.writer.excel",
    "chardet", "charset_normalizer", "Crypto.Cipher.AES",
    "cryptography.hazmat.primitives.ciphers.aead",
    "jwt", "ldap3", "lxml.etree", "pandas", "pyodbc",
    "requests", "dateutil.parser", "dotenv", "flask",
    "flask_cors", "waitress",
)
PLATFORM_IMPORTS = {"msvcrt", "winreg", "fcntl", "pwd", "grp", "termios", "resource"}
SMOKE_MARKER = "BUILD-SMOKE-OK"


def run(*args, **kwargs):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run([str(arg) for arg in args], check=True, cwd=ROOT, **kwargs)


def runtime_sources():
    """Everything shipped in the backend, excluding build tooling and tests."""
    return sorted(
        path for path in API_DIR.rglob("*.py")
        if "build" not in path.relative_to(API_DIR).parts
        and "__pycache__" not in path.parts
    )


def bundled_modules():
    return [
        ".".join(path.relative_to(API_DIR).with_suffix("").parts)
        for path in runtime_sources()
        if path.name != "__init__.py"
    ]


def verify_python_sources():
    """Catch syntax failures and missing non-platform imports before freezing."""
    sources = runtime_sources()
    modules = set(bundled_modules())
    local_roots = {name.split(".", 1)[0] for name in modules}
    required_roots = set()
    errors = []
    for path in sources:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                required_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                required_roots.add(node.module.split(".", 1)[0])
    required_roots.update(name.split(".", 1)[0] for name in DYNAMIC_IMPORTS)
    for name in sorted(required_roots - local_roots - PLATFORM_IMPORTS):
        if name in sys.stdlib_module_names or name in sys.builtin_module_names:
            continue
        if importlib.util.find_spec(name) is None:
            errors.append(f"Unresolved import: {name} (add its distribution to requirements.txt)")
    if errors:
        raise RuntimeError("Python preflight failed:\n" + "\n".join(errors))
    print(f"Validated {len(sources)} backend Python files and {len(required_roots)} import roots.", flush=True)
    return sorted(required_roots - local_roots - PLATFORM_IMPORTS)


def verify_requirements():
    """Ensure every declared distribution AND its pinned version is installed."""
    from packaging.requirements import Requirement

    missing = []
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8-sig").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        req = Requirement(raw)
        if req.marker and not req.marker.evaluate():
            continue
        try:
            version = importlib.metadata.version(req.name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(f"{req.name} is not installed")
            continue
        if req.specifier and not req.specifier.contains(version, prereleases=True):
            missing.append(f"{req.name}: found {version}, expected {req.specifier}")
    if missing:
        raise RuntimeError("Incorrect or missing requirements:\n" + "\n".join(missing))
    run(sys.executable, "-m", "pip", "check")
    import PyInstaller  # noqa: F401 - validates the same interpreter used to freeze
    print("All pinned runtime requirements and PyInstaller are installed.", flush=True)


def preflight(install=True):
    if install:
        run(sys.executable, "-m", "pip", "install", "-r", ROOT / "requirements.txt")
        run(sys.executable, "-m", "pip", "install", "pyinstaller>=6.10,<7")
    verify_requirements()
    verify_python_sources()


def pyinstaller_command(entrypoint, imports):
    if entrypoint not in ENTRYPOINTS:
        raise ValueError(f"Unknown entrypoint: {entrypoint}")
    suffix = ".exe" if os.name == "nt" else ""
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--console",
        "--name", entrypoint,
        "--paths", str(API_DIR),
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / entrypoint),
        "--specpath", str(BUILD_DIR / "spec"),
        "--runtime-hook", str(API_DIR / "build" / "frozen_smoke_hook.py"),
        # PyInstaller's builtin pandas/numpy/pyodbc/lxml hooks remain in use.
        # Explicit collection covers runtime plugins and lazy imports.
        "--collect-all", "openpyxl",
        "--collect-all", "chardet",
        "--collect-all", "charset_normalizer",
        "--collect-submodules", "Crypto",
        "--collect-submodules", "ldap3",
    ]
    for module in sorted(set(bundled_modules()) | set(DYNAMIC_IMPORTS) | set(imports)):
        command.extend(("--hidden-import", module))
    command.append(str(API_DIR / (entrypoint + ".py")))
    return command, DIST_DIR / (entrypoint + suffix)


def frozen_smoke(executable):
    result = run(executable, "--build-smoke", capture_output=True, text=True, timeout=120)
    if SMOKE_MARKER not in result.stdout:
        raise RuntimeError(f"Frozen smoke did not complete: {executable}\n{result.stdout}\n{result.stderr}")
    print(f"PASS frozen imports: {executable.name}", flush=True)


def build(only=None):
    imports = verify_python_sources()
    selected = (only,) if only else ENTRYPOINTS
    built = {}
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    for name in selected:
        command, exe = pyinstaller_command(name, imports)
        # A stale output must never be accepted as proof of a successful build.
        if exe.exists():
            exe.unlink()
        run(*command)
        if not exe.is_file() or exe.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty generated binary: {exe}")
        frozen_smoke(exe)
        copies = []
        for environment in ENVIRONMENTS:
            target = DIST_DIR / f"{environment}_{exe.name}"
            shutil.copy2(exe, target)
            copies.append(str(target.relative_to(ROOT)))
        built[name] = copies
    report = {"status": "passed", "platform": sys.platform, "executables": built}
    (DIST_DIR / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Install/check dependencies and imports; do not freeze")
    parser.add_argument("--skip-install", action="store_true", help="Verify the existing interpreter instead of pip installing")
    parser.add_argument("--only", choices=ENTRYPOINTS, help="Build one worker instead of all three")
    args = parser.parse_args(argv)
    try:
        preflight(install=not args.skip_install)
        if not args.check_only:
            build(only=args.only)
        return 0
    except (RuntimeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
