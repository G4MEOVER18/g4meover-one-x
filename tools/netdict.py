#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Zugriff auf das Netz-Woerterbuch (hardware/INTERFACE_NETS.md).

WARUM ES DIESES MODUL GIBT:

`kicad_netcheck.py` und `kicad_boardlink_check.py` lasen das Woerterbuch bisher
jedes fuer sich -- mit einer wortgleichen Kopie von `canonical_names()` und
jeweils EINER handgepflegten Liste daneben:

    kicad_netcheck.py:        PATTERNS    = [PA_EN_..., TXREQ_...]
    kicad_boardlink_check.py: BOARD_LOCAL = [PA_EN_..., TXREQ_...]

Das Woerterbuch fuehrt denselben Sachverhalt selbst -- im Abschnitt
"Board-lokal". Zwei handgepflegte Kopien neben der Single Source of Truth sind
genau die Drift, die dieses Repo sonst systematisch verhindert: Ein neues
board-lokales Netz haette an DREI Stellen eingetragen werden muessen, und
vergisst man eine, meldet ein Werkzeug einen Fehler, den es nicht gibt --
oder schlimmer: keinen, den es gibt.

Hier wird die Liste deshalb aus dem Woerterbuch abgeleitet.

VORSICHT BEIM PARSEN -- die Blockquotes:
Der Board-lokal-Abschnitt endet mit einer Korrektur-Notiz, die `KEY_*`,
`HAPTIC_*` und `LED_*` nennt -- als Namen, die dort faelschlich standen und
in Wahrheit `J_UI` queren (Session 29). Wuerde man den ganzen Abschnitt
einlesen, geriete ausgerechnet die Korrektur als Regel in die Werkzeuge und
haette den behobenen Fehler wieder eingebaut. Blockquote-Zeilen (">") werden
deshalb uebersprungen: der Abschnitt fuehrt seine Regel in Fliesstext, seine
Historie in Zitaten.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DICT = REPO / "hardware" / "INTERFACE_NETS.md"

# Netznamen duerfen "+", "-" und "." enthalten (Rails wie "+3V3_SYS").
# Ein Zeichenvorrat von nur [A-Za-z0-9_] haette genau die Power-Rails
# uebersehen -- die Netzklasse, bei der ein Namensdrift am teuersten ist.
_TICKED = re.compile(r'`([A-Za-z0-9_+.\-]+)`')
# Dasselbe, aber mit optionalem "*" fuer Familien-Eintraege (`PA_EN_*`).
_TICKED_FAMILY = re.compile(r'`([A-Za-z0-9_+.\-]+\*?)`')

_SECTION = re.compile(r'^#{2,3}\s')

# Masse und Rails liegen naturgemaess auf jedem Board -- als "Verbindung"
# aussagelos.
UBIQUITOUS = {"GND", "AGND"}


def _text() -> str:
    return DICT.read_text(encoding="utf-8") if DICT.is_file() else ""


def canonical_names() -> set[str]:
    """Alle im Woerterbuch woertlich gefuehrten Netznamen."""
    return set(_TICKED.findall(_text()))


def board_local_entries() -> list[str]:
    """
    Roh-Eintraege des Abschnitts "Board-lokal", z.B. ['PA_EN_*', 'VBL', ...].

    Nur Fliesstext-Zeilen; Blockquotes sind Historie, keine Regel (s.o.).
    """
    out: list[str] = []
    inside = False
    for line in _text().splitlines():
        if _SECTION.match(line):
            inside = line.lower().lstrip("# ").startswith("board-lokal")
            continue
        if not inside or line.lstrip().startswith(">"):
            continue
        out.extend(_TICKED_FAMILY.findall(line))
    return out


def board_local_patterns() -> list[re.Pattern]:
    """
    Kompilierte Muster fuer Netze, die per Definition auf genau einem Board
    leben. `NAME_*` wird zum Praefix-Muster, ein voller Name zur exakten
    Uebereinstimmung -- `VBL` darf nicht versehentlich `VBL_SENSE` decken.
    """
    pats = []
    for entry in board_local_entries():
        if entry.endswith("*"):
            pats.append(re.compile("^" + re.escape(entry[:-1])))
        else:
            pats.append(re.compile("^" + re.escape(entry) + "$"))
    return pats


def is_board_local(net: str, pats: list[re.Pattern] | None = None) -> bool:
    return any(p.match(net) for p in (pats if pats is not None
                                      else board_local_patterns()))


if __name__ == "__main__":       # kleine Selbstauskunft
    print(f"Woerterbuch : {DICT}")
    print(f"kanonisch   : {len(canonical_names())} Namen")
    entries = board_local_entries()
    print(f"board-lokal : {len(entries)} Eintraege -> {', '.join(entries)}")
