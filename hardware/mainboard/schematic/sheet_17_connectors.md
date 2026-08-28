# Sheet 17 — Connectors (Inter-Board)

Alle Board-zu-Board-/FPC-Verbinder des ONE-X-Board-Sets (siehe [`../../../manufacturing/BOARD_SET.md`](../../../manufacturing/BOARD_SET.md)). Outlines FIXED; Steckertypen TARGET (Bauraum/Pinbudget).

## Verbindungen (Mainboard-seitig)

| Connector | Ziel-Board | Signale | Status |
|---|---|---|---|
| `J_UI` | UI-Carrier (218×100) | Display-FPC-Durchführung, Touch-I²C+IRQ, Touch-Ring, Haptik, 5 Softkeys, Status-LEDs | Outline FIXED / Pinout TBD 📄 |
| `J_DSI` | Display-FPC | 4-lane MIPI-DSI + Backlight + Touch | FIXED (Signale) |
| `J_RFCORE` | RF-Core (92×66) | SPI/UART zu Radios, `RF_KILL`, Antennen-Feeds, Power | Pinout TBD 📄 |
| `J_M2` | M.2-Bridge → HyperRF | PCIe 2.1 ×1 + USB3 + Sideband + `HYPERRF_AUX_5V` (Sheet 12) | FIXED (Signale) |
| `J_ANT` | Antenna-Rail (150×18) | 4× SMA-Feeds/Filter | FIXED (4 SMA) |
| `J_BAT` | Akku-Pack (2S2P) | `BAT_2S2P`, NTC, Balancing (Sheet 01, G11) | Pinout TBD 📄 |
| `J_PWR` | USB-C-Board / PD | `VBUS_C`, CC, USB3, DP (Sheet 07) | FIXED (Signale) |

## Kritische Design-Notizen
- **Pin-Budget vor Steckerwahl:** Signal-Zahl je Interface summieren → passenden B2B-/FPC-Stecker (Pitch, Strom, Höhe) wählen; **Höhe** gegen Gehäuse-Bauraum (Mechanik) prüfen.
- **Power-Kontakte:** `HYPERRF_AUX_5V` (5 A) und `BAT_2S2P` mit ausreichend Kontakten/Strombelastbarkeit.
- **RF-Feeds:** Antennen-/Koax-Führung impedanzkontrolliert; Masse-Rückführung an Steckern.
- **Verpolungs-/Fehlsteck-Schutz:** eindeutige Steckerkodierung, unterschiedliche Typen je Board.
- **Testpunkte** an kritischen Steckersignalen (→ Sheet 18).

## ERC-Absicht
Jeder Connector als Multi-Pin-Symbol mit exakt gespiegelten Netznamen zum Ziel-Board; Power-Kontakte als Power-Flags; ungenutzte Pins No-Connect.

## HOLD / TBD
- **Pin-Budget + Steckertyp/-höhe** je Interface (nach vollständigen Sheets) 📄.
- Board-zu-Board-Stapelhöhen ⇒ Mechanik-Kollisionsmodell.
