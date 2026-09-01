# KiCad-Bauplan — rf-core

> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.
> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der
> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).

## Hierarchie
- Root-Sheet `rf-core.kicad_sch` instanziiert **7** Sub-Sheets.
- Root-UUID (fix): `dc1d8bb0-680a-5d14-bfdd-dd7737ee8729`

## Sub-Sheets (Reihenfolge + Global-Labels)

| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |
|---|---|---|---|---|
| 01 | `sheet_01_supervisor_rfkill.kicad_sch` | RF-Core Sheet 01 — Supervisor / RF-Kill (sicherheitskritisch) | `RF_KILL`, `RF_KILL_SW_n`, `TX_GATE_OK` | zeichnen |
| 02 | `sheet_02_subghz.kicad_sch` | RF-Core Sheet 02 — Sub-GHz (CC1101 + SX1262) | `RFC_SPI`, `RFC_SPI_SCK` | zeichnen |
| 03 | `sheet_03_24ghz_zwave.kicad_sch` | RF-Core Sheet 03 — 2,4 GHz (CC2652P7) + Z-Wave (EFR32ZG23) | — | zeichnen |
| 04 | `sheet_04_nfc_lfrfid.kicad_sch` | RF-Core Sheet 04 — NFC/HF (PN7160) + 125 kHz LF-RFID | — | zeichnen |
| 05 | `sheet_05_uhf_rain.kicad_sch` | RF-Core Sheet 05 — UHF RAIN RFID (E710) | — | zeichnen |
| 06 | `sheet_06_ir_1wire.kicad_sch` | RF-Core Sheet 06 — IR / 1-Wire | — | zeichnen |
| 07 | `sheet_07_power_host_antennas.kicad_sch` | RF-Core Sheet 07 — Power / Host-Link / Antennen / Testpoints | `RFC_I2C`, `RFC_IRQ`, `RFC_SPI`, `RFC_UART`, `RF_KILL`, `TX_GATE_OK` | zeichnen |

## Regeln
- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus
  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).
- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).
- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.
- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.
