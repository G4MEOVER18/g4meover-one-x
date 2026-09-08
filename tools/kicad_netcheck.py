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

try:                       # Konsolen unter Windows sind oft cp1252;
    sys.stdout.reconfigure(encoding="utf-8")   # Netznamen enthalten aber
except (AttributeError, ValueError):           # Zeichen wie Ohm.
    pass

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


# Zeilen, die zwei Netznamen mit einer Ellipse verbinden ("`A` … `B`").
# Solche Kurzschreibweisen sind fuer Menschen lesbar, aber maschinell
# unvollstaendig: was dazwischen liegt, kommt nie woertlich vor und gilt
# deshalb als unbekannt. Genau dieser Fehler ist im Projekt zweimal
# aufgetreten (DSI-Datenlanes, Softkeys) -- daher wird er jetzt gemeldet,
# statt auf Disziplin zu hoffen.
_ELLIPSIS_ROW = re.compile(
    r'`([A-Za-z0-9_+.\-]+)`\s*(?:…|\.\.\.|\.\.)\s*`([A-Za-z0-9_+.\-]+)`')
# Gemeinsamer Stamm + laufende Nummer, z.B. DSI0_D0_P / DSI0_D3_P
_RANGE = re.compile(r'^(.*?)(\d+)(.*)$')


def canonical_names() -> set[str]:
    text = DICT.read_text(encoding="utf-8")
    return set(_TICKED.findall(text))


def find_ellipsis_gaps(known: set[str]) -> list[str]:
    """
    Meldet Abkuerzungen NUR, wenn dadurch wirklich Namen fehlen.

    Eine Ellipse im Fliesstext ist harmlos, solange die Tabelle daneben alle
    Namen einzeln fuehrt. Ein pauschaler Alarm auf jede Ellipse waere ein
    Fehlalarm-Generator; geprueft wird deshalb, ob die Zwischenwerte
    tatsaechlich im Woerterbuch stehen.
    """
    out = []
    for i, line in enumerate(DICT.read_text(encoding="utf-8").splitlines(), 1):
        for lo, hi in _ELLIPSIS_ROW.findall(line):
            ml, mh = _RANGE.match(lo), _RANGE.match(hi)
            if not (ml and mh):
                continue
            if ml.group(1) != mh.group(1) or ml.group(3) != mh.group(3):
                continue          # kein gemeinsamer Stamm -> keine Zaehlreihe
            a, b = int(ml.group(2)), int(mh.group(2))
            if b <= a:
                continue
            missing = [f"{ml.group(1)}{n}{ml.group(3)}"
                       for n in range(a + 1, b)
                       if f"{ml.group(1)}{n}{ml.group(3)}" not in known]
            if missing:
                out.append(f"Zeile {i}: `{lo}` … `{hi}` -- es fehlen: "
                           f"{', '.join(missing)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Netznamen Schaltplan <-> Woerterbuch")
    ap.add_argument("--check", action="store_true", help="leise Ausgabe")
    args = ap.parse_args()

    if not DICT.is_file():
        print(f"[FEHLER] {DICT.relative_to(REPO)} fehlt")
        return 1

    known = canonical_names()

    # Abgekuerzte Netzlisten im Woerterbuch sind ein Befund fuer sich: sie
    # sehen vollstaendig aus, sind es aber nicht.
    ellipses = find_ellipsis_gaps(known)
    if ellipses:
        print("  [FEHLER] Abgekuerzte Netzlisten im Woerterbuch "
              "(bitte ausschreiben):")
        for e in ellipses:
            print(f"           {e}")
        print("           Was zwischen den Enden liegt, kommt nie woertlich vor")
        print("           und gilt damit als unbekanntes Netz. Bitte ausschreiben.")
        return 1

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
