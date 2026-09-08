#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Generator fuer echte, ERC-pruefbare KiCad-Schaltplaene.

WAS DAS IST -- und was nicht:
Bis Session 24 gab es im Repo nur `hardware/*/kicad/` mit Projekt- und
Manifestdateien: eine Ableitung der Design-Specs, aber KEIN Schaltplan. Grund
war, dass ohne kicad-cli handgeschriebene .kicad_sch nicht ueberpruefbar sind
-- und eine unpruefbare Datei ist im Zweifel schlimmer als keine.

Mit installiertem KiCad faellt dieser Einwand weg: was hier erzeugt wird,
laeuft anschliessend durch `kicad-cli sch erc`. Ein Schaltplan, der ERC
besteht, ist ein echtes Engineering-Artefakt.

HOLD-DISZIPLIN BLEIBT:
Erzeugt werden nur Sheets, deren Netze und Bauteile in der Design-Spec bereits
feststehen. Sheets, die eine Hersteller-Pinbelegung brauchen (RK3576-Ball-Map,
LPDDR5-Topologie, UFS, FPGA), werden NICHT erzeugt -- eine erfundene Pinmap
waere genau der Fehler, den dieses Repo systematisch vermeidet.

Aufruf:
    python tools/gen_kicad_sch.py            # erzeugen
    python tools/gen_kicad_sch.py --check    # nur pruefen, nichts schreiben
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Deterministische UUIDs: derselbe Input ergibt dieselbe Datei, sonst schluege
# der Determinismus-Check der CI bei jedem Lauf an.
NS = uuid.UUID("6f1a5b0e-0000-4000-8000-onexonexone".replace("onexonexone", "0e1a5b0e1a5b"))


def uid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "/".join(parts)))


# --------------------------------------------------------------- Symbole
#
# Bewusst eigene, generische Symbole statt der KiCad-Standardbibliothek:
# Die Sheets sind Design-Specs, keine Bauteilauswahl. Ein generisches
# "Matching-Platz"-Symbol sagt ehrlicher, was gemeint ist, als ein konkreter
# Kondensator, dessen Wert noch TBD ist (Gate G09).

SYMBOLS = """
	(lib_symbols
		(symbol "ONEX:SMA"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016))
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
			(property "Value" "SMA" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "SMA_0_1"
				(rectangle (start -2.54 3.81) (end 2.54 -3.81)
					(stroke (width 0.254) (type default)) (fill (type none)))
				(circle (center 0 0) (radius 1.27)
					(stroke (width 0.254) (type default)) (fill (type none)))
			)
			(symbol "SMA_1_1"
				(pin passive line (at -7.62 0 0) (length 5.08)
					(name "RF" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
				(pin passive line (at 0 -7.62 90) (length 3.81)
					(name "SHIELD" (effects (font (size 1.27 1.27))))
					(number "2" (effects (font (size 1.27 1.27)))))
			)
		)
		(symbol "ONEX:MATCH"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016) (hide yes))
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "MP" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
			(property "Value" "TBD" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "MATCH_0_1"
				(rectangle (start -2.54 1.27) (end 2.54 -1.27)
					(stroke (width 0.254) (type dash)) (fill (type none)))
			)
			(symbol "MATCH_1_1"
				(pin passive line (at -5.08 0 0) (length 2.54)
					(name "A" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
				(pin passive line (at 5.08 0 180) (length 2.54)
					(name "B" (effects (font (size 1.27 1.27))))
					(number "2" (effects (font (size 1.27 1.27)))))
			)
		)
		(symbol "ONEX:ESD"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016) (hide yes))
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "D" (at 3.81 3.81 0) (effects (font (size 1.27 1.27))))
			(property "Value" "ESD" (at 3.81 -3.81 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "ESD_0_1"
				(polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 -1.27) (xy -1.27 1.27))
					(stroke (width 0.254) (type default)) (fill (type none)))
				(polyline (pts (xy -1.905 -1.27) (xy 1.905 -1.27))
					(stroke (width 0.254) (type default)) (fill (type none)))
			)
			(symbol "ESD_1_1"
				(pin passive line (at 0 5.08 270) (length 3.81)
					(name "A" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
				(pin passive line (at 0 -5.08 90) (length 3.81)
					(name "K" (effects (font (size 1.27 1.27))))
					(number "2" (effects (font (size 1.27 1.27)))))
			)
		)
		(symbol "ONEX:GND"
			(power)
			(pin_numbers (hide yes))
			(pin_names (offset 0) (hide yes))
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "GND_0_1"
				(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
					(stroke (width 0.254) (type default)) (fill (type none)))
			)
			(symbol "GND_1_1"
				(pin power_in line (at 0 0 90) (length 0) (hide yes)
					(name "GND" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
			)
		)
		(symbol "ONEX:PWR_FLAG"
			(power)
			(pin_numbers (hide yes))
			(pin_names (offset 0) (hide yes))
			(exclude_from_sim no)
			(in_bom no)
			(on_board yes)
			(property "Reference" "#FLG" (at 0 2.54 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Value" "PWR_FLAG" (at 0 4.572 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "PWR_FLAG_0_0"
				(pin power_out line (at 0 0 90) (length 0)
					(name "pwr" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
			)
			(symbol "PWR_FLAG_0_1"
				(polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27))
					(stroke (width 0.254) (type default)) (fill (type none)))
			)
		)
	)
"""


