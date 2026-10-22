"""Build and validate the dashboard's standalone Python entry points.

Run from any working directory. Package installation is owned by py_build scripts
and CI; this command refuses to package an incomplete environment.
"""
import argparse
import ast
import importlib.metadata
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "api-server"
ENTRIES = ("serve", "cache_gen", "csvLoader")
ENVIRONMENTS = ("qa", "prod", "dev")
# Packages with runtime imports/plugins/resources that static PyInstaller analysis
# may not detect reliably. Keep this list small and expand on measured failures.
DYNAMIC_PACKAGES = (
    "Crypto", "cryptography", "flask", "flask_cors", "flask_login",
    "jwt", "ldap3", "mysql", "pandas", "openpyxl", "charset_normalizer",
    "chardet", "pkg_resources", "jaraco",
)


def requirements():
    path = ROOT / "requirements.txt"
    if not path.is_file():
        raise RuntimeError(f"Missing dependency manifest: {path}")
    from packaging.requirements import Requirement
    required = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            required.append(Requirement(line))
    return required


def validate_dependencies():
    from packaging.utils import canonicalize_name
    installed = {canonicalize_name(d.metadata["Name"]): d.version
                 for d in importlib.metadata.distributions() if d.metadata.get("Name")}
    missing = []
    invalid = []
    for req in requirements():
        if req.marker and not req.marker.evaluate():
            continue
        key = canonicalize_name(req.name)
        if key not in installed:
            missing.append(req.name)
        elif req.specifier and not req.specifier.contains(installed[key], prereleases=True):
            invalid.append(f"{req.name}: installed {installed[key]}, required {req.specifier}")
    if missing or invalid:
        raise RuntimeError("Dependency check failed. Missing: "
                           + (", ".join(missing) or "none")
                           + "; version conflicts: " + ("; ".join(invalid) or "none")
                           + ". Install with: python -m pip install -r requirements.txt")
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    print(f"Dependency validation passed ({len(installed)} installed distributions).", flush=True)


def validate_sources():
    for entry in ENTRIES:
        if not (API / f"{entry}.py").is_file():
            raise RuntimeError(f"Missing application entry point: {entry}.py")
    sources = list(API.rglob("*.py"))
    for file in sources:
        try:
            ast.parse(file.read_text(encoding="utf-8-sig"), filename=str(file))
        except (SyntaxError, UnicodeError) as exc:
            raise RuntimeError(f"Invalid Python source: {file}: {exc}") from exc
    print(f"Parsed {len(sources)} Python source files.", flush=True)


def pyinstaller_command(entry, dest, work, specs):
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--onefile", "--console", "--name", entry,
        "--distpath", str(dest), "--workpath", str(work),
        "--specpath", str(specs),
    ]
    for package in DYNAMIC_PACKAGES:
        if importlib.util.find_spec(package) is not None:
            command.extend(["--collect-all", package])
    command.append(str(API / f"{entry}.py"))
    return command


def build():
    validate_dependencies()
    validate_sources()
    import PyInstaller  # noqa: F401 - a missing packager must be fatal
    dest, work, specs = (ROOT / name for name in ("exe_dist", "exe_build", "exe_specs"))
    dest.mkdir(exist_ok=True)
    work.mkdir(exist_ok=True)
    specs.mkdir(exist_ok=True)
    suffix = ".exe" if os.name == "nt" else ""
    for entry in ENTRIES:
        print(f"Packaging {entry}...", flush=True)
        subprocess.run(pyinstaller_command(entry, dest, work, specs), cwd=ROOT, check=True)
        binary = dest / (entry + suffix)
        if not binary.is_file() or binary.stat().st_size == 0:
            raise RuntimeError(f"PyInstaller did not produce {binary}")
        for env in ENVIRONMENTS:
            shutil.copy2(binary, dest / f"{env}_{entry}{suffix}")
        binary.unlink()
    print(f"Validated and packaged {len(ENTRIES)} entry points.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without building")
    args = parser.parse_args()
    try:
        if args.check:
            validate_dependencies()
            validate_sources()
        else:
            build()
    except (RuntimeError, subprocess.CalledProcessError, ModuleNotFoundError) as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
