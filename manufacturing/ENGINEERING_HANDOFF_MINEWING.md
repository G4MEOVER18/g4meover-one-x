# Engineering-Handoff — Minewing (JDM/ODM)

**Projekt:** G4MEOVER ONE-X · **Stand:** EVT / Engineering-Review · **EVT-Menge:** 1–3 Einheiten.
**Rolle (angefragt):** JDM/ODM-Engineering-Partner — Schaltplan-/Layout-Review, SI/PI, DFM, **Sourcing/Validierung der HOLD-/TARGET-Teile**, Mechanik/Thermal, EVT-Build.

> **Kein bestehendes Partnerschafts-/Zusageverhältnis** — Erst-Anfrage in Outreach-Phase.

## 1. Wo wir eure Hilfe am dringendsten brauchen (die HOLD-Gates)

Diese Punkte blockieren die Fertigung und brauchen **Herstellerdaten**, die wir bewusst nicht raten:

| Gate | Thema | Konkreter Sourcing-/Validierungs-Auftrag |
|---|---|---|
| **G02** | 16 GB LPDDR5 | Rockchip-**RK3576-gestützte** LPDDR5-Topologie + qualifizierte MPN benennen (Kapazität FIXED 16 GB; Topologie HOLD). Referenz-Training/-Layout? |
| **G03** | 256 GB UFS | Für RK3576-UFS-Host **validiertes** UFS-Device (Generation/MPN). Public-Host-Spec: UFS 2.0. |
| **G04** | HyperRF-FPGA | Kandidaten mit **PCIe-2.1-Endpoint + DSP/Channelization** vorschlagen; Bewertung nach I/O, SERDES, BRAM, DSP, Power, **Verfügbarkeit/Lieferzeit**. |
| **G05** | UWB | Qorvo **DW3000-Serie**: konkretes, beziehbares Suffix (nicht SR150). |
| **G11** | Akku-Pack | 2S2P 4× 21700 (72-Wh-Klasse): Pack-Engineering + **UN38.3**, BMS/Sicherung/NTC, mech. Schutz, Zertifizierung. |

## 2. Review-Umfang (Schaltplan/Layout)
- **Schaltplan-Entwurf** entsteht im Repo ([`../hardware/schematic/`](../hardware/schematic/), Phase 5). Bitte **ERC-/Design-Review** (Gate G07).
- **Layout (Gate G08):** SI/PI-Review — LPDDR5 (nach G02), PCIe 2.1 ×1/USB3, RGMII, MIPI-DSI, kontrollierte Impedanz, Return-Path, Länge/Skew, IR-Drop (+5V_SYS 10 A transient).
- **DFM** gemeinsam mit PCBWay-Stackup (G06).

## 3. Mechanik / Thermal
- Gehäuse-Referenz: [`../mechanical/`](../mechanical/) (CadQuery, 230×110×64, EVT-Kollisionsmodell).
- **Thermal (Gate G10):** duale Low-Profile-Blower + getrennte Spreader/Vapor-Chamber (Main/HyperRF), RF-Fenster metallfrei. Bisher nur 2D-Precheck → **reale P/Q-Kurven + 3D-CFD/Mess-EVT** nötig.
- **Akku-Tray** für 2S2P 4× 21700.

## 4. BOM
[`BOM_EVT.csv`](BOM_EVT.csv) — Status je Position (FIXED/TARGET/HOLD), Sourcing-Owner, zugehöriges Gate. Bitte:
- HOLD-Positionen: konkrete, beziehbare MPN + Datenblatt + Verfügbarkeit vorschlagen.
- TARGET-Positionen: Suffix-Freeze + Alternativen (Second-Source) vorschlagen.
- FIXED-Positionen: Verfügbarkeit/Lieferzeit bestätigen.

## 5. EVT-Build
- **1–3 Einheiten**, gestaffelter Power-Up-Bringup (erst Power/Core-Boot, dann Display G01, dann RF-Kette).
- Test-/Bring-up-Punkte und Recovery (RP2350-DFU) sind vorzusehen.

## 6. Randbedingungen (aus Master-Spec)
Mainboard 12-Layer-HDI · PCIe 2.1 ×1 (kein Gen3 ×4) · kein IP-Rating-Claim (EVT) · RF-Hard-Kill hardware-erzwungen · Regulierungsprofile für Sendefunktionen. Nichts darf der [Master-Spec](../spec/) widersprechen; Werte sind unabhängig gegen Datenblätter zu verifizieren (`imported_under_review`).
