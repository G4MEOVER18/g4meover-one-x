#!/usr/bin/env python3
"""G4MEOVER ONE-X -- Cross-Sheet Netznamen-Konsistenzcheck.

Prueft, ob die Inter-Board-Signale (siehe hardware/INTERFACE_NETS.md) an ALLEN
beteiligten Boards mit dem kanonischen Namen vorkommen. Faengt Mirror-Luecken,
bevor die KiCad-ERC (G07) sie teuer macht.

Heuristik: ein Board 'fuehrt' einen Netz-Stamm, wenn irgendein Sheet-Text unter
hardware/<board>/schematic/ den Stamm als Teilstring enthaelt. Bewusst tolerant
(Prosa-Sheets), aber streng genug fuer Praefix-/Schreibweisen-Divergenzen.

Aufruf:  python tools/schematic_netcheck.py
Exit 0 = konsistent; Exit 1 = mindestens eine Mirror-Luecke.
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"

# Interface -> beteiligte Boards + kanonische Netz-Staemme (aus INTERFACE_NETS.md)
INTERFACES = [
    ("J_M2 PCIe 2.1 x1", ["mainboard", "m2-bridge", "hyperrf"],
     ["PCIE_TX", "PCIE_RX", "PCIE_REFCLK", "PCIE_PERST_n", "PCIE_CLKREQ_n", "PCIE_WAKE_n"]),
    ("J_M2 USB3", ["mainboard", "m2-bridge"],
     ["USB3_M2_TX", "USB3_M2_RX"]),
    ("J_DSI/J_UI Display+Touch", ["mainboard", "ui-carrier"],
     ["DSI0_CLK", "DSI0_D0", "LCD_RST_n", "BL_EN", "TP_SCL", "TP_SDA", "TP_INT"]),
    ("J_RFCORE Radio-Bus", ["mainboard", "rf-core"],
     ["RFC_SPI", "RFC_UART", "RFC_IRQ", "RF_KILL", "TX_GATE_OK"]),
    ("J_ANT Antennen-Feeds", ["mainboard", "antenna-rail"],
     ["ANT_1", "ANT_2", "ANT_3", "ANT_4"]),
    ("Power HYPERRF_AUX_5V", ["mainboard", "m2-bridge", "hyperrf"],
     ["HYPERRF_AUX_5V"]),
]


def board_text(board):
    d = HW / board / "schematic"
    if not d.exists():
        return None
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in d.glob("*.md"))


def main():
    print("== G4MEOVER ONE-X -- Cross-Sheet Netznamen-Konsistenzcheck ==")
    texts = {}
    gaps = 0
    checks = 0
    for name, boards, stems in INTERFACES:
        print(f"\n[{name}]  Boards: {', '.join(boards)}")
        for b in boards:
            if b not in texts:
                texts[b] = board_text(b)
            if texts[b] is None:
                print(f"  ! Board '{b}' hat kein schematic/-Verzeichnis")
        for stem in stems:
            checks += 1
            present = [b for b in boards if texts.get(b) and stem in texts[b]]
            missing = [b for b in boards if b not in present]
            if missing:
                gaps += 1
                print(f"  MISMATCH  {stem:16s} fehlt bei: {', '.join(missing)}  (vorhanden: {', '.join(present) or '-'})")
            else:
                print(f"  ok        {stem}")

    print("\n" + "-" * 60)
    print(f"Geprueft: {checks} Netz-Staemme ueber {len(INTERFACES)} Interfaces")
    if gaps:
        print(f"ERGEBNIS: {gaps} Mirror-Luecke(n) -- vor KiCad/ERC (G07) beheben.")
        return 1
    print("ERGEBNIS: konsistent. Alle kanonischen Inter-Board-Netze beidseitig vorhanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
