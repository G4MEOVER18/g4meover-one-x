# G4MEOVER ONE-X — Minewing JDM-Datenpaket

**Projekt:** G4MEOVER ONE-X — modularer Linux-Handheld · **Rev:** EVT6
**Owner:** Yanis Ameseder (G4MEOVER18) · **Repo:** https://github.com/G4MEOVER18/g4meover-one-x
**Gegenüber:** Jenny, Overseas Sales (jenny@minewing.com, WeChat/WhatsApp +86 17776192691)
**Kooperationsmodell:** JDM (Joint Design Manufacturing) — Design vorhanden, Engineering + Fertigung gesucht.

## Gerät in Kürze
230 × 110 × 64 mm, 800–950 g. RK3576 + 16 GB LPDDR5 + 256 GB UFS, 5″ MIPI-DSI-Touch, RP2350B-Systemcontroller, RF-Core (Sub-GHz/NFC/RFID/Zigbee/Z-Wave), HyperRF (2× LMS7002M SDR + FPGA + 5G/NTN/GNSS/UWB/Radar), 2× GbE, Wi-Fi 6E, 4× 21700 (~72 Wh).

## Gesuchte Arbeitspakete (Scope für Minewing)
| # | Paket | Bezug (Gate) | Deliverable |
|---|---|---|---|
| WP1 | Schaltplan-Review Mainboard | G07 | Review-Report, ERC-Checkliste |
| WP2 | SI/PI + Layout-Review High-Speed | G08 | Impedanz-/Return-Path-/Skew-Audit |
| WP3 | DFM Mainboard 12L HDI (+ mit PCBWay abstimmbar) | G06 | DFM-Report, Stackup |
| WP4 | Komponenten-Sourcing HOLD-Teile | G02/G03/G04 | LPDDR5-Topologie, UFS-MPN, FPGA-Kandidatenmatrix |
| WP5 | Mechanik + Thermal | G10 | Gehäuse-Toleranzen, Kühlkonzept, ggf. Vapor-Chamber |
| WP6 | Akku-Pack-Engineering | G11 | 2S2P-Pack, BMS, UN38.3-Pfad |
| WP7 | EVT-Build 5–10 Einheiten | Phase 12 | bestückte Boards, X-Ray, AOI, Bring-up-Support |

## Technische Eckdaten (für Quotation)
- **Mainboard:** 210 × 92 mm, 12-Layer HDI, RK3576-BGA, RK806S-5 PMIC.
- **High-Speed-Netze:** 2× RGMII, PCIe **2.1 ×1** (kein Gen3 ×4), USB3.x, MIPI-DSI 4-Lane, HDMI/DP-Alt, LPDDR5.
- **6 Boards** modular (siehe `spec/` + `hardware/`).
- **Status-Disziplin:** offene Herstellerdetails sind als **HOLD** markiert und werden nicht geraten — hier ist Minewings Sourcing-/Referenz-Zugang der Hebel.

## Rahmen & Bedingungen
- **NDA** vor Weitergabe produktionsrelevanter Details — vom Owner ausdrücklich gewünscht.
- Kooperationsmodell **JDM**, prototypennahe Stückzahl zuerst (EVT 5–10).
- Open-Source-Projekt (Hardware CERN-OHL-S) — kommerzielle Fertigung/Vermarktung durch den Owner bleibt möglich.

## Benötigte Rückmeldungen von Minewing
1. Passt RK3576 + LPDDR5/UFS in euren Standard-Scope?
2. NDA-Prozess + Ablauf einer ersten Engineering-/Quotation-Runde.
3. Grobe Größenordnung: Engineering-Support vs. Stückkosten bei Prototypmenge.
4. Realistische Timeline EVT-Build (CN vs. VN).
