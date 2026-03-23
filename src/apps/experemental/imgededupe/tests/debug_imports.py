import sys
import os

# Get project root (d:\github\BCor)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
print(f"Project root: {project_root}")

sys.path.insert(0, project_root)

try:
    from src.core.system import System
    print("Sucessfully imported System")
except Exception as e:
    print(f"Failed to import System: {e}")

try:
    from src.apps.experemental.imgededupe.module import ImgeDeduplicationModule
    print("Sucessfully imported ImgeDeduplicationModule")
except Exception as e:
    import traceback
    print(f"Failed to import ImgeDeduplicationModule: {e}")
    traceback.print_exc()
