# G4MEOVER ONE-X — Roadmap & Release-Gates

Weg von der synchronisierten Architektur (EVT6) zum echten EVT-Prototyp — **ohne offene Herstellerdaten zu raten**. Reihenfolge ist wichtig: erst Wissen/Validierung, dann Produktionslayout.

## Release-Gates (Freigabetore)

| Gate | Inhalt | Blocker / Voraussetzung | Status |
|---|---|---|---|
| **G01** | 5″-Display Linux/DSI-Bringup auf RK3576 | RK3576-Devboard + 5″ 720×1280 DSI-Panel, DRM/KMS, Device-Tree, Touch-I²C, Suspend/Resume | offen |
| **G02** | Exakte 16-GB-LPDDR5-Topologie | Rockchip-Referenz/Training-Design | HOLD |
| **G03** | Exaktes 256-GB-UFS-Teil | RK3576-UFS-Host/Device-Validierung | HOLD |
| **G04** | HyperRF-FPGA-MPN-Freeze | quantitative Auswahl (I/O, SERDES, PCIe-EP, BRAM, DSP, Power, Verfügbarkeit) | HOLD |
| **G05** | DW3000-UWB-Suffix-Freeze | Bauteilauswahl | HOLD |
| **G06** | PCBWay 12-Layer-HDI-Stackup/DFM | Outreach vorbereitet (noch keine Zusage) | geplant |
| **G07** | Produktions-Schaltplan ERC clean | nach G02/G03 | offen |
| **G08** | Produktions-Layout DRC/SI/PI komplett | Return-Path, Impedanz, Länge/Skew, IR-Drop | offen |
| **G09** | RF-EVT-Tuning | Matching auf realer Hardware, nie nur aus Simulation einfrieren | offen |
| **G10** | Finale Thermal-Validierung | reale Fan-P/Q-Kurven, 3D-CFD oder Mess-EVT (ersetzt 2D-Precheck) | offen |
| **G11** | Akku-Pack-Compliance | UN38.3, BMS/Sicherung/NTC, mechanischer Schutz | HOLD |

## Phasenplan

- **Phase 0 — Repo & Automation** ✅ Repo-Struktur, Master-Spec, `spec_validator.py`.
- **Phase 1 — Display PoC** → G01. Höchste Priorität (zentrales Produktmerkmal).
- **Phase 2 — RP2350B System-Manager** → Firmware-Architektur (power/buttons/touch_ring/haptic/sensors/fan/battery/watchdog/rk3576_link/recovery/rf_kill/protocol). Muss unabhängig von Linux laufen.
  - Architektur + Protokoll-Verträge ✅
  - **ONE-X-Link-v1-Codec implementiert + host-getestet ✅** (`firmware/rp2350/src/`, 40 Prüfungen via `tools/fw_test.py`, Teil des grünen Tors)
  - **`rf_kill`-Zustandsautomat implementiert + host-getestet ✅** (64 Prüfungen, überwiegend negativ; Freigabe-Policy per Owner-Entscheidung 2026-09-07 festgelegt: One-Shot-Nonce nach physischer Geste + Karenzzeit bei Link-Verlust)
  - **`rk3576_link` (Protokoll-Endpunkt) implementiert + host-getestet ✅** (64 Prüfungen Integration; Duplikat-Cache = Wiederholungen wirken genau einmal; RF-Kill-Freigabe end-to-end über den Draht bedienbar)
  - **`power` + `watchdog` implementiert + host-getestet ✅** (80 Prüfungen; Rail-Sequenz + Umkehrung, „nie endlos warten", Watchdog kickt nur bei durchgehend gesunden kritischen Modulen) → **Sicherheitskette `watchdog → power → rf_kill` durchgehend getestet**
  - **Superloop-Scheduler implementiert + host-getestet ✅** (46 Prüfungen; Tickreihenfolge = Sicherheitspriorität, Event-Zustellung ohne Rekursion, Budget-Überwachung, Kick-Erlaubnis)
  - **→ Phase 2 im Kern abgeschlossen.** Offen bleiben nur die HAL-nahen Module (`buttons`, `touch_ring`, `haptic`, `battery`, `fan`, `sensors`, `recovery`) — sinnvoll erst nach G07 (Pinmap).
- **Phase 3 — Vendor-Docs / Core-BOM-Freeze** → G02/G03. Kein Mainboard-Layout davor.
- **Phase 4 — PCBWay HDI-DFM** → G06.
- **Phase 5 — Mainboard-Schaltplan** (18 Sheets: RK3576-Core, RK806-Power, LPDDR5, UFS, USB-C-PD, USB-Host, HDMI/DP, 2× Ethernet, Wi-Fi/BT, M.2, RP2350-Link, Audio, Sensoren, Debug/Recovery, Connectors, Power-Tree, Testpoints).
- **Phase 6 — SI/PI-first Layout**.
- **Phase 7 — RF-Core** (ein Radio nach dem anderen: Supervisor/Kill → CC1101 → SX1262 → CC2652P7 → PN7160 → LF-RFID → Z-Wave → UHF-RFID → IR/1-Wire).
  - Sheet 01 Supervisor/RF-Kill ✅ · Sheet 07 Power/Antennen/Testpoints ✅ (beide ERC-sauber, pinmap-frei)
  - Sheets 02–06 (Radios) **gesperrt** bis Hersteller-Pinouts vorliegen; Antennen-Feed→SMA-Zuordnung offen (→ G09)
- **Phase 8 — HyperRF-FPGA-Auswahl** → G04 (Scored Candidate Matrix, nicht aus altem Bild wählen).
- **Phase 9 — HyperRF-Hardware** (fpga-core, lms-a/b, converters, filterbank, 5g, ntn, gnss, uwb, radar-tile, clock, power).
- **Phase 10 — Mechanik-EVT** (CadQuery aus finalen Bauteilhöhen, Kollisions-/Montage-Checks).
- **Phase 11 — Thermal** → G10.
- **Phase 12 — Erste EVT-Produktion** (5–10 Einheiten, gestaffelter Power-Up-Bring-up).
- **Phase 13 — EVT2 / DVT** (erst nach dokumentierten EVT-Findings).

## Autonome Arbeitsregel

Jede autonome Session: nächsten offenen Punkt der höchsten unerledigten Phase ziehen → einen kohärenten Schritt → `spec_validator.py` → `docs/AUTONOMOUS_WORKLOG.md` fortschreiben → committen.
