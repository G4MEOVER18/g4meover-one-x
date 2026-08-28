# DFM- / Fertigungs-RFQ — PCBWay (Gate G06)

**Projekt:** G4MEOVER ONE-X (Open-Source-Hardware) · **Owner:** G4MEOVER18
**Stand:** EVT / Engineering-Review · **Zweck:** HDI-Stackup-Definition + DFM-Feasibility für das Mainboard, plus Fertigung des EVT-Board-Sets.

> Dies ist eine **RFQ-/Feasibility-Anfrage**, keine finale Gerber-Übergabe. Finale Gerber folgen nach Schaltplan (G07) + Layout (G08), die u.a. **auf dem hier von PCBWay definierten Stackup aufbauen**.

## 1. Was wir fertigen wollen (EVT, Menge 1–3 Sets)

| Board | Outline | Lagen | Prozessbedarf |
|---|---|---|---|
| Mainboard | 210 × 92 mm | **12** | **HDI** (Microvia/Via-in-Pad, Impedanzkontrolle) |
| HyperRF | 136 × 72 mm | TBD | HDI wahrscheinlich (RF + FPGA-BGA) |
| RF-Core | 92 × 66 mm | TBD | RF, kontrollierte Impedanz |
| UI-Carrier | 218 × 100 mm | TBD | Standard |
| M.2-Bridge | 30 × 52 mm | TBD | Standard |
| Antenna-Rail | 150 × 18 mm | TBD | RF |

Details: [`BOARD_SET.md`](BOARD_SET.md).

## 2. Präzise Fragen an PCBWay (bitte um Rückmeldung)

### Stackup (Mainboard, 12-Layer HDI)
1. **Empfohlener 12-Layer-HDI-Stackup** für RK3576 + LPDDR5 + PCIe 2.1 ×1 + USB3 + RF-Referenzen (bevorzugt mit Microvia-Aufbau, z.B. 2+N+2 oder 3+N+3)?
2. **Kontrollierte Impedanz:** machbar für Single-Ended **50 Ω** und Differential **90 Ω** (USB2/GbE) und **100 Ω** (PCIe/USB3/MIPI-DSI)? Zugehörige Linien-/Abstandswerte pro Lage?
3. **Microvia:** min. Laser-Via-Durchmesser, Capture-Pad, Stacked/Staggered, Via-in-Pad (gefüllt/geplant) für BGA-Escape?
4. **Min. mechanisches Via / Ringbreite / Aspect-Ratio** in eurem HDI-Prozess?
5. **Min. Trace/Space** (Innen-/Außenlagen) für BGA-Escape (RK3576, FPGA-BGA)?

### Prozess / Material
6. Material-Empfehlung (Standard-FR4 vs. Low-Loss für RF/PCIe) — Vorschlag + Dk/Df?
7. Oberfläche: **ENIG** (Präferenz) — bestätigt für Feinpitch-BGA?
8. Kupfergewicht Innen/Außen-Vorschlag für +5V_SYS (10 A transient)?

### DFM / Prüfung
9. **X-Ray + AOI** für BGA-PCBA verfügbar (EVT-Menge)?
10. Impedanz-Coupon + Stackup-Report im Lieferumfang?
11. Panelisierung/Nutzen-Empfehlung für 1–3 Sets?

## 3. Was wir liefern (sobald Schaltplan/Layout stehen)
Gerber (RS-274X), NC-Drill, IPC-Netlist, Stackup-Vorgabe (nach eurem Vorschlag), Impedanz-Ziele, Fab-Notes, ggf. CPL/BOM für PCBA.

## 4. Bezug / Sponsoring
Open-Source-Projekt; PCBWays öffentliches Sponsoring-/Open-Source-Programm wird angefragt. **Kein bestehendes Partnerschafts-/Zusageverhältnis** — dies ist eine Erst-Anfrage in der Outreach-Phase.

## 5. Randbedingungen (aus Master-Spec, nicht verhandelbar)
- Mainboard **12 Lagen** (kein 6-Layer).
- PCIe **2.1 ×1** (kein Gen3 ×4).
- RF-Fenster **metallfrei** (Thermik/Antennen-Constraint).
- LPDDR5-Topologie + UFS-MPN sind noch **HOLD** → Speicher-Routing erst nach Freigabe (beeinflusst finalen Stackup-Bedarf; bitte in der Stackup-Empfehlung berücksichtigen).
