# KiCad-Bauplan — m2-bridge

> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.
> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der
> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).

## Hierarchie
- Root-Sheet `m2-bridge.kicad_sch` instanziiert **2** Sub-Sheets.
- Root-UUID (fix): `2b12aa56-1804-5e18-a2fc-1606bbf12418`

## Sub-Sheets (Reihenfolge + Global-Labels)

| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |
|---|---|---|---|---|
| 01 | `sheet_01_pcie_usb3.kicad_sch` | M.2-Bridge Sheet 01 — High-Speed (PCIe 2.1 ×1 / USB3) | `PCIE_CLKREQ_n`, `PCIE_REFCLK_P`, `PCIE_RX_P`, `PCIE_TX_P`, `USB3_M2_RX_P`, `USB3_M2_TX_P` | zeichnen |
| 02 | `sheet_02_sideband_power.kicad_sch` | M.2-Bridge Sheet 02 — Sideband / Power / Testpoints | `HYPERRF_AUX_5V`, `PCIE_CLKREQ_n`, `PCIE_PERST_n`, `PCIE_REFCLK`, `PCIE_WAKE_n` | zeichnen |

## Regeln
- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus
  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).
- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).
- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.
- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.
