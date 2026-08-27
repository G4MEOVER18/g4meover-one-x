# G4MEOVER ONE-X — PCBWay Datenpaket / One-Pager

**Projekt:** G4MEOVER ONE-X — modularer Linux-Handheld (RF-Research / Pentest / Netzwerk)
**Owner:** Yanis Ameseder (G4MEOVER18) · **Repo:** https://github.com/G4MEOVER18/g4meover-one-x
**Revision:** EVT6 (Architektur synchronisiert) · **Lizenz:** CERN-OHL-S / MIT / CC-BY-SA
**Gegenüber:** Liam, Marketing (liam@pcbway.com) · Programm: sponsor@pcbway.com

## Worum es geht (für PCBWay = Gate G06)
Wir benötigen einen **HDI-DFM- + Stackup-Partner** für das Mainboard. Kein Produktionslauf ohne schriftliche DFM-Antwort — das ist ausdrücklich ein Release-Gate.

## Board-Übersicht (6 Boards, modular)
| Board | Maße (mm) | Layer/Prozess | Priorität für PCBWay |
|---|---|---|---|
| **Mainboard** | 210 × 92 | **12-Layer HDI** | **HÖCHSTE** (HDI-DFM) |
| UI-Carrier | 218 × 100 | Standard-Multilayer | mittel |
| RF-Core | 92 × 66 | HF-Multilayer | hoch (Impedanz/HF) |
| HyperRF | 136 × 72 | HF-/High-Speed-Multilayer | hoch (PCIe/HF) |
| M.2-Bridge | 30 × 52 | Standard | niedrig |
| Antenna-Rail | 150 × 18 | Standard | niedrig |

## Konkrete DFM-Fragen (Mainboard, 12L HDI)
1. **Stackup-Vorschlag** 12 Layer: Prepreg/Core-Dicken, Dk/Df pro Layer, Kupfer (oz).
2. **Microvia**: Laser-µVia-Durchmesser/Aspect-Ratio, gestackt/gestaffelt, sequenzielle Lamination (1+N+1 / 2+N+2?).
3. **Via-in-Pad**: filled & capped für BGA — Prozess und Mindest-Pad.
4. **Controlled Impedance**: 50 Ω SE / 90 Ω USB / 100 Ω diff (RGMII, PCIe 2.1, USB3, MIPI-DSI) — welche Toleranz garantiert?
5. **BGA-Escape** RK3576 (Pitch laut Rockchip-Referenz): min. Trace/Space, das ihr auf HDI zuverlässig fertigt.
6. **PCBA**: X-Ray für BGA, AOI, Fine-Pitch-QFN, Verfügbarkeit von Bauteil-Sourcing.

## High-Speed-Netzklassen (Kurzliste)
- 2× RGMII (Gigabit Ethernet, RTL8211F)
- PCIe **2.1 ×1** (M.2 / HyperRF) — **kein Gen3 ×4**
- USB3.x (USB-C #1, USB-A), USB2
- MIPI-DSI 4-Lane (Display)
- HDMI/DP-Alt
- LPDDR5 (Topologie noch HOLD — Escape-Beratung willkommen)

## Was PCBWay dafür bekommt
- **PCBWay-Credit** im öffentlichen README (Sponsoren-Sektion).
- **Build-/Review-Beitrag** (Blog + Social) mit PCBWay-Logo nach Erhalt der Prototypen.
- Projekt als **Open-Source-Projekt auf pcbway.com** (Community-Re-Order, 10 %-Programm).
- Youtube Video und Erwähnung auf weiteren Platformen.

## Wichtiger Hinweis (Ehrlichkeit = Vertrauen)
Die aktuellen KiCad-Dateien sind **Floorplans (NOT FOR FABRICATION)**. Wir suchen zuerst **DFM/Stackup-Beratung**, nicht sofort einen Fertigungslauf. Produktions-Gerber folgen erst nach Schließen der HOLD-Gates (LPDDR5-Topologie, UFS, FPGA, Stackup).
