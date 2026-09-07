#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Firmware-Unit-Tests (Host).

Kompiliert und startet die hardware-unabhaengigen Teile der RP2350B-Firmware
mit dem System-Compiler. Bewusst OHNE arm-none-eabi: getestet wird nur Logik,
die frei von Pin-/HAL-Annahmen ist (Pinmap ist HOLD bis Gate G07). Genau dieser
Schnitt macht die Firmware schon vor der Hardware verifizierbar.

Warum ein Python-Runner statt Makefile: alle Werkzeuge dieses Repos sind
reine Python-stdlib und laufen identisch unter Windows und in der CI
(siehe tools/check_all.py).

Aufruf:
    python tools/fw_test.py            # bauen + ausfuehren
    python tools/fw_test.py --check    # dito, aber leise (fuer Hook/CI)

Exit 0 = alle Tests gruen. Exit 1 = Fehler. Exit 2 = kein Compiler gefunden.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FW = REPO / "firmware" / "rp2350"

# Uebersetzungseinheiten: Quelle + zugehoerige Testdatei.
SUITES = [
    {
        "name": "onex_proto (ONE-X-Link v1 Codec)",
        "sources": [FW / "src" / "onex_proto.c"],
        "test": FW / "test" / "test_onex_proto.c",
    },
    {
        "name": "onex_rfkill (RF-Kill-Zustandsautomat, safety-critical)",
        "sources": [FW / "src" / "onex_rfkill.c"],
        "test": FW / "test" / "test_onex_rfkill.c",
    },
]

# Streng: Warnungen sind Fehler. Firmware-Code, der auf dem Host warnt,
# warnt auf dem Cortex-M33 auch -- nur faellt es dort niemandem auf.
CFLAGS = [
    "-std=c11",
    "-O2",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wpedantic",
    "-Wconversion",
    "-Wshadow",
    "-Wstrict-prototypes",
    f"-I{FW / 'include'}",
]


def find_compiler() -> str | None:
    """Bevorzugt $CC, sonst gcc/cc/clang."""
    env_cc = os.environ.get("CC")
    if env_cc and shutil.which(env_cc):
        return env_cc
    for name in ("gcc", "cc", "clang"):
        if shutil.which(name):
            return name
    return None


def run_suite(cc: str, suite: dict, workdir: Path, quiet: bool) -> bool:
    missing = [p for p in [*suite["sources"], suite["test"]] if not p.is_file()]
    if missing:
        for p in missing:
            print(f"  [FEHLT] {p.relative_to(REPO)}")
        return False

    exe = workdir / (suite["test"].stem + (".exe" if os.name == "nt" else ""))
    cmd = [cc, *CFLAGS, str(suite["test"]), *map(str, suite["sources"]), "-o", str(exe)]

    build = subprocess.run(cmd, capture_output=True, text=True)
    if build.returncode != 0:
        print(f"  [BUILD-FEHLER] {suite['name']}")
        print(build.stderr.strip() or build.stdout.strip())
        return False
    if build.stderr.strip():  # sollte durch -Werror nie vorkommen
        print(build.stderr.strip())

    run = subprocess.run([str(exe)], capture_output=True, text=True)
    if run.returncode != 0 or not quiet:
        out = (run.stdout + run.stderr).strip()
        for line in out.splitlines():
            print(f"  {line}")
    return run.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ONE-X Firmware-Host-Tests")
    ap.add_argument("--check", action="store_true",
                    help="leise Ausgabe (nur Fehler), fuer pre-commit/CI")
    args = ap.parse_args()

    cc = find_compiler()
    if cc is None:
        # Kein Compiler ist kein bestandener Test -- aber auch kein Design-Fehler.
        # Eigener Exit-Code, damit check_all das unterscheiden kann.
        print("[UEBERSPRUNGEN] Kein C-Compiler gefunden (gcc/cc/clang, $CC).")
        return 2

    if not args.check:
        print("=" * 64)
        print(" ONE-X -- Firmware-Unit-Tests (Host, Compiler: %s)" % cc)
        print("=" * 64)

    ok = True
    with tempfile.TemporaryDirectory(prefix="onex_fwtest_") as tmp:
        for suite in SUITES:
            if not args.check:
                print(f"\n>> {suite['name']}")
            if not run_suite(cc, suite, Path(tmp), quiet=args.check):
                ok = False

    if ok:
        # Auch im --check-Modus eine Zeile: check_all zeigt die letzte
        # Ausgabezeile als Beleg an -- Stille laese sich nicht von "nichts getan"
        # unterscheiden.
        n = len(SUITES)
        print(f"{'ERGEBNIS: ' if not args.check else ''}"
              f"alle Firmware-Tests gruen ({n} Suite{'n' if n != 1 else ''}, Compiler: {cc}).")
        return 0

    print("\nERGEBNIS: Firmware-Tests FEHLGESCHLAGEN.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
