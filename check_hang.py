import subprocess
import os
from pathlib import Path

# Use absolute path for python and test directory
python_exe = r"d:/github/BCor/.venv/Scripts/python.exe"
test_dir = Path(r"d:/github/BCor/tests")
all_test_files = sorted(list(test_dir.rglob("test_*.py")))

for test_file in all_test_files:
    print(f"Running {test_file.relative_to(test_dir.parent)}...")
    try:
        # 10 second timeout per file
        result = subprocess.run(
            [python_exe, "-m", "pytest", str(test_file), "-q", "--tb=no"],
            capture_output=True,
            timeout=15,
            text=True,
            cwd=r"d:/github/BCor"
        )
        if result.returncode == 0:
            print(f"  PASSED")
        else:
            print(f"  FAILED")
            # print(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"  HANGED!!!")
    except Exception as e:
        print(f"  Error: {e}")
