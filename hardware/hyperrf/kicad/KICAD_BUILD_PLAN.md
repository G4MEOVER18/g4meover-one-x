# KiCad-Bauplan — hyperrf

> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.
> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der
> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).

## Hierarchie
- Root-Sheet `hyperrf.kicad_sch` instanziiert **8** Sub-Sheets.
- Root-UUID (fix): `5e6e171b-79ac-52f7-b3cd-ace491916737`

## Sub-Sheets (Reihenfolge + Global-Labels)

| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |
|---|---|---|---|---|
| 01 | `sheet_01_power.kicad_sch` | HyperRF Sheet 01 — Power | `HYPERRF_AUX_5V` | zeichnen |
| 02 | `sheet_02_clock_reference.kicad_sch` | HyperRF Sheet 02 — Takt / Referenz | — | zeichnen |
| 03 | `sheet_03_lms7002m_a.kicad_sch` | HyperRF Sheet 03 — LMS7002M A (SDR-RFIC A) | — | zeichnen |
| 04 | `sheet_04_lms7002m_b.kicad_sch` | HyperRF Sheet 04 — LMS7002M B (SDR-RFIC B) | — | zeichnen |
| 05 | `sheet_05_highband_conversion.kicad_sch` | HyperRF Sheet 05 — High-Band-Conversion (3,8 → 6 GHz) | — | zeichnen |
| 06 | `sheet_06_module_bays.kicad_sch` | HyperRF Sheet 06 — Modul-Bays (5G / NTN / LoRa-Sat / GNSS) | — | zeichnen |
| 07 | `sheet_07_uwb_radar.kicad_sch` | HyperRF Sheet 07 — UWB / 60-GHz-Radar | — | zeichnen |
| 08 | `sheet_08_fpga.kicad_sch` | HyperRF Sheet 08 — FPGA (⛔ Platzhalter — HOLD → G04) | `PCIE_CLKREQ_n`, `PCIE_PERST_n`, `PCIE_REFCLK_P`, `PCIE_RX_P`, `PCIE_TX_P`, `PCIE_WAKE_n` | ⛔ HOLD-Stub |

## Regeln
- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus
  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).
- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).
- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.
- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.
