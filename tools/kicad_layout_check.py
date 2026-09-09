#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Lesbarkeits-Waechter fuer die erzeugten Schaltplaene.

WARUM ES DIESEN CHECK GIBT:

In Session 31 war RF-Core Sheet 07 **ERC-sauber und trotzdem unbrauchbar**:
Textbloecke lagen ueber der Testpunktreihe, Netz-Labels auf den Symbolen, und
drei Viertel des A3-Blattes waren leer. ERC prueft Elektrik -- ob ein Mensch
den Plan lesen kann, prueft es nicht. Aufgefallen ist es nur, weil ich das
Blatt zufaellig geplottet und angesehen habe.

Genau dieselbe Lage wie beim Ellipsen-Waechter (Session 29): ein Fehler, der
sich wiederholen wird, solange nur Disziplin dagegen steht. Ein Schaltplan ist
eine REVIEW-Grundlage -- einer, den der Reviewer nicht lesen kann, erfuellt
seinen Zweck nicht, egal wie sauber die Netzliste ist.

WAS GEPRUEFT WIRD:

  1. Beschriftungen, die einander ueberlagern (Freitext, Labels, Bauteilwerte).
  2. Beschriftungen ausserhalb des Zeichenbereichs.
  3. Beschriftungen im Titelblock -- dort werden sie unlesbar ueberdruckt.
  4. Blatt-Titel, aus denen `kicad-cli` keine Datei schreiben kann.

ZU (4) -- ein stiller Ausfall, gefunden beim Bauen dieses Checks:
`kicad-cli sch export svg` baut den Dateinamen aus dem BLATT-TITEL. Der Titel
von UI-Carrier Sheet 03 enthielt einen Doppelpunkt ("Eingabe: D-Pad ..."). Auf
Windows trennt ein Doppelpunkt im Dateinamen einen NTFS-Datenstrom ab: Es
entstand eine 0-Byte-Datei, kicad-cli meldete Erfolg, und das Blatt liess sich
schlicht nicht plotten -- also auch nicht reviewen. Ein Fehler, der niemandem
auffaellt, bis jemand genau dieses eine Blatt sehen will.

WAS BEWUSST NICHT GEPRUEFT WIRD:

Symbolgrafik gegen Symbolgrafik und Draehte gegen Text. Kreuzende Draehte sind
in Schaltplaenen normal, und eine Beschriftung, die einen Draht streift, ist
noch lesbar. Ein Waechter, der beides meldet, waere ein Fehlalarm-Generator --
und ein Werkzeug, dessen Meldungen man wegklickt, schuetzt vor nichts.

FONT-METRIK:
Der KiCad-Strichfont hat keine feste Zeichenbreite. `W_FACTOR` ist an
geplotteten Blaettern kalibriert (s.u.); zusammen mit `MIN_OVERLAP` meldet der
Check erst eine *echte* Ueberlagerung, keine Beruehrung.

Aufruf:
    python tools/kicad_layout_check.py           # Bericht
    python tools/kicad_layout_check.py --check   # leise, fuer check_all
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

# --- Font-Metrik ------------------------------------------------------------
# Mittlere Vorschubbreite je Zeichen als Vielfaches der Fonthoehe, kalibriert
# an geplotteten A3-Blaettern (Messreihe ueber Texte in size 1.27 und 2.0:
# 0,77 bis 0,88). 0,85 liegt bewusst am oberen Rand -- lieber eine knappe
# Ueberlagerung melden als eine echte uebersehen.
W_FACTOR = 0.85
# Zeilenhoehe inkl. Ober-/Unterlaengen.
H_FACTOR = 1.2
# Ab wann eine Ueberlappung gemeldet wird. Zwei Beschriftungen, die sich um
# Haaresbreite beruehren, sind lesbar -- ohne Schwelle waere der Check ein
# Fehlalarm-Generator.
#
# Vertikal RELATIV zur Zeilenhoehe: Ein fester Millimeterwert taugt hier nicht.
# Eine Zeile in size 1.27 ist nur 1,52 mm hoch; eine feste Schwelle von 1,2 mm
# haette also erst bei fast vollstaendiger Ueberdeckung angeschlagen, waehrend
# sie bei grossen Ueberschriften ueberempfindlich gewesen waere. 40 % der
# kleineren Zeilenhoehe trifft beide Groessen gleich.
MIN_OVERLAP_REL = 0.40
# Horizontal absolut: rund ein Zeichen Ueberdeckung.
MIN_OVERLAP_X = 0.8

