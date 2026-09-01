#!/usr/bin/env python3
"""G4MEOVER ONE-X -- Git-Hooks aktivieren.

Setzt core.hooksPath auf .githooks (repo-verfolgt), sodass der pre-commit-Hook
vor jedem Commit tools/check_all.py (read-only) laeuft. Idempotent.

Aufruf:  python tools/install_hooks.py
"""
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent


def main():
    hooks = ROOT / ".githooks"
    if not (hooks / "pre-commit").exists():
        print(f"[FEHLER] {hooks/'pre-commit'} fehlt.")
        return 1
    r = subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT)
    if r.returncode != 0:
        print("[FEHLER] 'git config core.hooksPath .githooks' fehlgeschlagen.")
        return 1
    # Ausfuehrbar markieren (fuer POSIX; unter Git-for-Windows unkritisch)
    try:
        (hooks / "pre-commit").chmod(0o755)
    except OSError:
        pass
    print("core.hooksPath -> .githooks gesetzt. pre-commit-Hook aktiv (check_all.py, read-only).")
    print("Umgehen bei Bedarf: git commit --no-verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
