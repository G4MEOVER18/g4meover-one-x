# Sheet 17 — Connectors (Inter-Board)

Alle Board-zu-Board-/FPC-Verbinder des ONE-X-Board-Sets (siehe [`../../../manufacturing/BOARD_SET.md`](../../../manufacturing/BOARD_SET.md)). Outlines FIXED; Steckertypen TARGET (Bauraum/Pinbudget). **Netznamen kanonisch nach [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md)** (beidseitig gespiegelt; geprüft von `tools/schematic_netcheck.py`).

## Verbindungen (Mainboard-seitig)

| Connector | Ziel-Board | Signale | Status |
|---|---|---|---|
| `J_UI` | UI-Carrier (218×100) | `DSI0_*`-Durchführung, Touch (`TP_SCL`, `TP_SDA`, `TP_INT`, `TP_RST`), `LCD_RST_n`/`BL_EN`/`BL_PWM`, Touch-Ring/Haptik/`KEY_*`/`LED_*` | Outline FIXED / Pinout TBD 📄 |
| `J_DSI` | Display-FPC | 4-lane MIPI-DSI (`DSI0_CLK_P/N`, `DSI0_D0..D3_P/N`) + Backlight + Touch | FIXED (Signale) |
| `J_RFCORE` | RF-Core (92×66) | `RFC_SPI_*`, `RFC_UART_*`, `RFC_I2C_*`, `RFC_IRQ_*`, `RF_KILL`, `RF_KILL_SW_n`, `TX_GATE_OK`, `+3V3_SYS` | Pinout TBD 📄 |
| `J_M2` | M.2-Bridge → HyperRF | PCIe 2.1 ×1 + USB3 + Sideband + `HYPERRF_AUX_5V` (Sheet 12) | FIXED (Signale) |
| `J_ANT` | Antenna-Rail (150×18) | 4× SMA-Feeds `ANT_1`/`ANT_2`/`ANT_3`/`ANT_4` (50 Ω) | FIXED (4 SMA) |
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

## Korrektur (2026-09-09) — Antennen-Feeds und Power

Diese Tabelle führte `J_RFCORE` bisher mit „…, **Antennen-Feeds, Power**". Beim
Zeichnen von [RF-Core Sheet 07](../../rf-core/schematic/sheet_07_power_host_antennas.md)
zerfiel das in zwei getrennte Befunde:

* **Power war schlicht vergessen.** `+3V3_SYS` stand in der Aufzählung, aber
  nicht in der Zeichnung — der RF-Core-Stecker hatte keinen Versorgungspin,
  obwohl das [Netz-Wörterbuch](../../INTERFACE_NETS.md) die Rail ausdrücklich
  über `J_RFCORE` führt. Nachgezogen; die Rail hat jetzt beide Enden
  (`m2-bridge ↔ mainboard ↔ rf-core`).
* **Die Antennen-Feeds bleiben ungezeichnet.** Nicht aus Nachlässigkeit: Welcher
  Feed auf welchem SMA landet, ist TBD (→ G09), und ein Netz hat genau **einen**
  Namen. Solange die Zuordnung offen ist, lässt sich ein RF-Core-Feed nicht
  `ANT_1` nennen — „am Stecker umbenennen" gibt es elektrisch nicht. Ob die
  Feeds überhaupt über dieses Board laufen oder per Koax direkt zur
  Antenna-Rail, entscheidet dieselbe Frage.
