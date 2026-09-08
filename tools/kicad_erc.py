#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — ERC-Lauf ueber die erzeugten KiCad-Schaltplaene.

Bis KiCad verfuegbar war, konnte dieses Repo Schaltplaene nur als Design-Spec
in Markdown fuehren: pruefbar auf Netznamen, aber nicht auf elektrische
Konsistenz. Mit `kicad-cli sch erc` wird aus dem generierten Schaltplan ein
Artefakt, dessen Verdrahtung eine Maschine nachrechnet.

Der Nutzen ist nicht theoretisch: Der erste Lauf fand 120 Verstoesse im
Generator -- darunter ein Power-Flag, dessen Draht Masse mit einem
Antennen-Feed kurzschloss. Im Bild unsichtbar, in der Netzliste fatal.

KEINE AUSNAHMEN MEHR:
Solange Einzelblaetter geprueft wurden, war eine Ausnahme fuer
`lib_symbol_issues` noetig -- kicad-cli laedt bei einer einzelnen .kicad_sch
nur die globale Symboltabelle, nicht die projektbezogene `sym-lib-table`.
Seit die Pruefung an den BOARD-ROOTS ansetzt, findet KiCad die Bibliothek und
die Meldung entfaellt vollstaendig. Die Ausnahme wurde daraufhin entfernt:
eine Ausnahme, die nichts mehr unterdrueckt, verdeckt irgendwann echte Faelle.

Die Symbolbibliothek wird weiterhin separat validiert (rendern via
`sym export svg`) -- das ist billig und beweist, dass sie ladbar ist.

Exit 0 = sauber. 1 = Verstoesse. 2 = kicad-cli fehlt (SKIP, kein Fehler).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_env import find_kicad_cli   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SYMBOL_LIB = REPO / "hardware" / "kicad" / "onex.kicad_sym"

# Kategorien, die geprueft, aber nicht als Fehler gewertet werden.
# Bewusst LEER: im Board-Kontext ist keine noetig. Bleibt als Mechanismus
# bestehen, damit eine kuenftige Ausnahme benannt und begruendet werden muss,
# statt still im Code zu verschwinden.
IGNORED: dict[str, str] = {}

_CATEGORY = re.compile(r'^\[([a-z_]+)\]', re.MULTILINE)


def run_erc(cli: str, sch: Path, tmp: Path) -> tuple[dict[str, int], str]:
    rpt = tmp / (sch.stem + ".rpt")
    subprocess.run([cli, "sch", "erc", "--output", str(rpt), str(sch)],
                   capture_output=True, text=True)
    if not rpt.is_file():
        return ({"__no_report__": 1}, "")
    text = rpt.read_text(encoding="utf-8", errors="replace")
    counts: dict[str, int] = {}
    for cat in _CATEGORY.findall(text):
        counts[cat] = counts.get(cat, 0) + 1
    return counts, text


def validate_symbol_lib(cli: str, tmp: Path) -> bool:
    """Gegenprobe zur ignorierten Bibliothekswarnung: laesst sich die
    Bibliothek tatsaechlich laden und rendern?"""
    if not SYMBOL_LIB.is_file():
        print(f"  [FEHLER] {SYMBOL_LIB.relative_to(REPO)} fehlt")
        return False
    proc = subprocess.run(
        [cli, "sym", "export", "svg", "--output", str(tmp / "sym"), str(SYMBOL_LIB)],
        capture_output=True, text=True)
    if proc.returncode != 0:
        print("  [FEHLER] Symbolbibliothek laesst sich nicht laden:")
        print("           " + (proc.stderr.strip() or proc.stdout.strip())[:300])
        return False
    n = len(list((tmp / "sym").glob("*.svg")))
    print(f"  [OK] Symbolbibliothek geladen und gerendert ({n} Symbole)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="ERC ueber alle ONE-X-Schaltplaene")
    ap.add_argument("--check", action="store_true", help="leise Ausgabe (Hook/CI)")
    args = ap.parse_args()

    cli = find_kicad_cli()
    if cli is None:
        print("[UEBERSPRUNGEN] kicad-cli nicht gefunden "
              "(KiCad installieren oder $KICAD_CLI setzen).")
        return 2

    # Board-Roots, nicht Einzelblaetter: ein Board ist mehr als die Summe
    # seiner Blaetter. Erst im Board-Kontext verbinden sich globale Labels
    # ueber Blattgrenzen, und genau dort entstehen die interessanten Fehler
    # (zwei Power-Flags auf einem Netz etwa sieht man einzeln nie).
    sheets = sorted(
        p for p in REPO.glob("hardware/*/kicad/*.kicad_sch")
        if p.stem == p.parent.parent.name
    )
    if not sheets:
        print("[UEBERSPRUNGEN] Noch keine Board-Roots "
              "(tools/gen_kicad_sch.py).")
        return 2

    if not args.check:
        print("=" * 64)
        print(" ONE-X -- KiCad ERC")
        print("=" * 64)

    ok = True
    total_real = 0
    with tempfile.TemporaryDirectory(prefix="onex_erc_") as td:
        tmp = Path(td)
        if not validate_symbol_lib(cli, tmp):
            ok = False

        for sch in sheets:
            counts, text = run_erc(cli, sch, tmp)
            real = {k: v for k, v in counts.items() if k not in IGNORED}
            ignored = {k: v for k, v in counts.items() if k in IGNORED}
            rel = sch.relative_to(REPO)

            if real:
                ok = False
                total_real += sum(real.values())
                print(f"  [FEHLER] {rel}")
                for k, v in sorted(real.items()):
                    print(f"           {v:3}x {k}")
                for line in text.splitlines():
                    if any(line.startswith(f"[{k}]") for k in real):
                        print(f"           | {line[:110]}")
            elif not args.check:
                note = ""
                if ignored:
                    note = "  (" + ", ".join(
                        f"{v}x {k} ignoriert" for k, v in ignored.items()) + ")"
                print(f"  [OK] {rel}{note}")

    if ok:
        if not args.check:
            print(f"\nERGEBNIS: {len(sheets)} Schaltplan-Sheet(s) ERC-sauber.")
            for k, why in IGNORED.items():
                print(f"  Bewusst ignoriert: {k} -- {why}")
            if not IGNORED:
                print("  Keine Ausnahmen noetig.")
        else:
            print(f"ERC sauber ({len(sheets)} Board(s), Bibliothek validiert).")
        return 0

    print(f"\nERGEBNIS: {total_real} ERC-Verstoss/Verstoesse -- vor G07 beheben.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
