<div align="center">

# G4MEOVER ONE-X

**Der Overkill-Linux-Handheld für Research, Pentest und Funktechnologie.**
Ein Gerät für absolut alles — von 125 kHz LF-RFID bis 6 GHz SDR, von Zigbee bis 5G/NTN.

`ein Vokabular · jedes Gerät seine Stärke · alles an einem Punkt`

Revision **EVT6** · Status **Architektur synchronisiert / Engineering-Phase** · Lizenz **CERN-OHL-S 2.0 (HW) + MIT (SW/Docs)**

</div>

---

> **Warum dieses Projekt existiert.** Der [Flipper One](https://www.cnx-software.com/2026/05/21/flipper-one-a-rockchip-rk3576-powered-portable-arm-linux-computer-and-networking-multi-tool/) wurde im Mai 2026 angekündigt (RK3576, ~350 $) — aber die Auslieferung zieht sich, und er ist bewusst **klein**: 2,4″-Display, kein SDR-Kraftpaket, kein Touch-Tablet. **G4MEOVER ONE-X** nimmt dieselbe SoC-Klasse und geht in eine völlig andere Liga: 5″-Touch-Linux, 16 GB RAM, ein echtes **HyperRF-SDR (100 kHz–6 GHz, 4RX/4TX)**, Dual-Gigabit-Ethernet, 72-Wh-Akku und ein vollständiger RF-Zoo (Sub-GHz, NFC/RFID, Zigbee/Thread/Z-Wave, 5G/NTN, GNSS, UWB, 60-GHz-Radar). **Es gibt derzeit nichts Vergleichbares als integriertes Gerät.**

## Inhaltsverzeichnis

- [Das Gerät in einem Satz](#das-gerät-in-einem-satz)
- [Vergleich: ONE-X vs. Flipper One vs. Flipper Zero](#vergleich)
- [Kernspezifikation](#kernspezifikation)
- [Architektur](#architektur)
- [Status-Modell (die eiserne Regel)](#status-modell)
- [Repository-Struktur](#repository-struktur)
- [Roadmap & Release-Gates](#roadmap--release-gates)
- [Präsentation](#präsentation)
- [Mitmachen / Sponsoring](#sponsoring)
- [Sicherheit, Recht & verantwortungsvolle Nutzung](#sicherheit--recht)
- [Lizenz](#lizenz)

---

## Das Gerät in einem Satz

G4MEOVER ONE-X ist ein **modularer Linux-Handheld** (230 × 110 × 64 mm, 800–950 g) auf Basis des **Rockchip RK3576**, mit einem **5″-Multitouch-Display**, einem eigenständigen **RP2350B-Systemcontroller**, einem protokollorientierten **RF-Core** und einem hochleistungsfähigen, modularen **HyperRF-Funk-Subsystem** — gebaut für Elektronik, Netzwerktechnik, RF-Forschung, Automatisierung und Feld-Diagnose.

---

## Vergleich

| | **G4MEOVER ONE-X** | Flipper One (angek.) | Flipper Zero |
|---|---|---|---|
| **SoC** | RK3576 (Octa-Core A72/A53) | RK3576 | STM32WB55 (MCU) |
| **RAM** | 16 GB LPDDR5 | 8 GB | 256 KB |
| **Display** | **5,0″ IPS Multitouch 1280×720** | 2,4″ 256×144 | 1,3″ 128×64 mono |
| **OS** | Vollwertiges Debian-/Linux | Linux | Proprietäre MCU-FW |
| **SDR** | **HyperRF 100 kHz–6 GHz, 4RX/4TX (2× LMS7002M)** | — | — |
| **Sub-GHz** | CC1101 + SX1262 | CC1101-Klasse | CC1101 |
| **NFC/RFID** | PN7160 + 125 kHz LF + UHF RAIN (E710) | 13,56 MHz | 13,56 MHz + 125 kHz |
| **Mesh/IoT** | Zigbee/Thread/BLE + Z-Wave (LR) | teilw. | — |
| **Mobilfunk** | **5G Sub-6 + mmWave + NTN-Satellit** | — | — |
| **GNSS** | u-blox L1/L5 raw + PPS | — | — |
| **UWB / Radar** | DW3000 + 60-GHz-FMCW-Radar | — | — |
| **Netzwerk** | **2× Gigabit Ethernet**, Wi-Fi 6E, USB3, HDMI | 2× GbE, Wi-Fi 6E | — |
| **Akku** | 4× 21700, 2S2P, ~72 Wh | intern | 2000 mAh |

> Zahlen zu Flipper One stammen aus der öffentlichen Ankündigung (Mai 2026) und dienen der Einordnung, nicht dem Marketing gegen ein fremdes Produkt. Quellen siehe [`docs/COMPARISON_FLIPPER_ONE.md`](docs/COMPARISON_FLIPPER_ONE.md).

---

## Kernspezifikation

Die **verbindliche** Spezifikation ist [`spec/G4MEOVER-ONE-X_MASTER_SPEC.json`](spec/G4MEOVER-ONE-X_MASTER_SPEC.json) — die *Single Source of Truth*. Kein Dokument, keine Grafik, keine BOM und kein CAD darf ihr widersprechen.

| Domäne | Wert | Status |
|---|---|---|
| Gehäuse | 230 × 110 × 64 mm, 800–950 g | FIXED / TARGET |
| SoC | Rockchip RK3576 | FIXED |
| RAM | 16 GB LPDDR5 (Kapazität) | FIXED (Topologie HOLD) |
| Storage | 256 GB UFS (Kapazität) | FIXED (MPN HOLD) |
| Systemcontroller | RP2350B + 16 MB QSPI | FIXED |
| Display | 5,0″ IPS, 720×1280 nativ, 4-Lane MIPI DSI | FIXED (Panel-Bringup HOLD) |
| Akku | 2S2P 4× 21700, ~72 Wh (Molicel P50B) | VALIDATED_ARCH / TARGET |
| Netzwerk | 2× GbE, Wi-Fi 6E, USB-C PD/USB3/DP, USB-A, HDMI, M.2 (PCIe 2.1 ×1) | FIXED |
| RF-Core | CC1101, SX1262, CC2652P7, PN7160, LF-RFID, IR/1-Wire | FIXED |
| RF-Core (Target) | Z-Wave (EFR32ZG23), UHF RAIN (Impinj E710) | TARGET |
| HyperRF SDR | 2× LMS7002M, 4RX/4TX, 100 kHz–6 GHz | TARGET |
| HyperRF weitere | 5G/NTN, GNSS L1/L5, UWB, 60-GHz-Radar, LR1121 | TARGET |
| Mainboard | 210 × 92 mm, 12-Layer HDI | FIXED (Stackup HOLD) |

Vollständige Stückliste: [`spec/BOM.csv`](spec/BOM.csv).

---

## Architektur

```
                        ┌─────────────────────────────────────────────┐
                        │            5,0" IPS Multitouch DSI           │
                        └───────────────────┬─────────────────────────┘
                                  4-Lane MIPI DSI (direkt)
┌──────────────┐   I2C/UART/SPI   ┌─────────▼──────────┐   PCIe 2.1 ×1  ┌──────────────────┐
│  RP2350B     │◄────────────────►│   RK3576  (Linux)  │◄──────────────►│    HyperRF       │
│ System-MCU   │  Always-On-Bus   │  16 GB / 256 GB    │                │  FPGA + 2×LMS7002M│
│ Power·Tasten │                  │  Netz·USB·Storage  │                │  5G·NTN·GNSS·UWB │
│ Ring·Haptik  │                  │  RF-High-Level-SW  │                │  60-GHz-Radar    │
│ Fans·Watchdog│                  └───┬───────────┬────┘                └──────────────────┘
│ RF-Kill-Mon. │                      │           │
└──────────────┘        2× RGMII/GbE  │           │  I2C/SPI/UART
                        Wi-Fi6E·USB3·  │           ▼
                        HDMI·M.2       │      ┌─────────────┐
                                       │      │  RF-Core    │  CC1101·SX1262·CC2652P7
                                       │      │ (Low-Power) │  PN7160·LF-RFID·Z-Wave
                                       │      └─────────────┘  UHF-RAIN·IR·1-Wire
                                       ▼
                                 4× externe SMA (Antennen-Rail)
```

Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · Grafiken: [`docs/graphics/`](docs/graphics/).

---

## Status-Modell

Jede technische Aussage trägt einen Status. **Fehlende Herstellerdaten werden nicht erfunden** — sie werden als `HOLD` markiert.

| Status | Bedeutung |
|---|---|
| **FIXED** | Projektentscheidung. Nur per expliziter Change-Request änderbar. |
| **VALIDATED_ARCH** | Architektur durch Bauteil-/Interface-Fähigkeiten gestützt; Implementierung teils offen. |
| **TARGET** | Gewünschte Umsetzung; exaktes Teil/Wert kann sich ändern. |
| **HOLD** | **Nicht** produktionsbestätigt. Blocker muss geschlossen werden. |
| **DEFERRED** | In EVT6 bewusst nicht beansprucht/freigegeben. |

Verbotene Behauptungen (z. B. „PCIe Gen3 ×4", „DC-60 GHz SDR", „IP54 vor Validierung") stehen in der Master-Spec unter `claims_forbidden` und werden vom Validator geprüft:

```bash
python tools/spec_validator.py          # prüft Konsistenz & verbotene Claims, erzeugt derived docs
```

---

## Repository-Struktur

```
g4meover-one-x/
├── spec/            # Single Source of Truth (JSON) + BOM + Interface/Power-CSV
├── docs/            # Konzept, Architektur, Roadmap, Vergleich, Grafiken
├── tools/           # spec_validator.py (FIXED/TARGET/HOLD + forbidden-claim-Scan)
├── hardware/        # mainboard · ui-carrier · rf-core · hyperrf · m2-bridge · antenna-rail
├── firmware/rp2350/ # Always-On-Systemcontroller-Firmware (Architektur)
├── linux/           # Debian-/Linux-Plattform, Device-Tree, DRM-Bringup, ONE-X-UI
├── mechanical/      # CadQuery-Quelle, STEP/STL-Referenzen
├── validation/      # Geometrie-, Thermal-, Regressions-Checks
├── manufacturing/   # DFM, Stackup, EVT-Build-Prozess
├── providers/       # Sponsor-/Fertigungspartner: PCBWay, Minewing (Mails + Datenpakete)
├── branding/        # Marken-Tokens, Logo
├── presentation/    # Konzept-Präsentation
└── reference_evt6/  # eingefrorene EVT6-Handoff-Referenz
```

---

## Roadmap & Release-Gates

Der Weg von der synchronisierten Architektur (EVT6) zum echten EVT-Prototyp — ohne offene Herstellerdaten zu raten. Vollständig in [`docs/ROADMAP.md`](docs/ROADMAP.md).

| Gate | Inhalt | Status |
|---|---|---|
| **G01** | 5″-Display Linux/DSI-Bringup auf RK3576 | offen |
| **G02** | Exakte 16-GB-LPDDR5-Topologie | offen (HOLD) |
| **G03** | Exaktes 256-GB-UFS-Teil | offen (HOLD) |
| **G04** | HyperRF-FPGA-MPN-Freeze (quantitative Auswahl) | offen (HOLD) |
| **G06** | PCBWay 12-Layer-HDI-Stackup/DFM | **Sponsor-Kontakt aktiv** |
| **G07–G11** | Schaltplan-ERC · Layout-DRC/SI/PI · RF-EVT · Thermal · Akku-Compliance | offen |

---

## Präsentation

Die interaktive Konzept-Präsentation (theme-aware, mit Architektur-, RF-Abdeckungs- und Front-Layout-Diagrammen) liegt als eigenständige HTML-Seite unter [`presentation/index.html`](presentation/index.html) — im Browser öffnen. Sie fasst These, Vergleich, Architektur, Spektrum, Release-Gates und Sponsoren auf einer Seite zusammen.

---

## Sponsoring

Dieses Projekt ist **Open Source** und sucht Fertigungs-/Engineering-Partner. Zwei Kontakte sind bereits aktiv (vollständige Vorlagen + Datenpakete unter [`providers/`](providers/)):

- **[PCBWay](providers/pcbway/)** — bietet kostenloses PCB-Prototyping; ideal für **G06** (12-Layer-HDI-DFM, Stackup, Microvia/Via-in-Pad, Impedanz, BGA-Escape, X-Ray).
- **[Minewing](providers/minewing/)** — One-Stop-JDM/ODM (CN+VN, seit 2003); ideal für Schaltplan-Review, SI/PI, DFM, Komponenten-Sourcing, Mechanik/Thermal und EVT-Build.

Interesse an Mitarbeit (Linux/DRM, RF, FPGA, KiCad, Mechanik)? → Issues & Discussions.

---

## Sicherheit & Recht

ONE-X ist ein **Forschungs- und Diagnosewerkzeug**. Jede Sendefunktion:

- wird mit **regionalen Regulierungsprofilen** und sicheren Labor-Testmodi implementiert;
- besitzt einen **physischen TX/RF-Kill-Pfad**, den Software nicht übergehen kann;
- darf nur im gesetzlichen Rahmen und für autorisierte Zwecke betrieben werden.

Nutzung erfolgt in eigener Verantwortung und im Einklang mit lokalem Funk-, Datenschutz- und Fernmelderecht.

---

## Lizenz

- **Hardware** (Schaltpläne, Layouts, CAD, Gerber): **CERN-OHL-S 2.0**
- **Software & Firmware** (RP2350, Linux-Tools, `tools/`): **MIT**
- **Dokumentation & Grafiken**: **CC BY-SA 4.0**

Siehe [`LICENSE.md`](LICENSE.md). © 2026 Yanis Ameseder (G4MEOVER18).
