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
		(symbol "ONEX:R"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016) (hide yes))
			(exclude_from_sim no) (in_bom yes) (on_board yes)
			(property "Reference" "R" (at 2.54 1.27 0) (effects (font (size 1.27 1.27))))
			(property "Value" "R" (at 2.54 -1.27 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "R_0_1"
				(rectangle (start -1.016 2.54) (end 1.016 -2.54)
					(stroke (width 0.254) (type default)) (fill (type none)))
			)
			(symbol "R_1_1"
				(pin passive line (at 0 5.08 270) (length 2.54)
					(name "A" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
				(pin passive line (at 0 -5.08 90) (length 2.54)
					(name "B" (effects (font (size 1.27 1.27))))
					(number "2" (effects (font (size 1.27 1.27)))))
			)
		)
		(symbol "ONEX:C"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016) (hide yes))
			(exclude_from_sim no) (in_bom yes) (on_board yes)
			(property "Reference" "C" (at 2.54 1.27 0) (effects (font (size 1.27 1.27))))
			(property "Value" "C" (at 2.54 -2.54 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "C_0_1"
				(polyline (pts (xy -2.54 0.635) (xy 2.54 0.635))
					(stroke (width 0.508) (type default)) (fill (type none)))
				(polyline (pts (xy -2.54 -0.635) (xy 2.54 -0.635))
					(stroke (width 0.508) (type default)) (fill (type none)))
			)
			(symbol "C_1_1"
				(pin passive line (at 0 3.81 270) (length 3.175)
					(name "A" (effects (font (size 1.27 1.27))))
					(number "1" (effects (font (size 1.27 1.27)))))
				(pin passive line (at 0 -3.81 90) (length 3.175)
					(name "B" (effects (font (size 1.27 1.27))))
					(number "2" (effects (font (size 1.27 1.27)))))
			)
		)
		(symbol "ONEX:AND2"
			(pin_names (offset 0.254))
			(exclude_from_sim no) (in_bom yes) (on_board yes)
			(property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
			(property "Value" "AND2" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "AND2_0_1"
				(rectangle (start -3.81 3.81) (end 3.81 -3.81)
					(stroke (width 0.254) (type default)) (fill (type background)))
				(text "&" (at 0 0 0) (effects (font (size 1.778 1.778))))
			)
			(symbol "AND2_1_1"
				(pin input line (at -7.62 2.54 0) (length 3.81)
					(name "A" (effects (font (size 1.016 1.016))))
					(number "1" (effects (font (size 1.016 1.016)))))
				(pin input line (at -7.62 -2.54 0) (length 3.81)
					(name "B" (effects (font (size 1.016 1.016))))
					(number "2" (effects (font (size 1.016 1.016)))))
				(pin output line (at 7.62 0 180) (length 3.81)
					(name "Y" (effects (font (size 1.016 1.016))))
					(number "3" (effects (font (size 1.016 1.016)))))
			)
		)
		(symbol "ONEX:SW"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016) (hide yes))
			(exclude_from_sim no) (in_bom yes) (on_board yes)
			(property "Reference" "SW" (at 0 4.445 0) (effects (font (size 1.016 1.016))))
			(property "Value" "SW" (at 0 -4.445 0) (effects (font (size 1.016 1.016))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "SW_0_1"
				(circle (center 0 2.032) (radius 0.508)
					(stroke (width 0.2032) (type default)) (fill (type none)))
				(circle (center 0 -2.032) (radius 0.508)
					(stroke (width 0.2032) (type default)) (fill (type none)))
				(polyline (pts (xy -0.508 -1.524) (xy 1.778 2.286))
					(stroke (width 0.2032) (type default)) (fill (type none)))
			)
			(symbol "SW_1_1"
				(pin passive line (at 0 5.08 270) (length 2.54)
					(name "A" (effects (font (size 1.016 1.016))))
					(number "1" (effects (font (size 1.016 1.016)))))
				(pin passive line (at 0 -5.08 90) (length 2.54)
					(name "B" (effects (font (size 1.016 1.016))))
					(number "2" (effects (font (size 1.016 1.016)))))
			)
		)
		(symbol "ONEX:LED"
			(pin_numbers (hide yes))
			(pin_names (offset 1.016) (hide yes))
			(exclude_from_sim no) (in_bom yes) (on_board yes)
			(property "Reference" "D" (at 3.175 1.905 0) (effects (font (size 1.016 1.016))))
			(property "Value" "LED" (at 3.175 -1.905 0) (effects (font (size 1.016 1.016))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "LED_0_1"
				(polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 -1.27) (xy -1.27 1.27))
					(stroke (width 0.2032) (type default)) (fill (type none)))
				(polyline (pts (xy -1.905 -1.27) (xy 1.905 -1.27))
					(stroke (width 0.2032) (type default)) (fill (type none)))
				(polyline (pts (xy 1.27 1.905) (xy 2.286 2.921))
					(stroke (width 0.1524) (type default)) (fill (type none)))
			)
			(symbol "LED_1_1"
				(pin passive line (at 0 5.08 270) (length 3.81)
					(name "A" (effects (font (size 1.016 1.016))))
					(number "1" (effects (font (size 1.016 1.016)))))
				(pin passive line (at 0 -5.08 90) (length 3.81)
					(name "K" (effects (font (size 1.016 1.016))))
					(number "2" (effects (font (size 1.016 1.016)))))
			)
		)
		(symbol "ONEX:TP"
			(pin_numbers (hide yes))
			(pin_names (offset 0) (hide yes))
			(exclude_from_sim no) (in_bom yes) (on_board yes)
			(property "Reference" "TP" (at 0 -3.81 0) (effects (font (size 1.016 1.016))))
			(property "Value" "TP" (at 0 3.81 0) (effects (font (size 1.016 1.016))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "TP_0_1"
				(circle (center 0 1.905) (radius 0.635)
					(stroke (width 0.254) (type default)) (fill (type none)))
			)
			(symbol "TP_1_1"
				(pin passive line (at 0 0 90) (length 1.27)
					(name "tp" (effects (font (size 1.016 1.016))))
					(number "1" (effects (font (size 1.016 1.016)))))
			)
		)
		(symbol "ONEX:SRC"
			(pin_numbers (hide yes))
			(pin_names (offset 0) (hide yes))
			(exclude_from_sim no) (in_bom no) (on_board yes)
			(property "Reference" "#SRC" (at 0 3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Value" "SRC" (at 0 5.588 0) (effects (font (size 1.016 1.016))))
			(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
			(symbol "SRC_0_1"
				(polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 1.27 3.81) (xy -1.27 3.81) (xy -1.27 1.27))
					(stroke (width 0.254) (type dash)) (fill (type none)))
			)
			(symbol "SRC_1_1"
				(pin output line (at 0 0 90) (length 1.27)
					(name "src" (effects (font (size 1.016 1.016))))
					(number "1" (effects (font (size 1.016 1.016)))))
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

# Board-weite Buchhaltung der Power-Flags.
#
# Ein Power-Flag sagt ERC: "dieses Netz wird gespeist". Pro Netz darf es genau
# EINES geben. Solange jedes Blatt einzeln geprueft wurde, brauchte auch jedes
# Blatt sein eigenes Flag -- im Board-Kontext sind das dann zwei Treiber auf
# demselben Netz, und ERC meldet zu Recht einen Konflikt (pin_to_pin).
# Deshalb wird je Board und Netz nur das erste Flag gesetzt.
_POWER_FLAGS: set[tuple[str, str]] = set()


def claim_power_flag(board: str, net: str) -> bool:
    """True, wenn dieses Blatt das Flag fuer (board, net) setzen darf."""
    key = (board, net)
    if key in _POWER_FLAGS:
        return False
    _POWER_FLAGS.add(key)
    return True


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
            # Instanzpfad im BOARD-Kontext: /<board-root>/<blatt-instanz>.
            # Ein Blatt wird nicht fuer sich betrachtet, sondern als Teil
            # seines Boards -- nur so verbinden sich globale Labels ueber
            # Blattgrenzen hinweg und ERC prueft das Board als Ganzes.
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

    def glabel(self, text: str, x: float, y: float, shape: str = "bidirectional",
               rot: int = 0) -> None:
        """
        Blattuebergreifendes Netz. Lokale Labels enden am Blattrand -- ERC
        meldet solche Netze zu Recht als isoliert. Signale, die andere Sheets
        erreichen (PA_EN_*, TX_GATE_OK ...), muessen global sein.
        """
        u = uid(self.board, self.sheet, "glbl", f"{text}@{x},{y}")
        self.items.append(
            f'\t(global_label "{text}"\n'
            f'\t\t(shape {shape})\n'
            f'\t\t(at {x:.2f} {y:.2f} {rot})\n'
            f'\t\t(effects (font (size 1.27 1.27)) (justify left))\n'
            f'\t\t(uuid "{u}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:.2f} {y:.2f} 0)\n'
            f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'\t)'
        )

    def source(self, x: float, y: float, note: str) -> None:
        """
        Markiert einen Eingang, der von einem ANDEREN Blatt getrieben wird.
        Ohne diese Quelle meldet ERC "Input pin not driven" -- zu Recht, denn
        aus dem Blatt allein ist nicht ersichtlich, ob das Signal je entsteht.
        Den Pin stattdessen auf 'passive' zu setzen wuerde die Pruefung nur
        stumm schalten, statt die Herkunft zu benennen.
        """
        self.place("SRC", x, y, self._ref("#SRC"), note)

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
    if claim_power_flag(board, "GND"):
        s.wire(pin_x + g(4), gy, pin_x + g(8), gy)
        s.place("PWR_FLAG", pin_x + g(8), gy, "#FLG01", "PWR_FLAG")

    # Statushinweise direkt im Blatt -- wer den Plan oeffnet, sieht die Grenzen.
    s.text("FIXED: genau 4x SMA, 50 Ohm (Master-Spec).", g(70), g(12), 2.0)
    s.text("TBD (Gate G09): Matching-/ESD-Werte und Band-Zuordnung je Port.", g(70), g(16))
    s.text("Alle Matching-/ESD-Plaetze sind DNP - Tuning auf realer Hardware.", g(70), g(19))
    return s


# ------------------------------------- M.2-Bridge Sheet 01 (real)
#
# Quelle: hardware/m2-bridge/schematic/sheet_01_pcie_usb3.md
# Netznamen: hardware/INTERFACE_NETS.md (kanonisch, nicht neu erfunden)
# FIXED  : PCIe 2.1 x1 + USB3 als Diff-Paare; AC-Kopplung im TX-Pfad
# TBD    : AC-Kondensatorwerte (G08), RefClk-Modus (G04)

def build_m2_bridge_sheet01() -> Sheet:
    board, sheet = "m2-bridge", "sheet_01_pcie_usb3"

    # (Netzbasis, AC-gekoppelt?, Kommentar) -- Reihenfolge = Blattreihenfolge.
    pairs = [
        ("PCIE_TX",     True,  "Host -> EP, AC-gekoppelt (Sender-Ende)"),
        ("PCIE_RX",     False, "EP -> Host"),
        ("PCIE_REFCLK", False, "100 MHz, Modus TBD (G04)"),
        ("USB3_M2_TX",  True,  "SuperSpeed TX, AC-gekoppelt"),
        ("USB3_M2_RX",  False, "SuperSpeed RX"),
        ("USB2_M2_D",   False, "USB2 Fallback/Sideband"),
    ]

    host_pins: list[tuple[str, str]] = []
    for base, _ac, _c in pairs:
        host_pins.append((base + "_P", base + "_P"))
        host_pins.append((base + "_N", base + "_N"))
    host_pins.append(("GND", "GND"))

    ep_pins = [(p, p) for p, _ in host_pins]

    extra = "\n" + conn_symbol("J_M2_HOST", host_pins)
    extra += "\n" + conn_symbol("M2_BKEY", ep_pins)
    s = Sheet(board, sheet, "ONE-X M.2-Bridge - Sheet 01 - PCIe 2.1 x1 / USB3", extra)

    # Links der Verbinder zum Mainboard, rechts der M.2-B-Key zum HyperRF.
    hx, hy = g(24), g(60)
    s.place("J_M2_HOST", hx, hy, "J20", "J_M2 (Mainboard)")
    ex, ey = g(104), g(60)
    s.place("M2_BKEY", ex, ey, "J21", "M.2 B-Key (HyperRF)")

    htop = conn_pin_offset(len(host_pins))
    hpin_x = hx + CONN_PIN_X
    epin_x = ex + CONN_PIN_X

    for idx, (base, ac, note) in enumerate(pairs):
        for half, suffix in enumerate(("_P", "_N")):
            net = base + suffix
            i = idx * 2 + half
            py = hy - htop + g(2) * i
            row_y = g(20) + g(6) * i

            # Host-Seite: Pin -> Label.
            s.wire(hpin_x, py, hpin_x + g(4), py)
            s.label(net, hpin_x + g(4), py)

            # Strecke in der Blattmitte.
            #
            # Nur wo ein Serien-C sitzt, entstehen WIRKLICH zwei Netze
            # (Host-Seite und M.2-Seite). Ohne C ist es durchgehend ein Netz --
            # es dann trotzdem umzubenennen erzeugt zwei Namen fuer dieselbe
            # Verbindung; ERC meldet das als "multiple_net_names", und in der
            # Netzliste waere es schlicht falsch.
            x0 = g(50)
            ep_net = net + "_M2" if ac else net
            if ac:
                # Nur hier gibt es ueberhaupt eine Strecke in der Blattmitte.
                # Ohne C haengt ein Label dort frei in der Luft.
                #
                # Der C ist um 90 Grad gedreht; seine Anschlusspunkte liegen
                # dann bei +/- 3.81 mm (= 3 Raster) neben der Platzierung, NICHT
                # am Symbolrand. Die Draehte muessen genau dort enden.
                cx_ = x0 + g(4)
                s.label(net, x0, row_y)
                s.wire(x0, row_y, cx_ - g(3), row_y)
                s.place("C", cx_, row_y, s._ref("C"), "TBD", rot=90,
                        fields={"ONEX_Status": "Wert TBD (G08)",
                                "ONEX_Note": "AC-Kopplung, bestueckt (kein DNP)"})
                s.wire(cx_ + g(3), row_y, x0 + g(12), row_y)
                s.label(ep_net, x0 + g(12), row_y)

            # Endpoint-Seite.
            epy = ey - htop + g(2) * i
            s.wire(epin_x, epy, epin_x + g(4), epy)
            s.label(ep_net, epin_x + g(4), epy)

    # Masse beidseitig + ein Power-Flag.
    for cx_, cy_, tag in ((hpin_x, hy, "H"), (epin_x, ey, "E")):
        gy = cy_ - htop + g(2) * (len(host_pins) - 1)
        s.wire(cx_, gy, cx_ + g(4), gy)
        s.wire(cx_ + g(4), gy, cx_ + g(4), gy + g(4))
        s.place("GND", cx_ + g(4), gy + g(4), f"#PWR{tag}0", "GND")
    gy = hy - htop + g(2) * (len(host_pins) - 1)
    if claim_power_flag(board, "GND"):
        s.wire(hpin_x + g(4), gy, hpin_x + g(8), gy)
        s.place("PWR_FLAG", hpin_x + g(8), gy, "#FLG01", "PWR_FLAG")

    s.text("FIXED: PCIe 2.1 x1 (kein Gen3 x4) + USB3. Diff-Paare, ein Treiber je Richtung.",
           g(20), g(10), 2.0)
    s.text("TBD: AC-Kondensatorwerte (SI-Review G08) - Bauteile sind bestueckt, nur der Wert offen.",
           g(20), g(14))
    s.text("TBD: PCIe-RefClk-Modus Common-Clock oder SRIS (haengt am FPGA-Endpoint, G04).",
           g(20), g(17))
    return s


# ------------------------------------- RF-Core Sheet 01 (real)
#
# Quelle: hardware/rf-core/schematic/sheet_01_supervisor_rfkill.md
# Das sicherheitskritischste Sheet des Geraets: der HW-erzwungene
# TX-Disable-Pfad. Regel 2 dort: "auch ein haengender RP2350 laesst den Pfad
# im sicheren Zustand" -- deshalb Pull-Downs Richtung Kill an jedem Enable.

def build_rf_core_sheet01() -> Sheet:
    board, sheet = "rf-core", "sheet_01_supervisor_rfkill"

    radios = [
        ("CC1101",   "Sub-GHz"),
        ("SX1262",   "Sub-GHz LoRa"),
        ("CC2652P7", "2,4 GHz"),
        ("ZG23",     "Z-Wave"),
        ("E710",     "UHF RAIN"),
        ("LFRFID",   "LF-RFID TX-Feld"),
        ("IRTX",     "IR-TX"),
    ]

    sup_pins = [("RF_KILL", "RF_KILL"),
                ("RF_KILL_SW_n", "RF_KILL_SW_n"),
                ("TX_GATE_OK", "TX_GATE_OK"),
                ("GND", "GND")]
    extra = "\n" + conn_symbol("J_SUP", sup_pins)
    s = Sheet(board, sheet,
              "ONE-X RF-Core - Sheet 01 - Supervisor / RF-Kill (sicherheitskritisch)", extra)

    # Eingaenge vom RP2350 und vom physischen Notfallschalter.
    cx, cy = g(20), g(28)
    s.place("J_SUP", cx, cy, "J30", "J_RFCORE (Supervisor)")
    top = conn_pin_offset(len(sup_pins))
    pin_x = cx + CONN_PIN_X
    # RF_KILL und RF_KILL_SW_n kommen von aussen (RP2350 bzw. Notfallschalter),
    # TX_GATE_OK geht zurueck. Alle drei verlassen das Blatt -> global.
    for i, (name, _n) in enumerate(sup_pins[:3]):
        py = cy - top + g(2) * i
        s.wire(pin_x, py, pin_x + g(4), py)
        s.glabel(name, pin_x + g(4), py)

    # Masse des Supervisor-Verbinders.
    gy = cy - top + g(2) * 3
    s.wire(pin_x, gy, pin_x + g(4), gy)
    s.wire(pin_x + g(4), gy, pin_x + g(4), gy + g(4))
    s.place("GND", pin_x + g(4), gy + g(4), "#PWR00", "GND")
    if claim_power_flag(board, "GND"):
        s.wire(pin_x + g(4), gy, pin_x + g(8), gy)
        s.place("PWR_FLAG", pin_x + g(8), gy, "#FLG01", "PWR_FLAG")

    # Gemeinsames Gate: RF_KILL UND RF_KILL_SW_n. Beide muessen freigeben.
    # Die beiden Eingaenge werden von aussen getrieben -> je eine benannte
    # Quelle, damit ERC den Pfad als versorgt erkennt.
    gate_x, gate_y = g(48), g(24)
    for dy, src_note in ((-g(2), "RP2350"), (g(2), "Notfallschalter")):
        y = gate_y + dy
        # Anschlusspunkt der Quelle liegt auf ihrer Platzierung -> genau auf
        # den Draht setzen, sonst haengt sie daneben (ERC: "not driven").
        s.source(gate_x - g(14), y, src_note)
        s.wire(gate_x - g(14), y, gate_x - g(6), y)
    s.glabel("RF_KILL", gate_x - g(12), gate_y - g(2))
    s.glabel("RF_KILL_SW_n", gate_x - g(12), gate_y + g(2))

    s.place("AND2", gate_x, gate_y, "U30", "TX_GATE",
            fields={"ONEX_Status": "FIXED (fail-safe)",
                    "ONEX_Note": "Diskrete Logik, kein reiner MCU-GPIO"})
    # Der Gate-Ausgang traegt den kanonischen Namen TX_GATE_OK
    # (hardware/INTERFACE_NETS.md). Bewusst KEIN zweiter Name wie "TX_PERMIT"
    # daneben: es ist ein und derselbe Knoten, und zwei Namen fuer ein Netz
    # sind in der Netzliste schlicht falsch (ERC: multiple_net_names).
    #
    # Dass die Rueckmeldung an den RP2350 exakt das Signal ist, welches die
    # PAs freigibt, ist die erwuenschte Eigenschaft: die Firmware vergleicht
    # ihren Befehl dagegen und latcht bei Abweichung einen Fault
    # (onex_rfkill.c). Ein Abgriff VOR dem Gate waere derselbe Wert wie der
    # Befehl -- der Vergleich pruefte sich selbst.
    s.wire(gate_x + g(6), gate_y, gate_x + g(10), gate_y)
    s.wire(gate_x + g(10), gate_y, gate_x + g(10), gate_y + g(6))
    s.wire(gate_x + g(10), gate_y + g(6), gate_x + g(4), gate_y + g(6))
    s.glabel("TX_GATE_OK", gate_x + g(4), gate_y + g(6))

    # Je Radio: eigenes Gate aus TX_PERMIT, mit Pull-Down Richtung Kill.
    for i, (radio, band) in enumerate(radios):
        ry = g(40) + g(14) * i

        # Freigabe aus dem Supervisor-Gate (U30) dieses Blattes.
        s.glabel("TX_GATE_OK", g(40), ry - g(2))
        s.wire(g(40), ry - g(2), g(44), ry - g(2))

        # Die Sendeanforderung kommt vom jeweiligen Radio-Chip auf einem
        # anderen Sheet (02-06) -- global plus benannte Quelle, exakt auf
        # dem Draht platziert.
        s.source(g(36), ry + g(2), f"{radio} (Sheet 02-06)")
        s.wire(g(36), ry + g(2), g(44), ry + g(2))
        s.glabel(f"TXREQ_{radio}", g(38), ry + g(2))

        s.place("AND2", g(50), ry, s._ref("U"), f"PA_GATE_{radio}",
                fields={"ONEX_Status": "FIXED",
                        "ONEX_Note": f"{band} - PA-Enable nur ueber dieses Gate"})
        s.wire(g(56), ry, g(62), ry)

        # Pull-Down: ohne aktives Treiben bleibt das Enable auf Kill.
        s.place("R", g(62), ry + g(6), s._ref("R"), "100k",
                fields={"ONEX_Status": "FIXED (fail-safe)",
                        "ONEX_Note": "Pull Richtung Kill - Default TX gesperrt"})
        s.wire(g(62), ry, g(62), ry + g(2))
        s.wire(g(62), ry + g(10), g(62), ry + g(12))
        s.place("GND", g(62), ry + g(12), f"#PWR{i+1:02d}", "GND")

        # Das Enable verlaesst das Blatt Richtung Radio -> global.
        s.wire(g(62), ry, g(70), ry)
        s.glabel(f"PA_EN_{radio}", g(70), ry)

    s.text("REGEL: Jedes PA/TX-Enable laeuft ueber dieses Gate. Kein verdeckter TX-Pfad.",
           g(20), g(12), 2.0)
    s.text("Default nach Boot/Reset/Fault = Kill aktiv. Pull-Downs ziehen jedes Enable Richtung Kill,",
           g(20), g(16))
    s.text("auch wenn der RP2350 haengt (sheet_01_supervisor_rfkill.md, Regel 2).", g(20), g(19))
    s.text("TX_GATE_OK wird HINTER der Gate-Logik abgegriffen und an den RP2350 zurueckgemeldet.",
           g(20), g(22))
    s.text("Die Firmware vergleicht ihn gegen den Befehl und latcht bei Abweichung einen Fault",
           g(20), g(25))
    s.text("(onex_rfkill.c). Ein Abgriff VOR dem Gate waere derselbe Wert wie der Befehl -",
           g(20), g(28))
    s.text("der Vergleich pruefte sich selbst. Endgueltige Sense-Stelle hinter den PA-Enables: TBD.",
           g(20), g(31))
    return s


# ------------------------------------- M.2-Bridge Sheet 02 (real)
#
# Quelle: hardware/m2-bridge/schematic/sheet_02_sideband_power.md
#
# NAMENS-PRAEZISIERUNG: Das Sheet nannte die Logik-Rail "+3V3". Der Power-Tree
# (mainboard sheet_01) fuehrt genau diese Rail als "+3V3_SYS" ("Logik, Radios,
# M.2"). Es ist dieselbe Rail -- hier wird der kanonische Name verwendet, und
# die Markdown-Spec wurde nachgezogen. Zwei Namen fuer eine Rail waeren beim
# Zusammenfuehren der Boards ein Fehler.

def build_m2_bridge_sheet02() -> Sheet:
    board, sheet = "m2-bridge", "sheet_02_sideband_power"

    sideband = [
        ("PCIE_PERST_n",  "Reset vom Host an den Endpoint"),
        ("PCIE_CLKREQ_n", "Clock-Request (Richtung je Modus, G04)"),
        ("PCIE_WAKE_n",   "Wake vom Endpoint an den Host"),
    ]
    rails = [
        ("+3V3_SYS",       "M.2-Logik/Referenz"),
        ("HYPERRF_AUX_5V", "Durchfuehrung bis 5 A - Pinbudget TBD"),
    ]

    host_pins = [(n, n) for n, _ in sideband] + [(n, n) for n, _ in rails] + [("GND", "GND")]
    extra = "\n" + conn_symbol("J_M2_SB", host_pins)
    extra += "\n" + conn_symbol("M2_BKEY_SB", [(p, p) for p, _ in host_pins])
    s = Sheet(board, sheet, "ONE-X M.2-Bridge - Sheet 02 - Sideband / Power / Testpunkte", extra)

    hx, hy = g(24), g(48)
    ex, ey = g(96), g(48)
    s.place("J_M2_SB", hx, hy, "J22", "J_M2 (Sideband)")
    s.place("M2_BKEY_SB", ex, ey, "J23", "M.2 B-Key (Sideband)")

    top = conn_pin_offset(len(host_pins))
    hpin_x, epin_x = hx + CONN_PIN_X, ex + CONN_PIN_X

    all_nets = [n for n, _ in sideband] + [n for n, _ in rails]
    for i, net in enumerate(all_nets):
        py = hy - top + g(2) * i
        s.wire(hpin_x, py, hpin_x + g(4), py)
        s.glabel(net, hpin_x + g(4), py)
        epy = ey - top + g(2) * i
        s.wire(epin_x, epy, epin_x + g(4), epy)
        s.glabel(net, epin_x + g(4), epy)

    # Masse beidseitig, ein Power-Flag.
    for cxx, cyy, tag in ((hpin_x, hy, "H"), (epin_x, ey, "E")):
        gy = cyy - top + g(2) * len(all_nets)
        s.wire(cxx, gy, cxx + g(4), gy)
        s.wire(cxx + g(4), gy, cxx + g(4), gy + g(4))
        s.place("GND", cxx + g(4), gy + g(4), f"#PWR{tag}0", "GND")
    gy = hy - top + g(2) * len(all_nets)
    if claim_power_flag(board, "GND"):
        s.wire(hpin_x + g(4), gy, hpin_x + g(8), gy)
        s.place("PWR_FLAG", hpin_x + g(8), gy, "#FLG02", "PWR_FLAG")

    # Testpunkte fuer den gestaffelten Bring-up (Sheet 02: "messbar").
    # Jeder haengt an einem Netz, das auch anderswo verwendet wird.
    for i, (net, _why) in enumerate(sideband + rails):
        tx, ty = g(52), g(20) + g(6) * i
        s.glabel(net, tx, ty)
        s.wire(tx, ty, tx + g(4), ty)
        s.place("TP", tx + g(4), ty, s._ref("TP"), f"TP_{net}",
                fields={"ONEX_Note": "Bring-up-Messpunkt"})

    # Entkopplung nahe dem Endpoint (Sheet 02: "Entkopplung an +3V3 nahe EP").
    dx, dy = g(80), g(20)
    s.glabel("+3V3_SYS", dx, dy)
    s.wire(dx, dy, dx, dy + g(3))
    s.place("C", dx, dy + g(6), s._ref("C"), "100n",
            fields={"ONEX_Status": "TARGET",
                    "ONEX_Note": "Entkopplung nahe Endpoint"})
    s.wire(dx, dy + g(9), dx, dy + g(11))
    s.place("GND", dx, dy + g(11), "#PWR20", "GND")

    # Rails brauchen einen deklarierten Treiber, sonst gelten sie als
    # ungespeist -- sie kommen physisch vom Mainboard.
    for i, (net, _why) in enumerate(rails):
        fx, fy = g(88), g(38) + g(6) * i
        s.glabel(net, fx, fy)
        if claim_power_flag(board, net):
            s.wire(fx, fy, fx + g(4), fy)
            s.place("PWR_FLAG", fx + g(4), fy, f"#FLG1{i}", "PWR_FLAG")

    s.text("Power-vor-Reset: +3V3_SYS und HYPERRF_AUX_5V stabil, DANN PCIE_PERST_n freigeben.",
           g(18), g(10), 2.0)
    s.text("Rail heisst kanonisch +3V3_SYS (Power-Tree), nicht '+3V3' - zwei Namen fuer eine",
           g(18), g(14))
    s.text("Rail waeren beim Zusammenfuehren der Boards ein Fehler.", g(18), g(17))
    s.text("TBD: Kontakt-/Strombudget fuer HYPERRF_AUX_5V (bis 5 A) - Layout-Review G08.",
           g(18), g(56))
    return s


# ------------------------------------- UI-Carrier Sheet 01 (real)
#
# Quelle: hardware/ui-carrier/schematic/sheet_01_display_dsi.md
# FIXED  : 4-Lane-DSI + Takt, LCD_RST_n, BL_EN/BL_PWM, VLCD_3V3
# TBD    : DSI-Init/Timings, Backlight-String V/I, Panel-MPN -> Gate G01
#
# Der RK3576 taucht hier NICHT als Symbol auf: seine Ball-Map ist HOLD. Die
# Signale kommen als Durchfuehrung ueber J_UI/J_DSI -- genau so, wie es die
# Design-Spec beschreibt. Damit bleibt das Blatt pinmap-frei.

def build_ui_carrier_sheet01() -> Sheet:
    board, sheet = "ui-carrier", "sheet_01_display_dsi"

    lanes = ["DSI0_CLK", "DSI0_D0", "DSI0_D1", "DSI0_D2", "DSI0_D3"]
    control = ["LCD_RST_n", "BL_EN", "BL_PWM", "TP_INT", "TP_RST"]

    ui_pins: list[tuple[str, str]] = []
    for base in lanes:
        ui_pins.append((base + "_P", base + "_P"))
        ui_pins.append((base + "_N", base + "_N"))
    ui_pins += [(c, c) for c in control]
    ui_pins.append(("VLCD_3V3", "VLCD_3V3"))
    ui_pins.append(("GND", "GND"))

    # Panel-FPC fuehrt dieselben Signale plus die Backlight-Rail.
    fpc_pins = [(p, p) for p, _ in ui_pins if p != "GND"]
    fpc_pins.append(("VBL", "VBL"))
    fpc_pins.append(("GND", "GND"))

    extra = "\n" + conn_symbol("J_UI_DSI", ui_pins)
    extra += "\n" + conn_symbol("J_PANEL_FPC", fpc_pins)
    s = Sheet(board, sheet, "ONE-X UI-Carrier - Sheet 01 - Display / MIPI-DSI", extra)

    ux, uy = g(24), g(64)
    px, py0 = g(88), g(64)
    s.place("J_UI_DSI", ux, uy, "J40", "J_UI / J_DSI")
    s.place("J_PANEL_FPC", px, py0, "J41", "Panel-FPC")

    utop = conn_pin_offset(len(ui_pins))
    ftop = conn_pin_offset(len(fpc_pins))
    upin_x, fpin_x = ux + CONN_PIN_X, px + CONN_PIN_X

    # DSI-Paare und Steuersignale queren unveraendert -- ein durchgehendes
    # Netz je Signal, kein Umbenennen auf der Panelseite.
    signal_names = [p for p, _ in ui_pins if p != "GND"]
    for i, net in enumerate(signal_names):
        s.wire(upin_x, uy - utop + g(2) * i, upin_x + g(4), uy - utop + g(2) * i)
        s.glabel(net, upin_x + g(4), uy - utop + g(2) * i)
        s.wire(fpin_x, py0 - ftop + g(2) * i, fpin_x + g(4), py0 - ftop + g(2) * i)
        s.glabel(net, fpin_x + g(4), py0 - ftop + g(2) * i)

    # Masse beidseitig.
    for cxx, cyy, top_, tag in ((upin_x, uy, utop, "U"), (fpin_x, py0, ftop, "F")):
        n = len(ui_pins) - 1 if tag == "U" else len(fpc_pins) - 1
        gy = cyy - top_ + g(2) * n
        s.wire(cxx, gy, cxx + g(4), gy)
        s.wire(cxx + g(4), gy, cxx + g(4), gy + g(4))
        s.place("GND", cxx + g(4), gy + g(4), f"#PWR{tag}0", "GND")
    gy = uy - utop + g(2) * (len(ui_pins) - 1)
    if claim_power_flag(board, "GND"):
        s.wire(upin_x + g(4), gy, upin_x + g(8), gy)
        s.place("PWR_FLAG", upin_x + g(8), gy, "#FLG40", "PWR_FLAG")

    # Panel-Rail kommt vom Mainboard -> deklarierter Treiber.
    s.glabel("VLCD_3V3", g(52), g(16))
    if claim_power_flag(board, "VLCD_3V3"):
        s.wire(g(52), g(16), g(56), g(16))
        s.place("PWR_FLAG", g(56), g(16), "#FLG41", "PWR_FLAG")

    # Backlight-Boost: erzeugt VBL aus VLCD_3V3, gesteuert ueber BL_EN/BL_PWM.
    # String-Spannung/-Strom sind panelabhaengig und bleiben TBD (G01).
    bx, by = g(56), g(30)
    s.glabel("BL_EN", bx - g(12), by - g(2))
    s.wire(bx - g(12), by - g(2), bx - g(6), by - g(2))
    s.glabel("BL_PWM", bx - g(12), by + g(2))
    s.wire(bx - g(12), by + g(2), bx - g(6), by + g(2))
    s.place("AND2", bx, by, "U40", "BL_BOOST",
            fields={"ONEX_Status": "TARGET",
                    "ONEX_Note": "LED-Boost, String V/I TBD (G01)"})
    # VBL ist BOARD-LOKAL: der Boost erzeugt es hier, der Panel-FPC verbraucht
    # es hier. Es quert keinen Inter-Board-Verbinder -- also ein lokales Label,
    # kein globales. (Als global wuerde es zu Recht im Woerterbuch fehlen.)
    s.wire(bx + g(6), by, bx + g(10), by)
    s.label("VBL", bx + g(10), by)

    # ... und am Panel-FPC ankommen. Ohne diesen Anschluss haengt der
    # Backlight-Pin in der Luft (ERC: pin_not_connected).
    vbl_y = py0 - ftop + g(2) * len(signal_names)
    s.wire(fpin_x, vbl_y, fpin_x + g(4), vbl_y)
    s.label("VBL", fpin_x + g(4), vbl_y)

    # Entkopplung der Panel-Rail nahe dem FPC.
    s.glabel("VLCD_3V3", g(72), g(20))
    s.wire(g(72), g(20), g(72), g(23))
    s.place("C", g(72), g(26), s._ref("C"), "100n",
            fields={"ONEX_Status": "TARGET", "ONEX_Note": "nahe FPC"})
    s.wire(g(72), g(29), g(72), g(31))
    s.place("GND", g(72), g(31), "#PWR41", "GND")

    s.text("FIXED: 4 Datenlanes + Takt, LCD_RST_n, BL_EN/BL_PWM, VLCD_3V3.", g(18), g(8), 2.0)
    s.text("Der RK3576 erscheint hier NICHT als Symbol - seine Ball-Map ist HOLD.", g(18), g(12))
    s.text("Die Signale kommen als Durchfuehrung ueber J_UI/J_DSI (Design-Spec).", g(18), g(15))
    s.text("TBD (Gate G01): DSI-Init-Sequenz, Lane-Timings, Backlight-String V/I, Panel-MPN.",
           g(18), g(19))
    s.text("Power-Sequenz: VLCD_3V3 -> LCD_RST_n freigeben -> Backlight erst bei gueltigem Video.",
           g(18), g(22))
    return s


# ------------------------------------- UI-Carrier Sheet 02 (real)
#
# Quelle: hardware/ui-carrier/schematic/sheet_02_touch.md
# FIXED  : I2C-Bus + INT/RST + Rail. TBD: Adresse, Init, Timing (G01).

def build_ui_carrier_sheet02() -> Sheet:
    board, sheet = "ui-carrier", "sheet_02_touch"

    ctrl_pins = [("SCL", "TP_SCL"), ("SDA", "TP_SDA"), ("INT", "TP_INT"),
                 ("RST", "TP_RST"), ("VDD", "VDD_TP_3V3"), ("GND", "GND")]
    host_pins = [(n, n) for _p, n in ctrl_pins[:5]] + [("GND", "GND")]

    extra = "\n" + conn_symbol("J_TOUCH_FPC", [(p, p) for p, _ in ctrl_pins])
    extra += "\n" + conn_symbol("J_UI_TOUCH", host_pins)
    s = Sheet(board, sheet, "ONE-X UI-Carrier - Sheet 02 - Kapazitiver Touch", extra)

    hx, hy = g(24), g(40)
    cx2, cy2 = g(88), g(40)
    s.place("J_UI_TOUCH", hx, hy, "J42", "J_UI (Touch)")
    s.place("J_TOUCH_FPC", cx2, cy2, "J43", "Touch-FPC (GT911-Klasse)")

    htop = conn_pin_offset(len(host_pins))
    ctop = conn_pin_offset(len(ctrl_pins))
    hpin_x, cpin_x = hx + CONN_PIN_X, cx2 + CONN_PIN_X

    nets = [n for _p, n in ctrl_pins[:5]]
    for i, net in enumerate(nets):
        s.wire(hpin_x, hy - htop + g(2) * i, hpin_x + g(4), hy - htop + g(2) * i)
        s.glabel(net, hpin_x + g(4), hy - htop + g(2) * i)
        s.wire(cpin_x, cy2 - ctop + g(2) * i, cpin_x + g(4), cy2 - ctop + g(2) * i)
        s.glabel(net, cpin_x + g(4), cy2 - ctop + g(2) * i)

    for cxx, cyy, top_, n_, tag in ((hpin_x, hy, htop, len(host_pins) - 1, "H"),
                                    (cpin_x, cy2, ctop, len(ctrl_pins) - 1, "C")):
        gy = cyy - top_ + g(2) * n_
        s.wire(cxx, gy, cxx + g(4), gy)
        s.wire(cxx + g(4), gy, cxx + g(4), gy + g(4))
        s.place("GND", cxx + g(4), gy + g(4), f"#PWRT{tag}", "GND")
    if claim_power_flag(board, "GND"):
        gy = hy - htop + g(2) * (len(host_pins) - 1)
        s.wire(hpin_x + g(4), gy, hpin_x + g(8), gy)
        s.place("PWR_FLAG", hpin_x + g(8), gy, "#FLG42", "PWR_FLAG")

    # Genau EIN Pull-up-Satz am I2C (Sheet 02: "Doppel-Pull-up vermeiden").
    for i, net in enumerate(("TP_SCL", "TP_SDA")):
        px_ = g(56) + g(8) * i
        s.glabel("VDD_TP_3V3", px_, g(14))
        s.wire(px_, g(14), px_, g(18))
        s.place("R", px_, g(22), s._ref("R"), "4k7",
                fields={"ONEX_Status": "TARGET",
                        "ONEX_Note": "I2C-Pull-up, genau ein Satz je Bus"})
        s.wire(px_, g(26), px_, g(30))
        s.glabel(net, px_, g(30))

    if claim_power_flag(board, "VDD_TP_3V3"):
        s.glabel("VDD_TP_3V3", g(40), g(14))
        s.wire(g(40), g(14), g(44), g(14))
        s.place("PWR_FLAG", g(44), g(14), "#FLG43", "PWR_FLAG")

    s.text("FIXED: I2C-Bus + INT/RST + Rail. Genau EIN Pull-up-Satz je Bus.", g(18), g(8), 2.0)
    s.text("TBD (G01): I2C-Adresse, Init-Register, Reset-/INT-Timing.", g(18), g(11))
    s.text("Achtung Adress-Strapping: GT911-Klasse waehlt die Adresse ueber INT/RST-Pegel", g(18), g(56))
    s.text("waehrend des Resets - die Boot-Sequenz entscheidet mit (Bringup G01).", g(18), g(59))
    return s


# ------------------------------------- UI-Carrier Sheet 03 (real)
#
# Quelle: hardware/ui-carrier/schematic/sheet_03_input_ring_dpad_keys.md
#
# HOLD-treu: Der Touch-Ring erscheint NICHT als Schaltung. Seine Anbindung
# (Cap-Touch-AFE ueber I2C oder RP2350-Sense-Pins) ist offen; Netznamen dafuer
# zu erfinden hiesse, die Architekturfrage stillschweigend zu entscheiden.

def build_ui_carrier_sheet03() -> Sheet:
    board, sheet = "ui-carrier", "sheet_03_input_ring_dpad_keys"

    keys = ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_CENTER",
            "KEY_SK1", "KEY_SK2", "KEY_SK3", "KEY_SK4", "KEY_SK5"]

    pins = [(k, k) for k in keys] + [("GND", "GND")]
    extra = "\n" + conn_symbol("J_UI_KEYS", pins)
    s = Sheet(board, sheet,
              "ONE-X UI-Carrier - Sheet 03 - Eingabe: D-Pad / Softkeys / Ring", extra)

    cx3, cy3 = g(24), g(56)
    s.place("J_UI_KEYS", cx3, cy3, "J44", "J_UI (RP2350-Domaene)")
    top = conn_pin_offset(len(pins))
    pin_x = cx3 + CONN_PIN_X

    for i, key in enumerate(keys):
        py = cy3 - top + g(2) * i
        s.wire(pin_x, py, pin_x + g(4), py)
        s.glabel(key, pin_x + g(4), py)

        # Je Taste: Pull-up Richtung Ruhezustand + Taster gegen Masse.
        # Aktiv-low, wie in der Spec beschrieben.
        row_y = g(16) + g(14) * i
        s.glabel(key, g(52), row_y)
        s.wire(g(52), row_y, g(56), row_y)
        s.place("SW", g(56), row_y + g(5), s._ref("SW"), key.replace("KEY_", ""),
                fields={"ONEX_Status": "TARGET",
                        "ONEX_Note": "mech. Taster / Dome, aktiv-low"})
        s.wire(g(56), row_y, g(56), row_y + g(1))
        s.wire(g(56), row_y + g(9), g(56), row_y + g(11))
        s.place("GND", g(56), row_y + g(11), f"#PWRK{i:02d}", "GND")

    gy = cy3 - top + g(2) * len(keys)
    s.wire(pin_x, gy, pin_x + g(4), gy)
    s.wire(pin_x + g(4), gy, pin_x + g(4), gy + g(4))
    s.place("GND", pin_x + g(4), gy + g(4), "#PWRK99", "GND")
    if claim_power_flag(board, "GND"):
        s.wire(pin_x + g(4), gy, pin_x + g(8), gy)
        s.place("PWR_FLAG", pin_x + g(8), gy, "#FLG44", "PWR_FLAG")

    s.text("Alle Bedienelemente haengen am RP2350, NICHT am RK3576 -", g(18), g(8), 2.0)
    s.text("damit Wake, Navigation vor dem Linux-Boot, Recovery und", g(18), g(11))
    s.text("RF-Kill-Bestaetigung ohne laufendes Linux funktionieren.", g(18), g(14))
    s.text("TOUCH-RING (Oe40) bewusst NICHT gezeichnet: die Anbindung ist offen -", g(72), g(16), 2.0)
    s.text("Cap-Touch-AFE ueber I2C ODER RP2350-eigene Sense-Pins, AFE-MPN TBD.", g(72), g(20))
    s.text("Netznamen dafuer zu erfinden hiesse, die Architekturfrage still zu", g(72), g(23))
    s.text("entscheiden. Folgt mit dem AFE-Freeze (Gate G07).", g(72), g(26))
    s.text("Entprellung: RC + Firmware-Debounce im RP2350 (onex_modules.h).", g(72), g(32))
    return s


# ------------------------------------- UI-Carrier Sheet 04 (real)
#
# Quelle: hardware/ui-carrier/schematic/sheet_04_haptic_status_connector.md
#
# LED_RFKILL ist sicherheitsrelevant: sie zeigt den PHYSISCHEN Kill-Zustand und
# wird vom RP2350 getrieben -- nicht von Linux. Sonst leuchtete sie falsch,
# sobald Linux haengt, und genau dann ist die Anzeige am wichtigsten.

def build_ui_carrier_sheet04() -> Sheet:
    board, sheet = "ui-carrier", "sheet_04_haptic_status_connector"

    leds = [("LED_PWR", "Power/Charge"),
            ("LED_RFKILL", "RF-Kill aktiv (rot) - vom RP2350"),
            ("LED_ACT", "Aktivitaet / TX")]
    haptic = ["HAPTIC_PWM", "HAPTIC_EN"]

    pins = [(n, n) for n, _ in leds] + [(h, h) for h in haptic] + [("GND", "GND")]
    extra = "\n" + conn_symbol("J_UI_STATUS", pins)
    extra += "\n" + conn_symbol("J_ACTUATOR", [("VHAPTIC", "VHAPTIC"), ("GND", "GND")])
    s = Sheet(board, sheet,
              "ONE-X UI-Carrier - Sheet 04 - Haptik / Status-LED / Connector", extra)

    cx4, cy4 = g(24), g(40)
    s.place("J_UI_STATUS", cx4, cy4, "J45", "J_UI (Status/Haptik)")
    top = conn_pin_offset(len(pins))
    pin_x = cx4 + CONN_PIN_X

    all_n = [n for n, _ in leds] + haptic
    for i, net in enumerate(all_n):
        py = cy4 - top + g(2) * i
        s.wire(pin_x, py, pin_x + g(4), py)
        s.glabel(net, pin_x + g(4), py)

    gy = cy4 - top + g(2) * len(all_n)
    s.wire(pin_x, gy, pin_x + g(4), gy)
    s.wire(pin_x + g(4), gy, pin_x + g(4), gy + g(4))
    s.place("GND", pin_x + g(4), gy + g(4), "#PWRS0", "GND")
    if claim_power_flag(board, "GND"):
        s.wire(pin_x + g(4), gy, pin_x + g(8), gy)
        s.place("PWR_FLAG", pin_x + g(8), gy, "#FLG45", "PWR_FLAG")

    # LEDs mit Vorwiderstand gegen Masse.
    for i, (net, why) in enumerate(leds):
        row_y = g(16) + g(14) * i
        s.glabel(net, g(56), row_y)
        s.wire(g(56), row_y, g(60), row_y)
        s.place("R", g(60), row_y + g(4), s._ref("R"), "1k",
                fields={"ONEX_Status": "TARGET", "ONEX_Note": "Strombegrenzung"})
        s.wire(g(60), row_y + g(8), g(60), row_y + g(10))
        s.place("LED", g(60), row_y + g(14), s._ref("D"), net.replace("LED_", ""),
                fields={"ONEX_Status": "TARGET", "ONEX_Note": why})
        s.wire(g(60), row_y + g(18), g(60), row_y + g(20))
        s.place("GND", g(60), row_y + g(20), f"#PWRL{i}", "GND")

    # Haptik-Treiber: PWM + Enable vom RP2350, Aktuator an VHAPTIC (lokal).
    hx4, hy4 = g(88), g(24)
    s.glabel("HAPTIC_PWM", hx4 - g(12), hy4 - g(2))
    s.wire(hx4 - g(12), hy4 - g(2), hx4 - g(6), hy4 - g(2))
    s.glabel("HAPTIC_EN", hx4 - g(12), hy4 + g(2))
    s.wire(hx4 - g(12), hy4 + g(2), hx4 - g(6), hy4 + g(2))
    s.place("AND2", hx4, hy4, "U41", "HAPTIC_DRV",
            fields={"ONEX_Status": "TARGET",
                    "ONEX_Note": "LRA/ERM offen - bestimmt Resonanz (TBD)"})
    s.wire(hx4 + g(6), hy4, hx4 + g(10), hy4)
    # VHAPTIC ist board-lokal: entsteht hier, treibt den Aktuator hier.
    s.label("VHAPTIC", hx4 + g(10), hy4)

    # Der Aktuator selbst ist ein externes Bauteil (LRA oder ERM -- die Wahl
    # bestimmt Resonanz und Ansteuerung und ist noch offen). Er haengt an einem
    # eigenen Anschluss; ohne ihn haette VHAPTIC keinen Verbraucher.
    ax, ay = hx4 + g(6), hy4 + g(16)
    s.place("J_ACTUATOR", ax, ay, "J46", "Haptik-Aktuator",
            fields={"ONEX_Status": "TARGET", "ONEX_Note": "LRA oder ERM - TBD"})
    atop = conn_pin_offset(2)
    apin_x = ax + CONN_PIN_X
    s.wire(apin_x, ay - atop, apin_x + g(4), ay - atop)
    s.label("VHAPTIC", apin_x + g(4), ay - atop)
    s.wire(apin_x, ay - atop + g(2), apin_x + g(4), ay - atop + g(2))
    s.wire(apin_x + g(4), ay - atop + g(2), apin_x + g(4), ay - atop + g(6))
    s.place("GND", apin_x + g(4), ay - atop + g(6), "#PWRA0", "GND")

    s.text("LED_RFKILL ist sicherheitsrelevant: sie zeigt den PHYSISCHEN Kill-Zustand", g(18), g(8), 2.0)
    s.text("und wird vom RP2350 getrieben, nicht von Linux. Sonst leuchtete sie falsch,", g(18), g(11))
    s.text("sobald Linux haengt - und genau dann ist die Anzeige am wichtigsten.", g(18), g(14))
    s.text("TBD: Haptik-Treiber-MPN und Aktuatortyp (LRA vs. ERM) - bestimmt die Ansteuerung.",
           g(72), g(40))
    return s


SHEETS = [
    ("antenna-rail", "sheet_01_sma_feeds", build_antenna_rail_sheet01),
    ("m2-bridge", "sheet_01_pcie_usb3", build_m2_bridge_sheet01),
    ("m2-bridge", "sheet_02_sideband_power", build_m2_bridge_sheet02),
    ("rf-core", "sheet_01_supervisor_rfkill", build_rf_core_sheet01),
    ("ui-carrier", "sheet_01_display_dsi", build_ui_carrier_sheet01),
    ("ui-carrier", "sheet_02_touch", build_ui_carrier_sheet02),
    ("ui-carrier", "sheet_03_input_ring_dpad_keys", build_ui_carrier_sheet03),
    ("ui-carrier", "sheet_04_haptic_status_connector", build_ui_carrier_sheet04),
]


# ------------------------------------------------------- Symbolbibliothek
#
# Die Symbole stecken zwar in jeder .kicad_sch (lib_symbols), aber ohne
# registrierte Bibliothek meldet ERC fuer JEDES Bauteil eine Warnung. Eine
# echte .kicad_sym plus sym-lib-table loest das -- und macht die Symbole in
# der KiCad-GUI wiederverwendbar, statt sie in generierten Dateien zu
# vergraben.

def render_board_root(board: str, sheets: list[str], titles: dict[str, str]) -> str:
    """
    Root-Sheet eines Boards: instanziiert alle Sub-Sheets.

    Warum das mehr ist als Kosmetik: Ohne Root pruefte ERC jedes Blatt fuer
    sich. Globale Labels, die zwei Blaetter verbinden sollen, sahen darin wie
    einsame Netze aus -- weshalb ein Teil der Meldungen unvermeidbar war. Im
    Board-Kontext verbinden sie sich wirklich, und ERC prueft, was das Board
    tatsaechlich ist: die Summe seiner Blaetter samt ihrer Verbindungen.
    """
    root_uuid = uid(board, "board_root")
    parts = [
        '(kicad_sch',
        '	(version 20250114)',
        '	(generator "onex_gen_kicad_sch")',
        '	(generator_version "10.0")',
        f'	(uuid "{root_uuid}")',
        '	(paper "A4")',
        '	(title_block',
        f'		(title "ONE-X {board} - Board-Root")',
        '		(company "G4MEOVER ONE-X")',
        '		(comment 1 "Erzeugt von tools/gen_kicad_sch.py - nicht von Hand editieren")',
        '	)',
        '	(lib_symbols)',
    ]
    y = 25.4
    for i, sheet in enumerate(sheets):
        inst = uid(board, sheet, "instance")
        title = titles.get(sheet, sheet)
        parts += [
            '	(sheet',
            f'		(at 25.4 {y:.2f})',
            '		(size 152.4 20.32)',
            '		(fields_autoplaced yes)',
            '		(stroke (width 0.1524) (type solid))',
            '		(fill (color 0 0 0 0.0000))',
            f'		(uuid "{inst}")',
            f'		(property "Sheetname" "{title}" (at 25.4 {y - 0.8:.2f} 0)',
            '			(effects (font (size 1.27 1.27)) (justify left bottom)))',
            f'		(property "Sheetfile" "{sheet}.kicad_sch" (at 25.4 {y + 21.0:.2f} 0)',
            '			(effects (font (size 1.27 1.27)) (justify left top)))',
            '		(instances',
            f'			(project "{board}"',
            f'				(path "/{root_uuid}" (page "{i + 2}"))',
            '			)',
            '		)',
            '	)',
        ]
        y += 25.4
    parts += [
        '	(sheet_instances',
        '		(path "/" (page "1"))',
        '	)',
        '	(embedded_fonts no)',
        ')',
    ]
    return "\n".join(parts) + "\n"


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
    _POWER_FLAGS.clear()   # reproduzierbar, auch bei mehrfachem Aufruf

    extra_defs = ""
    by_board: dict[str, list[str]] = {}
    titles: dict[str, str] = {}
    for board, sheet, build in SHEETS:
        s = build()
        extra_defs += s.extra_symbols
        by_board.setdefault(board, []).append(sheet)
        titles[sheet] = s.title
        artifacts.append((REPO / "hardware" / board / "kicad" / f"{sheet}.kicad_sch",
                          s.render()))
        artifacts.append((REPO / "hardware" / board / "kicad" / "sym-lib-table",
                          SYM_LIB_TABLE))

    # Je Board ein Root-Sheet, das seine Blaetter instanziiert. Dadurch prueft
    # ERC das Board als Ganzes statt jedes Blatt fuer sich.
    for board, sheets in by_board.items():
        artifacts.append((REPO / "hardware" / board / "kicad" / f"{board}.kicad_sch",
                          render_board_root(board, sorted(sheets), titles)))

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
