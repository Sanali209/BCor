"""Generate a monorepo inventory for BCor.

Output: Ddocks/Design_docks/specs/monorepo-inventory.md

Collects: top-level packages under src/, apps, modules, adapters, common, core.
For each entry records: path, type, README present, QUARANTINE.md present, tests presence, suggested owner.

Run from repository root:
    python tools/generate_inventory.py
Or with uv:
    uv run python tools/generate_inventory.py
"""
from __future__ import annotations
import os
from pathlib import Path
import datetime
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT_DIR = ROOT / "Ddocks" / "Design_docks" / "specs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "monorepo-inventory.md"


def list_top_level_dirs(src: Path):
    if not src.exists():
        return []
    return [p for p in src.iterdir() if p.is_dir()]


def has_tests_for(name: str, tests_root: Path) -> bool:
    # Quick heuristic: search for occurrences of the module name in tests files
    if not tests_root.exists():
        return False
    pattern = re.compile(re.escape(name), re.IGNORECASE)
    for p in tests_root.rglob("*.py"):
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if pattern.search(text):
            return True
    return False


def detect_type(path: Path) -> str:
    # simple rules
    parts = path.parts
    if "modules" in parts:
        return "module"
    if "apps" in parts:
        return "app"
    if path.name == "adapters":
        return "adapter"
    if path.name == "common":
        return "common"
    if path.name == "core":
        return "core"
    return "package"


def suggest_owner(path: Path, kind: str) -> str:
    base = str(path).replace('\\', '/').lstrip('./')
    return f"module-owner:{base}"


def gather_entries():
    entries = []
    tests_root = ROOT / "tests"
    # common top-level under src
    top_dirs = list_top_level_dirs(SRC)
    for d in top_dirs:
        # skip __pycache__
        if d.name.startswith("__"):
            continue
        # collect items: for apps and modules, enumerate children
        if d.name in ("apps", "modules"):
            for child in sorted(d.iterdir()):
                if not child.is_dir():
                    continue
                readme = (child / "README.md").exists()
                quarantine = (child / "QUARANTINE.md").exists() or (child / "QUARANTINE").exists()
                tests = has_tests_for(child.name, tests_root)
                kind = detect_type(child)
                owner = suggest_owner(child, kind)
                entries.append({
                    "name": child.name,
                    "path": str(child.relative_to(ROOT)).replace('\\', '/'),
                    "type": kind,
                    "readme": readme,
                    "quarantine": quarantine,
                    "tests": tests,
                    "owner": owner,
                })
        else:
            # top-level single package
            readme = (d / "README.md").exists()
            quarantine = (d / "QUARANTINE.md").exists()
            tests = has_tests_for(d.name, tests_root)
            kind = detect_type(d)
            owner = suggest_owner(d, kind)
            entries.append({
                "name": d.name,
                "path": str(d.relative_to(ROOT)).replace('\\', '/'),
                "type": kind,
                "readme": readme,
                "quarantine": quarantine,
                "tests": tests,
                "owner": owner,
            })
    # also check some well-known folders
    extras = [ROOT / "src" / "adapters", ROOT / "src" / "common", ROOT / "src" / "core"]
    for e in extras:
        if e.exists() and all(not (en['path'] == str(e.relative_to(ROOT)).replace('\\','/')) for en in entries):
            readme = (e / "README.md").exists()
            quarantine = (e / "QUARANTINE.md").exists()
            tests = has_tests_for(e.name, tests_root)
            kind = detect_type(e)
            owner = suggest_owner(e, kind)
            entries.append({
                "name": e.name,
                "path": str(e.relative_to(ROOT)).replace('\\', '/'),
                "type": kind,
                "readme": readme,
                "quarantine": quarantine,
                "tests": tests,
                "owner": owner,
            })

    # sort entries by type then name
    entries.sort(key=lambda x: (x['type'], x['name']))
    return entries


def render_markdown(entries):
    ts = datetime.datetime.utcnow().isoformat() + 'Z'
    lines = []
    lines.append(f"# Monorepo Inventory\n\nGenerated: {ts}\n")
    lines.append("| Name | Path | Type | README | QUARANTINE | Tests | Suggested Owner |")
    lines.append("|---|---|---:|:---:|:---:|:---:|---|")
    for e in entries:
        lines.append(f"| {e['name']} | `{e['path']}` | {e['type']} | {'✅' if e['readme'] else '❌'} | {'✅' if e['quarantine'] else '❌'} | {'✅' if e['tests'] else '❌'} | `{e['owner']}` |")
    lines.append('\n## Notes\n- Suggested owners are heuristic; please review and assign canonical CODEOWNERS or update inventory.')
    return '\n'.join(lines)


def main():
    entries = gather_entries()
    md = render_markdown(entries)
    OUT_FILE.write_text(md, encoding='utf-8')
    print(f"Inventory written: {OUT_FILE}")


if __name__ == '__main__':
    main()

