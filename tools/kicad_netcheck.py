#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Netznamen der erzeugten Schaltplaene gegen die Single Source
of Truth pruefen.

WOZU, wo es doch schon schematic_netcheck.py gibt:
Jenes Werkzeug vergleicht die Design-Specs (Markdown) untereinander. Es kann
nicht sehen, ob der tatsaechlich erzeugte Schaltplan dieselben Netznamen
verwendet. Genau dort entsteht Drift: Ein Generator, der `PCIE_TX_P` still zu
`PCIETXP` macht, faellt keinem Markdown-Check auf -- aber die Netzliste passt
dann nicht mehr zum Gegenstueck auf dem Nachbarboard.

Geprueft wird deshalb: Jedes blattuebergreifende Netz (global_label) muss im
kanonischen Woerterbuch `hardware/INTERFACE_NETS.md` stehen. Lokale Labels
bleiben aussen vor -- die gehoeren dem Blatt und muessen nirgends bruecken.

Exit 0 = konsistent, 1 = Drift.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DICT = REPO / "hardware" / "INTERFACE_NETS.md"

_GLOBAL = re.compile(r'\(global_label\s+"([^"]+)"')
# Netznamen duerfen "+", "-" und "." enthalten (Rails wie "+3V3_SYS").
# Ein Zeichenvorrat von nur [A-Za-z0-9_] haette genau die Power-Rails
# uebersehen -- und damit die Netzklasse, bei der ein Namensdrift am
# teuersten ist.
_TICKED = re.compile(r'`([A-Za-z0-9_+.\-]+)`')

# Netze, die bewusst kein Eintrag im Woerterbuch sind: sie existieren pro
# Radio und werden dort als Muster gefuehrt, nicht einzeln aufgezaehlt.
PATTERNS = [
    re.compile(r'^PA_EN_[A-Z0-9]+$'),     # sheet_01_supervisor_rfkill.md: PA_EN_<radio>
    re.compile(r'^TXREQ_[A-Z0-9]+$'),     # Sendeanforderung je Radio
]


def canonical_names() -> set[str]:
    text = DICT.read_text(encoding="utf-8")
    return set(_TICKED.findall(text))


def main() -> int:
    ap = argparse.ArgumentParser(description="Netznamen Schaltplan <-> Woerterbuch")
    ap.add_argument("--check", action="store_true", help="leise Ausgabe")
    args = ap.parse_args()

    if not DICT.is_file():
        print(f"[FEHLER] {DICT.relative_to(REPO)} fehlt")
        return 1

    known = canonical_names()
    sheets = sorted(REPO.glob("hardware/*/kicad/*.kicad_sch"))
    if not sheets:
        print("[UEBERSPRUNGEN] Noch keine erzeugten Schaltplaene.")
        return 0

    unknown: list[tuple[str, str]] = []
    checked = 0
    for sch in sheets:
        for net in sorted(set(_GLOBAL.findall(sch.read_text(encoding="utf-8")))):
            checked += 1
            if net in known or any(p.match(net) for p in PATTERNS):
                continue
            unknown.append((str(sch.relative_to(REPO)), net))

    if unknown:
        print("  [FEHLER] Blattuebergreifende Netze ohne Eintrag im Woerterbuch:")
        for where, net in unknown:
            print(f"           {net}  ({where})")
        print(f"           -> {DICT.relative_to(REPO)} ergaenzen oder Netz umbenennen.")
        return 1

    if not args.check:
        print(f"  [OK] {checked} blattuebergreifende Netze, alle kanonisch "
              f"({len(sheets)} Sheets).")
    else:
        print(f"Netznamen konsistent ({checked} globale Netze).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
