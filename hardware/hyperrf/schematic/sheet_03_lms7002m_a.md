# HyperRF Sheet 03 — LMS7002M A (SDR-RFIC A)

Erster der beiden LMS7002M-Transceiver — 4RX/4TX-Architektur, nativ ~100 kHz–3,8 GHz. Analog-RF-Frontend, Power-Sequencing, digitale IQ-Schnittstelle zum FPGA.

## Analog-RF (diff, 50 Ω-Referenz)

| Netz | Rolle | Status |
|---|---|---|
| `LMSA_RX1..4_P/N` | 4× RX-Eingänge (diff) | TARGET |
| `LMSA_TX1..4_P/N` | 4× TX-Ausgänge (diff) | TARGET |
| `LMSA_ANT_*` | Antennen-/Frontend-Routing (Balun/Filter/Schalter) | TARGET |

- **Balun/Matching** je RX/TX-Pfad (LMS ist differenziell); Werte = TBD 📄, getunt auf realer HW (**G09**).
- **Frontend-Schalter/Filter** Richtung Antenna-Rail-Feeds bzw. High-Band-Conversion (Sheet 05); Bandaufteilung = TBD 📄.
- **TX-PA-Enables** laufen über den subsystemübergreifenden **RF-Kill** (RF-Core Sheet 01) — kein verdeckter TX-Pfad.

## Digitale IQ-Schnittstelle (LML) — FPGA-Seite HOLD

| Netz | Rolle | Status |
|---|---|---|
| `LMSA_LML_*` | Parallel-LVDS IQ-Bus (DDR) zum FPGA | LMS-Seite design-bar / **FPGA-Seite HOLD → G04** |
| `LMSA_SPI_*` | Konfig-SPI | TARGET |
| `LMSA_RESET_n` | Reset | TARGET |

> Lane-Zahl/Modus (SISO/MIMO, SDR/DDR) bestimmt die LML-Breite — das ist zugleich Knockout **K2** der FPGA-Auswahl ([`../fpga-selection/REQUIREMENTS.md`](../fpga-selection/REQUIREMENTS.md)). Die FPGA-seitige Pin-Zuordnung bleibt HOLD bis G04; die LMS-Seite (Bus-Struktur, Terminierung) ist hier ausgearbeitet.

## Power (aus Sheet 01)
`HRF_1V2_TX` / `HRF_1V2_RX` (rauscharm) / `HRF_1V8_DIG` / `HRF_1V8_ANA`. **Power-Up-Order** nach LMS7002M-Datenblatt = TBD 📄. Lokale Entkopplung je Rail nah am RFIC.

## Takt (aus Sheet 02)
`REF_CLK_A` + `LO_COH_*` — phasenstabil zu LMS B (Kohärenz).

## Kritische Design-Notizen
- **RX-Empfindlichkeit:** RX-Analog rauscharm versorgen, weg von Digital-IF/Schaltreglern; Guard/Partition.
- **LVDS-Terminierung** + Skew des LML-Busses (SI-Review G08).
- **Kanalisolation** zwischen den 4 Pfaden und zu LMS B.

## ERC-Absicht
RX/TX als diff-Paare (ein Treiber je Richtung); LML als terminierter Bus; SPI/Reset eindeutig; Rails Power-Flags; FPGA-seitige LML-Pins Platzhalter bis G04.

## HOLD / TBD
Balun/Matching-Werte (→ G09) · Bandaufteilung/Frontend-Schaltung 📄 · LML-Breite/Modus 📄 · Power-Up-Order 📄 · **FPGA-seitige LML-Pins HOLD → G04**.
