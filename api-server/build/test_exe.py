import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
 
 
# List of exe files to test
exe_files = [
    'qa_serve.exe',
    'prod_serve.exe',
    'dev_serve.exe',
    'qa_cache_gen.exe',
    'prod_cache_gen.exe',
    'dev_cache_gen.exe',
    'qa_csvLoader.exe',
    'prod_csvLoader.exe',
    'dev_csvLoader.exe'
]
 
 
def test_exe(exe_path, timeout=30, expect_timeout=True):
    """Test if exe runs without immediate errors."""
    try:
        proc = subprocess.Popen(
            [exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
 
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            return_code = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            if expect_timeout:
                return True, "Timeout expected"
            return False, "Timeout"
 
        if return_code != 0:
            return False, f"Exit code {return_code}, stderr: {stderr}"
 
        if (
            'ImportError' in stderr
            or 'ModuleNotFoundError' in stderr
            or 'error' in stderr.lower()
        ):
            return False, f"Import or other error in stderr: {stderr}"
 
        return True, "OK"
 
    except FileNotFoundError:
        return False, "Exe not found"
    except Exception as e:
        return False, str(e)
 
 
def run_test(dist_dir, exe):
    exe_path = os.path.join(dist_dir, exe)
    success, message = test_exe(
        exe_path,
        expect_timeout=True
    )
    return exe, success, message
 
 
def main():
    dist_dir = 'exe_dist'
 
    if not os.path.exists(dist_dir):
        print(f"Dist directory {dist_dir} not found. Run build first.")
        return
 
    results = []
 
    with ThreadPoolExecutor(max_workers=min(8, len(exe_files))) as executor:
        futures = {
            executor.submit(run_test, dist_dir, exe): exe
            for exe in exe_files
        }
 
        for future in as_completed(futures):
            exe, success, message = future.result()
 
            print(
                f"{exe}: "
                f"{'PASS' if success else 'FAIL'} - {message}"
            )
 
            results.append((exe, success, message))
 
    print("\nSummary:")
    for exe, success, message in sorted(results):
        status = "PASS" if success else "FAIL"
        print(f"{exe}: {status} - {message}")
 
    all_pass = all(success for _, success, _ in results)
 
    if all_pass:
        print("All exe tests passed!")
    else:
        print("Some exe tests failed.")
        exit(1)
 
 
if __name__ == "__main__":
    main()