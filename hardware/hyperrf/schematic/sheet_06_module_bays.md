# HyperRF Sheet 06 — Modul-Bays (5G / NTN / LoRa-Sat / GNSS)

Vier **modul-basierte** Funkfunktionen als steckbare/bestückbare Bays — Versorgung, Host-Interface, Antennen-Feed, Steuerung. Alle **TARGET** (Modul-MPNs Klassen, Freeze auf EVT).

## Bays (Klassen aus Spec)

| Bay | Klasse (Spec) | Interface | Status |
|---|---|---|---|
| **5G** | Quectel RM530N-GL-Klasse (Sub-6 + mmWave-Bay) | M.2/USB3+PCIe je Modul | TARGET |
| **NTN** | Quectel BG95-S5-Klasse (3GPP Rel-17 IoT-NTN) | UART/USB | TARGET |
| **LoRa-Sat** | Semtech LR1121-Klasse (sub-GHz/2,4/L/S) | SPI | TARGET |
| **GNSS** | u-blox NEO-F10N-Klasse (**L1/L5**, Raw + Zeitpuls) | UART/I²C + `PPS_IN` | TARGET |

> **Statusehrlich:** GNSS ist **L1/L5** (nicht L1/L2/L5 — Forbidden-Claim). 5G-mmWave nur als **Bay**, nicht als Fähigkeitszusage. Modul-MPNs = Klassen, nicht eingefroren.

## Gemeinsame Anbindung
| Netz | Rolle |
|---|---|
| `HRF_3V3` / modul-spezifische Rails | Versorgung (Sheet 01) |
| `<bay>_HOST_*` | UART/SPI/USB/PCIe je Bay zum Host/FPGA |
| `<bay>_ANT` | Antennen-Feed (Antenna-Rail / eigene Antenne) |
| `PPS_IN` | GNSS-Sekundenpuls → Sheet 02 (Timestamping) |
| `<bay>_EN` / SIM (5G/NTN) | Enable / SIM-Anbindung |

## Kritische Design-Notizen
- **SIM** (5G/NTN): SIM-Halter/eSIM + ESD; Führung zur Modul-Bay.
- **Antennen:** 5G/mmWave-Antennenführung ist kritisch (mmWave sehr verlustempfindlich) — Detailkonzept TBD 📄 (Antennen-/Mechanik-Abstimmung).
- **Power-Spitzen** (5G-TX-Bursts) im Budget berücksichtigen (Sheet 01 / Thermik G10).
- **TX-Module** ebenfalls unter der RF-Kill-Policy (Freigabe mit Regulierungsprofil).
- **GNSS-`PPS`** rauscharm zu Sheet 02 führen.

## ERC-Absicht
Jede Bay als Modul-Footprint mit eigenem Enable/Power-Flag; Host-Bus eindeutig; ungenutzte Modul-Pins No-Connect; `PPS_IN` ein Treiber.

## HOLD / TBD
Modul-MPNs (TARGET-Freeze EVT) · 5G/mmWave-Antennenkonzept 📄 · SIM-Typ/-Führung 📄 · Bay-Interface je Modul (M.2/USB/UART) 📄.
