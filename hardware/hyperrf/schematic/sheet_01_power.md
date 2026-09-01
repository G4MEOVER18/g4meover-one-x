# HyperRF Sheet 01 — Power

Lokales Power-Tree des HyperRF-Boards. Eingang ist `HYPERRF_AUX_5V` (bis 5 A) vom Mainboard über die M.2-Bridge (Mainboard Sheet 12/17, M.2-Bridge Sheet 02). Point-of-Load-Regler erzeugen die RF-/Analog-/Digital-Rails **lokal** (kurze, saubere Versorgung nah an den RFICs).

## Eingang

| Netz | Rolle | Status |
|---|---|---|
| `HYPERRF_AUX_5V` | Haupteinspeisung (bis 5 A), aus Mainboard | FIXED (Signal) |
| `GND` | massive Rückführung | FIXED |

## Point-of-Load-Rails (Architektur ✅, Werte TBD 📄)

| Rail | Zweck | Typ | Status |
|---|---|---|---|
| `HRF_1V8_DIG` | LMS7002M Digital / IO | Buck | Architektur ✅ / Wert TBD 📄 |
| `HRF_1V2_TX` | LMS7002M TX-Analog | LDO (rauscharm) | TBD 📄 |
| `HRF_1V2_RX` | LMS7002M RX-Analog | LDO (rauscharm) | TBD 📄 |
| `HRF_1V8_ANA` | Analog/PLL-Referenz | LDO | TBD 📄 |
| `HRF_3V3` | Module/GNSS/UWB/Aux | Buck | TBD 📄 |
| `HRF_FPGA_*` | **FPGA-Core/IO/Transceiver** | — | **HOLD → G04** (Rail-Zahl/Spannungen erst mit FPGA-MPN) |

> **Grundsatz:** RF-Analog-Rails **rauscharm** (LDO nach Vor-Buck), getrennt von Digital-Schaltreglern; jede LMS-Rail lokal entkoppelt. Die exakten Spannungen/Toleranzen kommen aus den LMS7002M-/Modul-Datenblättern (TBD 📄), die FPGA-Rails erst nach G04.

## Sequencing (Design-Absicht)
- **Digital vor Analog** bzw. nach RFIC-Vorgabe (LMS7002M-Power-Up-Order beachten, Datenblatt).
- FPGA-Sequencing (falls MPN es fordert) = TBD 📄 nach G04.
- **RF-Kill-Bezug:** Kein PA/TX-Pfad bekommt Strom vor gültiger Freigabe — der subsystemübergreifende Kill (RF-Core Sheet 01) gilt auch für HyperRF-PAs.

## Kritische Design-Notizen
- **IR-Drop** auf `HYPERRF_AUX_5V` (5 A) — genug Kupfer/Kontakte über die M.2-Bridge; Sense/Entkopplung am Boardeingang.
- **Thermik:** HyperRF hat getrennte Wärmeableitung (Spec `thermal.architecture`); Regler-Verlustleistung in die Budget-Rechnung (G10).
- **Rauschtrennung:** Schaltregler-Rückpfade weg von RX-Analog; Guard/Partitionierung.

## ERC-Absicht
Jede Rail als Power-Netz mit genau einer Quelle; `HYPERRF_AUX_5V` mit Strom-Annotation; FPGA-Rails als benannte Platzhalter (No-Connect bis G04).

## HOLD / TBD
Rail-Spannungen/Toleranzen (LMS/Modul-Datenblätter) 📄 · **FPGA-Rails HOLD → G04** · Sequencing-Delays 📄 · Regler-MPNs (TARGET).
