#!/usr/bin/env python3
"""G4MEOVER ONE-X -- Aggregierter Verifikations-Lauf (ein gruenes Tor vor KiCad/G07).

Fuehrt alle Repo-Checker nacheinander aus und fasst das Ergebnis zusammen:
  1. spec_validator.py       -- Master-Spec konsistent, keine verbotenen Claims
  2. schematic_netcheck.py   -- Inter-Board-Netznamen beidseitig gespiegelt
  3. gen_kicad_project.py     -- KiCad-Ableitung reproduzierbar + selbstgeprueft
  4. gen_kicad_sch.py         -- erzeugte Schaltplaene aktuell
  5. kicad_erc.py             -- ERC ueber die erzeugten Schaltplaene
  6. gen_sourcing.py          -- Sourcing-Register aktuell
  7. fw_test.py               -- Firmware-Unit-Tests (Host-Compiler)

Exit 0 nur, wenn ALLE bestehen; sonst Exit 1. CI-/Handoff-tauglich.

Ein Check darf UEBERSPRUNGEN melden, wenn eine externe Voraussetzung fehlt
(z.B. kein C-Compiler fuer die Firmware-Tests). Das ist kein FAIL, wird aber
sichtbar ausgewiesen -- ein uebersprungener Check darf nie wie ein bestandener
aussehen.

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

# Exit-Code, mit dem ein Check "Voraussetzung fehlt" (statt FAIL) meldet.
RC_SKIPPED = 2

# Alle im read-only --check-Modus, damit der Lauf keine Dateien schreibt (Pre-Commit-tauglich).
# (label, script, args, skippable)
CHECKS = [
    ("Master-Spec (verbotene Claims / Konsistenz)", "spec_validator.py", ["--check"], False),
    ("Netznamen-Konsistenz (Inter-Board-Mirror)", "schematic_netcheck.py", [], False),
    ("KiCad-Ableitung (reproduzierbar + Selbstpruefung)", "gen_kicad_project.py", ["--check"], False),
    ("KiCad-Schaltplaene (reproduzierbar erzeugt)", "gen_kicad_sch.py", ["--check"], False),
    ("KiCad ERC (elektrische Konsistenz)", "kicad_erc.py", ["--check"], True),
    ("Sourcing-Register (BOM -> Bestellung)", "gen_sourcing.py", ["--check"], False),
    ("Firmware-Unit-Tests (Codec/RF-Kill/Link/Power/Watchdog)", "fw_test.py", ["--check"], True),
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
    for label, script, args, skippable in CHECKS:
        rc, out = run(script, args)
        if skippable and rc == RC_SKIPPED:
            state = "SKIP"
        else:
            state = "PASS" if rc == 0 else "FAIL"
        results.append((label, script, state))
        print(f"\n[{state}] {label}")
        print(f"       ({script})  ->  {last_meaningful_line(out)}")
        if state == "FAIL":
            # bei Fehler mehr Kontext zeigen
            for ln in out.splitlines()[-12:]:
                print(f"       | {ln}")

    print("\n" + "-" * 64)
    passed = sum(1 for _, _, st in results if st == "PASS")
    skipped = sum(1 for _, _, st in results if st == "SKIP")
    failed = sum(1 for _, _, st in results if st == "FAIL")
    total = len(results)

    if failed:
        print(f"ERGEBNIS: {passed}/{total} gruen -- {failed} Check(s) FAIL, vor G07 beheben.")
        return 1

    if skipped:
        # Ehrlich benennen: das Tor ist offen, aber nicht vollstaendig geprueft.
        names = ", ".join(s for _, s, st in results if st == "SKIP")
        print(f"ERGEBNIS: {passed}/{total} gruen, {skipped} uebersprungen ({names}) "
              f"-- Voraussetzung fehlt, NICHT vollstaendig geprueft.")
        return 0

    print(f"ERGEBNIS: {passed}/{total} gruen -- Repo bereit fuer die KiCad-Phase (G07).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
