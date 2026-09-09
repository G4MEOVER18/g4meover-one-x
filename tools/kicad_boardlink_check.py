#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Board-gegen-Board-Pruefung der Inter-Board-Netze.

Die staerkste der Netzpruefungen, und erst moeglich, seit das Mainboard-Blatt
mit den Verbindern existiert:

  * `schematic_netcheck.py` vergleicht Design-Specs (Markdown) untereinander.
  * `kicad_netcheck.py` prueft, ob Netznamen im Schaltplan kanonisch sind.
  * Hier wird geprueft, ob ein Inter-Board-Netz auf BEIDEN Seiten wirklich
    ankommt -- im erzeugten Schaltplan, nicht in der Doku.

Ein Netz, das nur auf einem Board existiert, ist eine Leitung ins Nichts: Der
Stecker fuehrt sie, das Gegenstueck kennt sie nicht. Das faellt sonst erst auf,
wenn die Boards zusammengesteckt werden.

Bewusst gemeldet, aber NICHT als Fehler gewertet, wird der umgekehrte Fall:
ein kanonisches Netz, das noch auf gar keinem Board vorkommt. Das ist kein
Defekt, sondern schlicht ein Blatt, das es noch nicht gibt -- die Zahl zeigt
den Ausbaustand.

Exit 0 = jede gezeichnete Verbindung hat zwei Enden. 1 = einseitiges Netz.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

REPO = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from netdict import (                                          # noqa: E402
    DICT, UBIQUITOUS, board_local_patterns, canonical_names,
)

_GLOBAL = re.compile(r'\(global_label\s+"([^"]+)"')

# Netze, die per Definition auf genau einem Board leben, kommen aus dem
# Woerterbuch selbst (Abschnitt "Board-lokal") -- frueher stand hier eine
# handgepflegte Kopie daneben. Eine zweite Wahrheit neben der Single Source
# of Truth driftet zwangslaeufig; siehe tools/netdict.py.
BOARD_LOCAL = board_local_patterns()


def boards_with_nets() -> dict[str, set[str]]:
    """Board -> Menge seiner blattuebergreifenden Netze."""
    out: dict[str, set[str]] = {}
    for sch in REPO.glob("hardware/*/kicad/*.kicad_sch"):
        board = sch.parent.parent.name
        nets = set(_GLOBAL.findall(sch.read_text(encoding="utf-8")))
        out.setdefault(board, set()).update(nets)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Inter-Board-Netze beidseitig?")
    ap.add_argument("--check", action="store_true", help="leise Ausgabe")
    args = ap.parse_args()

    per_board = boards_with_nets()
    if len(per_board) < 2:
        print("[UEBERSPRUNGEN] Weniger als zwei Boards mit Schaltplaenen.")
        return 0

    known = canonical_names()

    # Wo kommt jedes Netz vor?
    where: dict[str, set[str]] = {}
    for board, nets in per_board.items():
        for net in nets:
            if net in UBIQUITOUS or any(p.match(net) for p in BOARD_LOCAL):
                continue
            where.setdefault(net, set()).add(board)

    one_sided = {n: b for n, b in where.items() if len(b) == 1}
    linked = {n: b for n, b in where.items() if len(b) > 1}
    # Kanonische Netze, die noch nirgends gezeichnet sind -> Ausbaustand.
    undrawn = sorted(
        n for n in known
        if n not in where and not any(p.match(n) for p in BOARD_LOCAL)
        and n not in UBIQUITOUS and "_" in n
    )

    if one_sided:
        print("  [FEHLER] Inter-Board-Netze mit nur EINEM Ende:")
        for net, boards in sorted(one_sided.items()):
            print(f"           {net}  (nur auf {', '.join(sorted(boards))})")
        print("           Der Stecker fuehrt die Leitung, das Gegenstueck kennt sie nicht.")
        return 1

    if not args.check:
        print("=" * 64)
        print(" ONE-X -- Board-gegen-Board-Verbindungen")
        print("=" * 64)
        print(f"  [OK] {len(linked)} Netze mit beidseitigem Anschluss "
              f"({len(per_board)} Boards):")
        for net, boards in sorted(linked.items())[:6]:
            print(f"       {net:16} {' <-> '.join(sorted(boards))}")
        if len(linked) > 6:
            print(f"       ... und {len(linked) - 6} weitere")
        print(f"\n  Ausbaustand: {len(undrawn)} kanonische Netze noch auf keinem "
              f"Board gezeichnet")
        print("  (kein Defekt -- die zugehoerigen Blaetter existieren noch nicht)")
    else:
        print(f"Board-Verbindungen konsistent ({len(linked)} beidseitig, "
              f"{len(undrawn)} noch ungezeichnet).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
