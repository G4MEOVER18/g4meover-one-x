# Manufacturing Readiness Review (MRR) — ONE-X EVT

Ehrlicher Reifegrad je Release-Gate ([`../docs/ROADMAP.md`](../docs/ROADMAP.md)). Legende: 🟢 bereit · 🟡 in Arbeit/Entwurf · 🔴 HOLD (blockiert, extern zu schließen).

| Gate | Inhalt | Reife | Wer schließt | Was fehlt konkret |
|---|---|---|---|---|
| **G01** | 5″-DSI-Display-Bringup | 🟡 | wir (Devboard) | HW-Nachweis; DT-Skelett steht ([`../linux/`](../linux/)) |
| **G02** | 16-GB-LPDDR5-Topologie | 🔴 | **Minewing** + Rockchip-Ref | Rockchip-gestützte Topologie/MPN; nicht routen bis bestätigt |
| **G03** | 256-GB-UFS-Teil | 🔴 | **Minewing** + RK3576-Host-Val. | validiertes UFS-Device (Gen/MPN) für RK3576-Host |
| **G04** | HyperRF-FPGA-MPN | 🔴 | wir + **Minewing** | Scored-Candidate-Matrix → Freeze (I/O, SERDES, PCIe-EP, BRAM, DSP, Power, Verfügbarkeit) |
| **G05** | DW3000-UWB-Suffix | 🔴 | wir + **Minewing** | konkretes Suffix wählen (nicht SR150) |
| **G06** | 12-Layer-HDI-Stackup/DFM | 🔴 | **PCBWay** | Stackup, Microvia-Struktur, Impedanz-Machbarkeit, Min.-Via/Ring |
| **G07** | Produktions-Schaltplan ERC | 🟡 | wir + Minewing-Review | Schaltplan-Entwurf (Phase 5, in Arbeit) → ERC clean |
| **G08** | Layout DRC/SI/PI | 🔴 | wir + Minewing-Review | nach G02/G03/G06; Impedanz, Return-Path, Länge/Skew, IR-Drop |
| **G09** | RF-EVT-Tuning | 🔴 | wir (EVT-Messung) | Matching auf realer HW (nicht aus Simulation) |
| **G10** | Thermal-Validierung | 🔴 | wir + Minewing | reale Fan-P/Q-Kurven, 3D-CFD/Mess-EVT (2D-Precheck ersetzt) |
| **G11** | Akku-Pack-Compliance | 🔴 | **Minewing** + Zellhersteller | UN38.3, BMS/Sicherung/NTC, mech. Schutz |

## Kernaussage
- **Vor Fertigung zwingend zu schließen (Reihenfolge):** G02/G03 (Speicher) + G06 (Stackup) → G07 (Schaltplan) → G08 (Layout) → dann erst Gerber/CPL.
- **Grund für kein-Gerber-jetzt:** G02/G03/G04/G06 sind HOLD. Diese Werte zu raten würde ein Board erzeugen, das SI/PI/Boot nicht besteht. Der RFQ-Weg schließt sie mit Herstellerdaten.

## Was JETZT weitergebbar ist (dieses Paket)
🟢 Board-Set (Outlines/Lagen/Schnittstellen), BOM mit Status, Power-Tree-Absicht, Interface-Matrix, mechanische Referenz, präzise DFM-/Sourcing-Fragen an beide Partner.

## Forbidden-Claims-Guard (aus Master-Spec — nie behaupten)
Kein IP-Rating (vor Validierung) · kein PCIe Gen3 ×4 · kein DC–60-GHz-/general-purpose-60-GHz-SDR · kein Zynq-UltraScale+ (bis FPGA frozen) · kein UWB-SR150 · kein GNSS L1/L2/L5 (Ziel L1/L5) · keine 10+ SMA · **kein** 6-Layer-Mainboard · UFS/LPDDR5 **nicht** produktionsbestätigt.
