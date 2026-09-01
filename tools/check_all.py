#!/usr/bin/env python3
"""G4MEOVER ONE-X -- Aggregierter Verifikations-Lauf (ein gruenes Tor vor KiCad/G07).

Fuehrt alle Repo-Checker nacheinander aus und fasst das Ergebnis zusammen:
  1. spec_validator.py       -- Master-Spec konsistent, keine verbotenen Claims
  2. schematic_netcheck.py   -- Inter-Board-Netznamen beidseitig gespiegelt
  3. gen_kicad_project.py     -- KiCad-Ableitung reproduzierbar + selbstgeprueft

Exit 0 nur, wenn ALLE bestehen; sonst Exit 1. CI-/Handoff-tauglich.
Aufruf:  python tools/check_all.py
"""
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

TOOLS = Path(__file__).resolve().parent
# Alle im read-only --check-Modus, damit der Lauf keine Dateien schreibt (Pre-Commit-tauglich).
CHECKS = [
    ("Master-Spec (verbotene Claims / Konsistenz)", "spec_validator.py", ["--check"]),
    ("Netznamen-Konsistenz (Inter-Board-Mirror)", "schematic_netcheck.py", []),
    ("KiCad-Ableitung (reproduzierbar + Selbstpruefung)", "gen_kicad_project.py", ["--check"]),
]


def run(script, args):
    proc = subprocess.run(
        [sys.executable, str(TOOLS / script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def last_meaningful_line(out):
    lines = [ln.rstrip() for ln in out.splitlines() if ln.strip()]
    return lines[-1] if lines else "(keine Ausgabe)"


def main():
    print("=" * 64)
    print(" G4MEOVER ONE-X -- Aggregierter Verifikations-Lauf")
    print("=" * 64)
    results = []
    for label, script, args in CHECKS:
        rc, out = run(script, args)
        ok = rc == 0
        results.append((label, script, ok))
        badge = "PASS" if ok else "FAIL"
        print(f"\n[{badge}] {label}")
        print(f"       ({script})  ->  {last_meaningful_line(out)}")
        if not ok:
            # bei Fehler mehr Kontext zeigen
            for ln in out.splitlines()[-12:]:
                print(f"       | {ln}")

    print("\n" + "-" * 64)
    passed = sum(1 for _, _, ok in results if ok)
    total = len(results)
    if passed == total:
        print(f"ERGEBNIS: {passed}/{total} gruen -- Repo bereit fuer die KiCad-Phase (G07).")
        return 0
    print(f"ERGEBNIS: {passed}/{total} gruen -- {total - passed} Check(s) FAIL, vor G07 beheben.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
