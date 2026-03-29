"""Find tests that import missing src.apps.<Name> modules.

Scans `tests/` for imports like `from src.apps.<Name>` or `import src.apps.<Name>`
and checks whether `src/apps/<Name>` or `src/apps/experemental/<Name>` exists.
Writes a list of test directories to ignore (one per line) to stdout.

Usage:
    python tools/find_missing_app_tests.py
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SRC_APPS = ROOT / "src" / "apps"
EXPERIMENTAL = SRC_APPS / "experemental"

IMPORT_RE = re.compile(r"from\s+src\.apps\.([A-Za-z0-9_]+)|import\s+src\.apps\.([A-Za-z0-9_]+)")


def find_imported_apps():
    apps = set()
    for p in TESTS.rglob("*.py"):
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        for m in IMPORT_RE.finditer(text):
            name = m.group(1) or m.group(2)
            if name:
                apps.add(name)
    return apps


def app_exists(name: str) -> bool:
    # Check src/apps/<Name> or src/apps/experemental/<Name>
    if (SRC_APPS / name).exists():
        return True
    if (EXPERIMENTAL / name).exists():
        return True
    return False


def tests_dir_for(name: str) -> Path | None:
    p = TESTS / "apps" / name
    if p.exists():
        return p
    # fallback: maybe tests are under tests/** referencing that name; try to find any file containing the import
    for f in TESTS.rglob("*.py"):
        try:
            text = f.read_text(encoding='utf-8')
        except Exception:
            continue
        if f"src.apps.{name}" in text:
            return f.parent
    return None


def main():
    apps = find_imported_apps()
    missing = []
    for name in sorted(apps):
        if not app_exists(name):
            td = tests_dir_for(name)
            if td is not None:
                missing.append(str(td.relative_to(ROOT)).replace('\\', '/'))
            else:
                # no tests dir found; still report the name
                missing.append(f"(no tests dir) {name}")
    if not missing:
        print("# No missing app modules referenced by tests detected")
        return 0
    # print directories to ignore
    for m in missing:
        print(m)
    return 0


if __name__ == '__main__':
    sys.exit(main())

