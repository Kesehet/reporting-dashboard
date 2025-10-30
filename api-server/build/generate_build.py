import os
import json
import subprocess
import pkg_resources

installed = {dist.key for dist in pkg_resources.working_set}

with open("./requirements.txt", "r") as f:
    required = {line.strip().split('==')[0] for line in f if line.strip() and not line.startswith('#')}

packages = sorted(required & installed)

pyi_cmd = [
    "pyinstaller",
    "--clean",
    # "--debug=all",
    "--onefile",
    "--console"
]
# for pkg in packages:
#     pyi_cmd += [f"--collect-all", pkg, f"--hidden-import", pkg, "--copy-metadata", pkg]

# Define environments
environments = ["qa", "prod", "dev"]

# Function to generate .env file
def generate_env(environment, config_file, output_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    env_config = config.get(environment, {})
    with open(output_file, 'w') as f:
        for key, value in env_config.items():
            f.write(f"{key}={value}\n")
            print(f"{key}={value}\n")

# Function to build the executable
def build_executable(env):
    generate_env(env, "./api-server/build/build_config.json", ".env")
    files = ["serve", "cache_gen", "csvLoader"]
    for py_file in files:
        cmd = pyi_cmd + ["--name", f"{env}_{py_file}", f"./api-server/{py_file}.py", f"./api-server/{py_file}.py"]
        print("Command is", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError as e:
            print(f"Error: {e}. Ensure 'pyinstaller' is installed and in your PATH.")
            return
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller failed with exit code {e.returncode}")
            return
        try:
            os.remove(f"{env}_{py_file}.spec")
        except FileNotFoundError:
            pass

# Main function to run tasks sequentially
def main():
    import shutil
    import os

    # Define file paths
    original_file = '.env'
    backup_file = '.env.backup'

    # Step 1: Copy original file to backup file
    shutil.copyfile(original_file, backup_file)
    print(f"Copied {original_file} to {backup_file}")

    # Step 2: Run the loop to generate exe
    for env in environments:
        build_executable(env)

    # Step 3: Copy backup file back to original file
    shutil.copyfile(backup_file, original_file)
    print(f"Copied {backup_file} back to {original_file}")

    # Step 4: Delete the backup file
    if os.path.exists(backup_file):
        os.remove(backup_file)
        print(f"Deleted {backup_file}")
    else:
        print(f"{backup_file} does not exist")

    

if __name__ == "__main__":
    main()
