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
import re
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
    {
        # power + watchdog + ihre Kopplung an den RF-Kill (Sicherheitskette).
        "name": "onex_power + onex_watchdog (safety-critical)",
        "sources": [
            FW / "src" / "onex_power.c",
            FW / "src" / "onex_watchdog.c",
            FW / "src" / "onex_rfkill.c",
        ],
        "test": FW / "test" / "test_onex_power.c",
    },
    {
        # Integrationssuite: Codec + RF-Kill + Endpunkt ueber die Drahtdarstellung.
        "name": "onex_link (Protokoll-Endpunkt, Integration)",
        "sources": [
            FW / "src" / "onex_link.c",
            FW / "src" / "onex_proto.c",
            FW / "src" / "onex_rfkill.c",
        ],
        "test": FW / "test" / "test_onex_link.c",
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


# ---------------------------------------------------------------------------
# Statische Vorpruefung: fehlende <stddef.h>-Includes
#
# Warum eigens geprueft: Manche libc-Implementierungen (z. B. MinGW) ziehen
# NULL/size_t beilaeufig ueber <stdint.h> mit herein, glibc nicht. Eine Datei,
# die NULL nutzt, ohne <stddef.h> zu erreichen, kompiliert dann lokal
# anstandslos und faellt erst in der CI um. Genau so ein Fehler ist in
# Session 23 aufgetreten -- diese Pruefung faengt ihn plattformunabhaengig.
# ---------------------------------------------------------------------------

# Systemheader, die NULL/size_t garantiert mitbringen.
STDDEF_PROVIDERS = {"stddef.h", "string.h", "stdio.h", "stdlib.h", "time.h"}
# Symbole, die <stddef.h> braucht.
STDDEF_SYMBOLS = ("NULL", "size_t", "ptrdiff_t", "offsetof")

_SYS_INCLUDE = re.compile(r'^\s*#\s*include\s*<([^>]+)>', re.MULTILINE)
_OWN_INCLUDE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.MULTILINE)
# Kommentare und Zeichenketten grob entfernen, damit ein "NULL" im Fliesstext
# keinen Fehlalarm ausloest.
_STRIP = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', re.DOTALL)


def _reaches_stddef(path: Path, seen: set[Path]) -> bool:
    """Erreicht path (transitiv ueber eigene Header) einen stddef-Lieferanten?"""
    if path in seen or not path.is_file():
        return False
    seen.add(path)

    text = path.read_text(encoding="utf-8", errors="replace")
    if STDDEF_PROVIDERS & set(_SYS_INCLUDE.findall(text)):
        return True
    return any(
        _reaches_stddef(FW / "include" / own, seen)
        for own in _OWN_INCLUDE.findall(text)
    )


def check_stddef_includes(quiet: bool) -> bool:
    files = sorted(FW.glob("**/*.c")) + sorted(FW.glob("**/*.h"))
    bad = []
    for f in files:
        body = _STRIP.sub(" ", f.read_text(encoding="utf-8", errors="replace"))
        used = [s for s in STDDEF_SYMBOLS if re.search(rf'\b{s}\b', body)]
        if used and not _reaches_stddef(f, set()):
            bad.append((f, used))

    if bad:
        print("  [FEHLER] Datei nutzt stddef-Symbole ohne <stddef.h> zu erreichen:")
        for f, used in bad:
            print(f"           {f.relative_to(REPO)}  ->  {', '.join(used)}")
        print("           (kompiliert je nach libc trotzdem -- faellt spaeter in der CI um)")
        return False
    if not quiet:
        print(f"  [OK] stddef-Includes vollstaendig ({len(files)} Dateien geprueft)")
    return True


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

    # Vorpruefung: laeuft ohne Compiler-Lauf und faengt libc-abhaengige
    # Include-Luecken, die lokal unsichtbar bleiben.
    if not args.check:
        print("\n>> Statische Vorpruefung")
    ok = check_stddef_includes(quiet=args.check)

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