# Zeichen, an denen der Datei-Export scheitert. `:` und `\` trennen unter
# Windows Datenstrom bzw. Pfad; die uebrigen sind auf mindestens einem der
# Zielsysteme unzulaessig. `/` fehlt bewusst: kicad-cli ersetzt es durch "_",
# das funktioniert nachweislich (mehrere Titel im Repo enthalten es).
TITLE_FORBIDDEN = ':\\*?"<>|'

# --- Blattgeometrie (A3, wie in Sheet.render() gesetzt) ---------------------
SHEET_W, SHEET_H = 420.0, 297.0
MARGIN = 10.0                      # Rahmenrand
# Titelblock unten rechts. Masse aus dem geplotteten Blatt abgenommen; der
# Block ist bei KiCad fest, deshalb als Konstante statt geraten.
TITLE_X, TITLE_Y = 215.0, 235.0

# --- Parser -----------------------------------------------------------------
#
# Bewusst zeilen-/einrueckungsbasiert statt echter S-Expression-Parser: Die
# Dateien kommen alle aus gen_kicad_sch.py und haben ein festes Format. Die
# Einrueckung trennt zuverlaessig, was auf dem BLATT liegt (1 Tab) von dem, was
# zur Symbol-DEFINITION gehoert (3 Tabs) -- letztere traegt lokale Koordinaten
# und haette als Blattposition gelesen nur Unsinn ergeben.
_TEXT = re.compile(
    r'^\t\(text "((?:[^"\\]|\\.)*)" \(exclude_from_sim \w+\) \(at ([-\d.]+) ([-\d.]+) (\d+)\)')
_LABEL = re.compile(
    r'^\t\((global_label|label) "((?:[^"\\]|\\.)*)"')
_AT = re.compile(r'\(at ([-\d.]+) ([-\d.]+) (\d+)\)')
_SIZE = re.compile(r'\(font \(size ([\d.]+) [\d.]+\)\)')
# Sichtbare Beschriftung eines platzierten Bauteils (2 Tabs = im Blatt-Symbol).
_PROP = re.compile(
    r'^\t\t\(property "(Reference|Value)" "((?:[^"\\]|\\.)*)" \(at ([-\d.]+) ([-\d.]+) (\d+)\)')


class Box:
    __slots__ = ("x1", "y1", "x2", "y2", "text", "kind")

    def __init__(self, x1, y1, x2, y2, text, kind):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.text, self.kind = text, kind

    def overlap(self, o: "Box") -> tuple[float, float]:
        return (min(self.x2, o.x2) - max(self.x1, o.x1),
                min(self.y2, o.y2) - max(self.y1, o.y1))

    def collides(self, o: "Box") -> tuple[float, float] | None:
        ox, oy = self.overlap(o)
        min_y = min(self.y2 - self.y1, o.y2 - o.y1) * MIN_OVERLAP_REL
        return (ox, oy) if ox > MIN_OVERLAP_X and oy > min_y else None

    def __repr__(self):
        return f"{self.text[:34]!r} @ ({self.x1:.0f},{self.y1:.0f})"


def _dims(text: str, size: float) -> tuple[float, float]:
    return len(text) * size * W_FACTOR, size * H_FACTOR


