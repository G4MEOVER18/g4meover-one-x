# ONE-X — Board-Set (EVT)

Alle Outlines/Lagen sind **FIXED** aus der Master-Spec (`pcb.*`). Stackup/Prozess für das Mainboard ist **HOLD** (→ PCBWay-DFM, G06).

| Board | Outline (mm) | Lagen | Prozess | Kern-Inhalt | Status |
|---|---|---|---|---|---|
| **Mainboard** | 210 × 92 | **12** | **HDI** (Stackup HOLD → G06) | RK3576, RK806S-PMIC, LPDDR5 (Topo HOLD), UFS (MPN HOLD), USB-C-PD/USB3/DP, 2× GbE, Wi-Fi 6E/BT, M.2, RP2350-Link, Audio, Sensoren, Power-Tree | Outline/Lagen FIXED; Stackup HOLD |
| **UI-Carrier** | 218 × 100 | TBD (Minewing) | Standard | Display-FPC, Touch-I²C, Touch-Ring-AFE, Haptik, 5 Softkeys, Status-LEDs | Outline FIXED |
| **RF-Core** | 92 × 66 | TBD | Standard + RF | CC1101, SX1262, CC2652P7, PN7160, LF-RFID-AFE, Z-Wave, UHF-RAIN, IR/1-Wire, **HW-RF-Kill** | Outline FIXED |
| **HyperRF** | 136 × 72 | TBD (HDI wahrsch.) | HDI + RF | 2× LMS7002M, High-Band-Conversion, **FPGA (MPN HOLD → G04)**, 5G/NTN-Bay, GNSS, UWB (Suffix HOLD → G05), 60-GHz-Radar-Tile | Outline FIXED; FPGA HOLD |
| **M.2-Bridge** | 30 × 52 | TBD | Standard | PCIe 2.1 ×1 + USB3 Brücke Mainboard↔HyperRF | Outline FIXED |
| **Antenna-Rail** | 150 × 18 | TBD | RF | 4× externe SMA, Filter/Matching-Vorbereitung | Outline FIXED; 4 SMA FIXED |

## Verbindungen (aus Interface-Matrix)
- **Mainboard ↔ HyperRF:** M.2, **PCIe 2.1 ×1 + USB3** (FIXED; kein Gen3 ×4).
- **Mainboard ↔ RP2350-Link:** SPI + I²C + UART (FIXED) — Kommandos/Status/Recovery.
- **RK3576 ↔ Display:** 4-lane MIPI-DSI (FIXED); Touch I²C+IRQ (FIXED).
- **Netzwerk:** 2× RGMII → RTL8211F-Klasse PHYs (FIXED).
- **RF-Hard-Kill:** physischer Supervisor-Gate über alle PA-Enables (FIXED, softwareunabhängig).

## Kritische Layout-Themen (für SI/PI-Review, Gate G08)
- **LPDDR5:** nicht routen vor bestätigter Rockchip-Topologie (G02) — Längen/Skew/Impedanz.
- **UFS:** M-PHY, validiertes Device (G03).
- **PCIe 2.1 ×1 / USB3:** Impedanz, Return-Path, AC-Kopplung, Länge.
- **RF:** kontrollierte Impedanz, Isolation zwischen SDR-Kanälen, HyperRF↔RF-Core-Trennung, metallfreie RF-Fenster (Thermik-Constraint).
- **Power:** IR-Drop bei +5V_SYS (10 A transient), RK806S-Rail-Map (HOLD).

## Maßquellen
`spec/G4MEOVER-ONE-X_MASTER_SPEC.json` → `pcb.*_outline_mm`, `pcb.mainboard_layers=12`, `mechanical.*`. Nichts hier darf der Master-Spec widersprechen.
