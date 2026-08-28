# RF-Core Sheet 07 — Power / Host-Link / Antennen / Testpoints

Versorgung, Mainboard-Anbindung, Antennen-Aggregation und Bring-up des RF-Core-Boards.

## Power
- Eingang über `J_RFCORE` (Mainboard Sheet 17): `+3V3_SYS` (+ ggf. lokale LDOs für rauschempfindliche Radios).
- Getrennte, gefilterte Analog-/RF-Rails wo nötig (Ferrit/π-Filter je Radio).

## Host-Link (zum Mainboard)
| Netz | Funktion |
|---|---|
| `RFC_SPI_*`, `RFC_UART_*` | gemeinsame Radio-Busse (getrennte CS/Selektoren) |
| `RFC_I2C_*` | NFC (PN7160) |
| `RF_KILL`, `TX_GATE_OK` | Sicherheitspfad (Sheet 01) |
| `RFC_IRQ_*` | Sammel-IRQs der Radios |

## Antennen-Aggregation
| Feed | Radio |
|---|---|
| `ANT_SUBGHZ` | CC1101/SX1262 (Sheet 02) |
| `ANT_2G4` / `ANT_ZWAVE` | CC2652P7 / EFR32ZG23 (Sheet 03) |
| HF-Loop | PN7160 (Sheet 04) |
| LF-Coil | LF-RFID (Sheet 04) |
| `ANT_UHF` | E710 (Sheet 05) |
| IR-Fenster | IR (Sheet 06) |
→ Verteilung auf Antennen-Rail (4× SMA) + interne Antennen; Isolation zwischen Bändern.

## Testpoints (gestaffelter Bring-up)
- **Zuerst:** `RF_KILL` + jeder `PA_EN_*` (physische Kill-Wirksamkeit vor jedem TX-Test).
- Power-Rails, Host-Busse (`RFC_SPI/UART/I2C`), Radio-Resets.
- Pro-Radio-RSSI/TX-Check über Host-SW (RK3576).

## Kritische Design-Notizen
- **RF-Kill zuerst verifizieren** (Sheet 01) — kein TX-Test ohne bestätigten Gate.
- Rail-Filterung gegen gegenseitige Radio-Störung; Masse-/Schirmkonzept.
- Antennen-/Band-Isolation (besonders 2,4 GHz vs. Wi-Fi/BT auf Mainboard, UHF vs. Sub-GHz).

## ERC-Absicht
Rails Power-Input; Host-Busse konsistent zum Mainboard-Connector; Antennen-Feeds eindeutig; Sicherheitsnetze (`RF_KILL`/`PA_EN_*`) mit Sheet 01 abgeglichen.