def boxes_of(path: Path) -> list[Box]:
    """Bounding-Boxen aller sichtbaren Beschriftungen eines Blattes."""
    out: list[Box] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    for i, line in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""

        m = _TEXT.match(line)
        if m:
            txt, x, y, rot = m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4))
            if rot:                      # gedrehter Freitext kommt nicht vor
                continue
            size = float(sm.group(1)) if (sm := _SIZE.search(nxt)) else 1.27
            w, h = _dims(txt, size)
            # justify left bottom: Ankerpunkt ist die Grundlinie links.
            out.append(Box(x, y - h, x + w, y, txt, "Text"))
            continue

        m = _LABEL.match(line)
        if m:
            kind, txt = m.group(1), m.group(2)
            block = "\n".join(lines[i:i + 6])
            am, sm = _AT.search(block), _SIZE.search(block)
            if not am:
                continue
            x, y, rot = float(am.group(1)), float(am.group(2)), int(am.group(3))
            if rot:
                continue
            size = float(sm.group(1)) if sm else 1.27
            w, h = _dims(txt, size)
            if kind == "global_label":
                w += size * 2.2         # Pfeil-/Kaestchenrand
            # Labels sitzen vertikal mittig auf ihrem Ankerpunkt.
            out.append(Box(x, y - h / 2, x + w, y + h / 2, txt, "Label"))
            continue

        m = _PROP.match(line)
        if m:
            txt = m.group(2)
            # NUR die eigene Zeile pruefen. Ein Blick in die Folgezeile war hier
            # zuerst als Vorsicht gedacht und bewirkte das Gegenteil: Auf jede
            # "Value"-Property folgt die versteckte "Footprint"-Property -- damit
            # verwarf der Check saemtliche Bauteilwerte und war auf einem Auge
            # blind. Aufgedeckt vom eigenen Mutationstest (vgl. Session 27:
            # Pruefwerkzeuge selbst pruefen).
            if not txt or "(hide yes)" in line:
                continue
            x, y = float(m.group(3)), float(m.group(4))
            size = float(sm.group(1)) if (sm := _SIZE.search(line)) else 1.27
            w, h = _dims(txt, size)
            # Bauteilbeschriftungen sind auf ihrem Ankerpunkt zentriert.
            out.append(Box(x - w / 2, y - h / 2, x + w / 2, y + h / 2, txt, "Bauteil"))

    return out


_TITLE = re.compile(r'^\t\t\(title "([^"]*)"')


def check_sheet(path: Path) -> list[str]:
    boxes = boxes_of(path)
    bad: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines()[:12]:
        if m := _TITLE.match(line):
            if hit := [c for c in TITLE_FORBIDDEN if c in m.group(1)]:
                bad.append(
                    f"Blatt-Titel enthaelt {', '.join(repr(c) for c in hit)} -- "
                    f"'kicad-cli sch export' baut daraus den Dateinamen und "
                    f"schreibt still eine leere Datei: {m.group(1)!r}")
            break

    for b in boxes:
        if b.x1 < MARGIN or b.y1 < MARGIN or b.x2 > SHEET_W - MARGIN or b.y2 > SHEET_H - MARGIN:
            bad.append(f"ausserhalb des Zeichenbereichs: {b}")
        elif b.x2 > TITLE_X and b.y2 > TITLE_Y:
            bad.append(f"im Titelblock (wird ueberdruckt): {b}")

    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if hit := a.collides(b):
                bad.append(f"ueberlagert ({hit[0]:.1f}x{hit[1]:.1f} mm): {a}  <->  {b}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="Sind die Schaltplaene lesbar?")
    ap.add_argument("--check", action="store_true", help="leise Ausgabe")
    args = ap.parse_args()

    sheets = sorted(REPO.glob("hardware/*/kicad/sheet_*.kicad_sch"))
    if not sheets:
        print("[UEBERSPRUNGEN] Noch keine erzeugten Schaltplaene.")
        return 0

    findings: dict[str, list[str]] = {}
    for sch in sheets:
        if bad := check_sheet(sch):
            findings[str(sch.relative_to(REPO))] = bad

    if findings:
        print("  [FEHLER] Unlesbare Stellen im Schaltplan:")
        for where, bad in findings.items():
            print(f"           {where}")
            for b in bad[:8]:
                print(f"             - {b}")
            if len(bad) > 8:
                print(f"             ... und {len(bad) - 8} weitere")
        print("           ERC prueft Elektrik, nicht Lesbarkeit -- ein Plan, den")
        print("           der Reviewer nicht lesen kann, erfuellt seinen Zweck nicht.")
        return 1

    total = sum(len(boxes_of(s)) for s in sheets)
    if args.check:
        print(f"Schaltplaene lesbar ({total} Beschriftungen, {len(sheets)} Sheets).")
    else:
        print("=" * 64)
        print(" ONE-X -- Lesbarkeit der Schaltplaene")
        print("=" * 64)
        print(f"  [OK] {total} Beschriftungen auf {len(sheets)} Sheets, "
              f"keine Ueberlagerung,")
        print("       nichts ausserhalb des Zeichenbereichs, nichts im Titelblock.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