# KiCad-Verbindungsraster. Jede erzeugte Koordinate MUSS ein Vielfaches davon
# sein -- sonst meldet ERC "endpoint off grid" und Verbindungen greifen nicht
# zuverlaessig. Deshalb wird nicht in "schoenen" Zahlen wie 80 mm gerechnet,
# sondern in Rastereinheiten.
G = 1.27


def g(n: float) -> float:
    """n Rastereinheiten in mm."""
    return round(n * G, 2)


# x-Lage des Connector-Anschlusspunktes im Symbol (7 Raster vom Mittelpunkt).
CONN_PIN_X = g(7)


def conn_pin_offset(n_pins: int) -> float:
    """Y-Offset des obersten Pins im Symbol-Koordinatensystem."""
    return g(2.0) * (n_pins - 1) / 2.0


def conn_symbol(name: str, pins: list[tuple[str, str]]) -> str:
    """Erzeugt ein Connector-Symbol mit beliebig vielen passiven Pins."""
    top = conn_pin_offset(len(pins)) + g(2.0)
    body = [
        f'\t\t(symbol "ONEX:{name}"',
        '\t\t\t(pin_names (offset 1.016))',
        '\t\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)',
        f'\t\t\t(property "Reference" "J" (at 0 {top + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
        f'\t\t\t(property "Value" "{name}" (at 0 {-top - 2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
        '\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        '\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        '\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        f'\t\t\t(symbol "{name}_0_1"',
        f'\t\t\t\t(rectangle (start -3.81 {top:.2f}) (end 3.81 {-top:.2f})',
        '\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))',
        '\t\t\t)',
        f'\t\t\t(symbol "{name}_1_1"',
    ]
    # Anschlusspunkt liegt bei x = PIN_X; der Pin wird von dort nach links zum
    # Koerper gezeichnet (Winkel 180). Die Laenge gehoert NICHT auf die
    # Anschlusskoordinate addiert -- genau der Fehler, den ERC zuerst fand.
    y = conn_pin_offset(len(pins))
    for i, (pname, _net) in enumerate(pins, start=1):
        body.append(
            f'\t\t\t\t(pin passive line (at {CONN_PIN_X:.2f} {y:.2f} 180) (length {g(4):.2f})'
            f' (name "{pname}" (effects (font (size 1.27 1.27))))'
            f' (number "{i}" (effects (font (size 1.27 1.27)))))'
        )
        y -= g(2.0)
    body += ['\t\t\t)', '\t\t)']
    return "\n".join(body)


# ------------------------------------------------------------ Sheet-Bau

class Sheet:
    """Sammelt Symbole, Draehte und Labels und schreibt eine .kicad_sch."""

    def __init__(self, board: str, sheet: str, title: str, extra_symbols: str = ""):
        self.board = board
        self.sheet = sheet
        self.title = title
        self.extra_symbols = extra_symbols
        self.items: list[str] = []
        self.refs: dict[str, int] = {}

    def _ref(self, prefix: str) -> str:
        self.refs[prefix] = self.refs.get(prefix, 0) + 1
        return f"{prefix}{self.refs[prefix]}"

    def place(self, lib: str, x: float, y: float, ref: str, value: str,
              rot: int = 0, dnp: bool = False, fields: dict[str, str] | None = None) -> None:
        u = uid(self.board, self.sheet, "sym", ref)
        props = [
            f'\t\t(property "Reference" "{ref}" (at {x:.2f} {y - 6.35:.2f} 0)'
            f' (effects (font (size 1.27 1.27))))',
            f'\t\t(property "Value" "{value}" (at {x:.2f} {y + 6.35:.2f} 0)'
            f' (effects (font (size 1.27 1.27))))',
            f'\t\t(property "Footprint" "" (at {x:.2f} {y:.2f} 0)'
            f' (effects (font (size 1.27 1.27)) (hide yes)))',
        ]
        for k, v in (fields or {}).items():
            props.append(
                f'\t\t(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0)'
                f' (effects (font (size 1.27 1.27)) (hide yes)))'
            )
        hide_ref = ref.startswith("#")
        if hide_ref:
            props[0] = props[0][:-2] + ' (hide yes)))'
        self.items.append(
            f'\t(symbol\n'
            f'\t\t(lib_id "ONEX:{lib}")\n'
            f'\t\t(at {x:.2f} {y:.2f} {rot})\n'
            f'\t\t(unit 1)\n'
            f'\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)'
            f' (dnp {"yes" if dnp else "no"})\n'
            f'\t\t(uuid "{u}")\n'
            + "\n".join(props) + "\n"
            f'\t\t(instances\n'
            f'\t\t\t(project "{self.board}"\n'
            f'\t\t\t\t(path "/{uid(self.board, self.sheet, "root")}"\n'
            f'\t\t\t\t\t(reference "{ref}") (unit 1)\n'
            f'\t\t\t\t)\n'
            f'\t\t\t)\n'
            f'\t\t)\n'
            f'\t)'
        )

    def wire(self, x1: float, y1: float, x2: float, y2: float) -> None:
        u = uid(self.board, self.sheet, "w", f"{x1},{y1},{x2},{y2}")
        self.items.append(
            f'\t(wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))\n'
            f'\t\t(stroke (width 0) (type default)) (uuid "{u}"))'
        )

    def label(self, text: str, x: float, y: float, rot: int = 0) -> None:
        u = uid(self.board, self.sheet, "lbl", f"{text}@{x},{y}")
        self.items.append(
            f'\t(label "{text}" (at {x:.2f} {y:.2f} {rot})\n'
            f'\t\t(effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{u}"))'
        )

    def text(self, s: str, x: float, y: float, size: float = 1.27) -> None:
        u = uid(self.board, self.sheet, "txt", f"{s[:40]}@{x},{y}")
        esc = s.replace('"', "'")
        self.items.append(
            f'\t(text "{esc}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0)\n'
            f'\t\t(effects (font (size {size} {size})) (justify left bottom)) (uuid "{u}"))'
        )

    def render(self) -> str:
        return (
            '(kicad_sch\n'
            '\t(version 20250114)\n'
            '\t(generator "onex_gen_kicad_sch")\n'
            '\t(generator_version "10.0")\n'
            f'\t(uuid "{uid(self.board, self.sheet, "root")}")\n'
            '\t(paper "A3")\n'
            '\t(title_block\n'
            f'\t\t(title "{self.title}")\n'
            f'\t\t(company "G4MEOVER ONE-X")\n'
            f'\t\t(comment 1 "Erzeugt aus der Design-Spec durch tools/gen_kicad_sch.py")\n'
            f'\t\t(comment 2 "Nicht von Hand editieren -- Aenderungen gehen in die Spec")\n'
            '\t)\n'
            + SYMBOLS.rstrip()[:-1] + self.extra_symbols + "\n\t)\n"
            + "\n".join(self.items) + "\n"
            '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)\n'
            '\t(embedded_fonts no)\n'
            ')\n'
        )


# ------------------------------------- Antenna-Rail Sheet 01 (real)
#
# Quelle: hardware/antenna-rail/schematic/sheet_01_sma_feeds.md
# FIXED  : genau 4 SMA, 50 Ohm, Feeds kommen ueber J_ANT
# TBD    : Matching-/ESD-Werte und Band-Zuordnung je Port -> Gate G09
#          Deshalb sind alle Matching-Plaetze DNP und tragen "TBD".

def build_antenna_rail_sheet01() -> Sheet:
    board, sheet = "antenna-rail", "sheet_01_sma_feeds"
    feeds = ["ANT_1", "ANT_2", "ANT_3", "ANT_4"]

    conn_pins: list[tuple[str, str]] = []
    for f in feeds:
        conn_pins.append((f, f))
    conn_pins.append(("GND", "GND"))

    extra = "\n" + conn_symbol("J_ANT", conn_pins)
    s = Sheet(board, sheet, "ONE-X Antenna-Rail - Sheet 01 - SMA-Feeds / Matching / ESD", extra)

    # Verbinder zum Mainboard (J_ANT). Alle Koordinaten in Rastereinheiten.
    cx, cy = g(32), g(56)
    s.place("J_ANT", cx, cy, "J10", "J_ANT")

    # Symbol-Y waechst nach oben, Blatt-Y nach unten -> Vorzeichen dreht sich.
    top = conn_pin_offset(len(conn_pins))
    pin_x = cx + CONN_PIN_X

    for i, feed in enumerate(feeds):
        py = cy - top + g(2) * i
        row_y = g(28) + g(24) * i

        # Vom Connector-Pin ein Stueck nach rechts, dort das Netzlabel.
        s.wire(pin_x, py, pin_x + g(4), py)
        s.label(feed, pin_x + g(4), py)

        # --- Feed-Strecke: Label -> 3 Matching-Plaetze -> ESD -> SMA ---
        x = g(70)
        s.wire(x - g(6), row_y, x - g(4), row_y)
        s.label(feed, x - g(6), row_y)

        for _m in range(3):
            s.place("MATCH", x, row_y, s._ref("MP"), "TBD", dnp=True,
                    fields={"ONEX_Status": "TBD (G09)",
                            "ONEX_Note": "Matching auf realer HW tunen"})
            s.wire(x + g(4), row_y, x + g(8), row_y)
            x += g(12)

        # ESD-Diode gegen Masse, direkt am externen Port.
        esd_x = x - g(4)
        s.place("ESD", esd_x, row_y + g(8), s._ref("D"), "ESD", dnp=True,
                fields={"ONEX_Status": "TBD (G09)",
                        "ONEX_Note": "low-C, bandabhaengig"})
        s.wire(esd_x, row_y, esd_x, row_y + g(4))     # Feed -> ESD-Anode
        s.wire(esd_x, row_y + g(12), esd_x, row_y + g(14))
        s.place("GND", esd_x, row_y + g(14), f"#PWR0{i+1}", "GND")

        # SMA-Port.
        sma_x = esd_x + g(16)
        s.wire(esd_x, row_y, sma_x - g(6), row_y)
        s.place("SMA", sma_x, row_y, f"J{i+1}", "SMA",
                fields={"ONEX_Status": "FIXED (4x SMA)",
                        "ONEX_Note": "50 Ohm, Zuordnung TBD (G09)"})
        s.wire(sma_x, row_y + g(6), sma_x, row_y + g(8))
        s.place("GND", sma_x, row_y + g(8), f"#PWR1{i+1}", "GND")

    # Masse des Verbinders + ein Power-Flag, damit GND als getrieben gilt.
    #
    # Das Power-Flag geht bewusst nach RECHTS, nicht nach oben: oberhalb der
    # GND-Pinzeile liegt die Zeile des letzten Feeds. Ein Flag dort haette
    # seinen Draht durch dessen Label gezogen und GND mit einem Antennen-Feed
    # kurzgeschlossen -- im Bild unsichtbar, in der Netzliste fatal. ERC hat
    # genau das gemeldet ("GND und ANT_3 sind dasselbe Netz").
    gy = cy - top + g(2) * len(feeds)
    s.wire(pin_x, gy, pin_x + g(4), gy)
    s.wire(pin_x + g(4), gy, pin_x + g(4), gy + g(4))
    s.place("GND", pin_x + g(4), gy + g(4), "#PWR000", "GND")
    s.wire(pin_x + g(4), gy, pin_x + g(8), gy)
    s.place("PWR_FLAG", pin_x + g(8), gy, "#FLG01", "PWR_FLAG")

    # Statushinweise direkt im Blatt -- wer den Plan oeffnet, sieht die Grenzen.
    s.text("FIXED: genau 4x SMA, 50 Ohm (Master-Spec).", g(70), g(12), 2.0)
    s.text("TBD (Gate G09): Matching-/ESD-Werte und Band-Zuordnung je Port.", g(70), g(16))
    s.text("Alle Matching-/ESD-Plaetze sind DNP - Tuning auf realer Hardware.", g(70), g(19))
    return s


SHEETS = [
    ("antenna-rail", "sheet_01_sma_feeds", build_antenna_rail_sheet01),
]


# ------------------------------------------------------- Symbolbibliothek
#
# Die Symbole stecken zwar in jeder .kicad_sch (lib_symbols), aber ohne
# registrierte Bibliothek meldet ERC fuer JEDES Bauteil eine Warnung. Eine
# echte .kicad_sym plus sym-lib-table loest das -- und macht die Symbole in
# der KiCad-GUI wiederverwendbar, statt sie in generierten Dateien zu
# vergraben.

def render_symbol_lib(extra_defs: str) -> str:
    """Baut aus den eingebetteten Definitionen eine eigenstaendige Bibliothek."""
    body = SYMBOLS.strip()
    body = body[body.index("\n") + 1:body.rindex(")")]     # (lib_symbols ...) abstreifen
    body = (body + extra_defs).replace('(symbol "ONEX:', '(symbol "')
    # Eine Ebene Einrueckung zurueck, damit die Datei sauber aussieht.
    body = "\n".join(ln[1:] if ln.startswith("\t") else ln for ln in body.splitlines())
    return (
        '(kicad_symbol_lib\n'
        '\t(version 20241209)\n'
        '\t(generator "onex_gen_kicad_sch")\n'
        '\t(generator_version "10.0")\n'
        + body.rstrip() + "\n)\n"
    )


SYM_LIB_TABLE = (
    '(sym_lib_table\n'
    '\t(version 7)\n'
    '\t(lib (name "ONEX")(type "KiCad")'
    '(uri "${KIPRJMOD}/../../kicad/onex.kicad_sym")(options "")'
    '(descr "ONE-X generische Design-Spec-Symbole"))\n'
    ')\n'
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Erzeugt ERC-pruefbare KiCad-Schaltplaene")
    ap.add_argument("--check", action="store_true",
                    help="nur pruefen, ob die erzeugten Dateien aktuell sind")
    args = ap.parse_args()

    # (Pfad, Inhalt) -- alles, was dieser Generator besitzt.
    artifacts: list[tuple[Path, str]] = []

    extra_defs = ""
    for board, sheet, build in SHEETS:
        s = build()
        extra_defs += s.extra_symbols
        artifacts.append((REPO / "hardware" / board / "kicad" / f"{sheet}.kicad_sch",
                          s.render()))
        artifacts.append((REPO / "hardware" / board / "kicad" / "sym-lib-table",
                          SYM_LIB_TABLE))

    artifacts.append((REPO / "hardware" / "kicad" / "onex.kicad_sym",
                      render_symbol_lib(extra_defs)))

    changed, ok = [], True
    for path, content in artifacts:
        if args.check:
            if not path.is_file():
                print(f"  [FEHLT] {path.relative_to(REPO)}")
                ok = False
            elif path.read_text(encoding="utf-8") != content:
                print(f"  [VERALTET] {path.relative_to(REPO)}")
                ok = False
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                path.write_text(content, encoding="utf-8", newline="\n")
                changed.append(path.relative_to(REPO))

    if args.check:
        if ok:
            print(f"  [OK] {len(artifacts)} KiCad-Artefakt(e) aktuell.")
        return 0 if ok else 1

    print(f"Erzeugt/aktualisiert: {len(changed)} von {len(artifacts)} Artefakt(en)")
    for c in changed:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
