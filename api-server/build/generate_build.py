import importlib.metadata as metadata
import os
import shutil
import subprocess
import sys
from pathlib import Path

requirements_path = Path("requirements.txt")
if requirements_path.exists():
    raw_bytes = requirements_path.read_bytes()
    encoding = "utf-16-le" if raw_bytes.startswith(b"\xff\xfe") else "utf-16-be" if raw_bytes.startswith(b"\xfe\xff") else "utf-8"
    with requirements_path.open("r", encoding=encoding) as f:
        required = {line.strip().split('==')[0] for line in f if line.strip() and not line.startswith('#')}
else:
    required = set()

installed = {dist.metadata['Name'] if 'Name' in dist.metadata else dist.name for dist in metadata.distributions()}
packages = sorted(required & installed)

exe_dist = Path("exe_dist")
exe_build = Path("exe_build")
exe_dist.mkdir(exist_ok=True)
exe_build.mkdir(exist_ok=True)

pyi_cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--clean",
    "--onefile",
    "--console",
    "--distpath",
    str(exe_dist.resolve()),
    "--workpath",
    str(exe_build.resolve()),
    "--hidden-import",
    "chardet.pipeline.orchestrator__mypyc",
    "--collect-all",
    "chardet",
    "--collect-all",
    "charset_normalizer",
]

# Define environments
environments = ["qa", "prod", "dev"]
ALL_FILES = ["serve", "cache_gen", "csvLoader"]

# Function to build the executable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shutil
import subprocess
 
 
def build_single_executable(py_file):
    source = Path("api-server") / f"{py_file}.py"
    cmd = pyi_cmd + ["--name", py_file, str(source)]
 
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed for {py_file} with exit code {e.returncode}")
        return False
    except FileNotFoundError as e:
        print(f"Error: {e}. Ensure PyInstaller is installed in the virtualenv.")
        return False
 
    built_exe = exe_dist / f"{py_file}.exe"
    if not built_exe.exists():
        print(f"Error: Executable {built_exe} not found after build.")
        return False
 
    for env in environments:
        env_exe = exe_dist / f"{env}_{py_file}.exe"
        shutil.copy2(built_exe, env_exe)
 
    built_exe.unlink()
 
    return True
 
 
def build_executable():
    build_succeeded = True
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(build_single_executable, py_file): py_file
            for py_file in ALL_FILES
        }
 
        for future in as_completed(futures):
            py_file = futures[future]
            try:
                if not future.result():
                    print(f"Build failed for {py_file}")
                    build_succeeded = False
            except Exception as e:
                print(f"Unexpected error building {py_file}: {e}")
                build_succeeded = False
    return build_succeeded


def cleanup_spec_files():
    dist_dir = Path("dist")
    if dist_dir.exists():
        for spec_file in dist_dir.glob("*.spec"):
            try:
                spec_file.unlink()
            except OSError:
                pass


# Main function to run tasks sequentially
def main():
    if not build_executable():
        return 1
    cleanup_spec_files()
    return 0


if __name__ == "__main__":
    sys.exit(main())
