# HyperRF Sheet 04 — LMS7002M B (SDR-RFIC B)

Zweiter LMS7002M — **strukturidentisch zu Sheet 03 (A)**, kohärent zu A getaktet. Ergibt zusammen mit A die kohärente 2× (4RX/4TX)-Architektur (`hyperrf.sdr`).

## Gleich wie Sheet 03 (nur Präfix `LMSB_`)
- Analog-RF: `LMSB_RX1..4_P/N`, `LMSB_TX1..4_P/N`, `LMSB_ANT_*` — Balun/Matching TBD 📄 (G09).
- Digital-IF: `LMSB_LML_*` (FPGA-Seite **HOLD → G04**), `LMSB_SPI_*`, `LMSB_RESET_n`.
- Power (Sheet 01), Takt (Sheet 02).
- TX-PA-Enables über subsystemübergreifenden **RF-Kill** (RF-Core Sheet 01).

## Unterschiede / Kohärenz-spezifisch

| Punkt | Anforderung |
|---|---|
| **Takt** | `REF_CLK_B` + `LO_COH_*` **phasenstarr/skew-gematcht zu A** — Voraussetzung für Kohärenz | 
| **LML-Bus** | eigener Bus zum FPGA (oder gemeinsamer, je Interface-Modus) — Aufteilung = TBD 📄 (G04-abhängig) |
| **Layout** | symmetrisch zu A (gleiche Leitungslängen der kohärenten Takte); Isolation A↔B |

## Kritische Design-Notizen
- **Kohärenz steht/fällt mit Takt-Skew** A↔B → identische Verteilung, gemeinsamer Fanout (Sheet 02).
- **Kanalisolation** A↔B (Übersprechen begrenzt Kohärenz-/Dynamik-Güte).
- Doppelter LML-Bus verdoppelt den FPGA-I/O-Bedarf → fließt in K2/S6 der FPGA-Auswahl ein.

## ERC-Absicht
Wie Sheet 03, Präfix `LMSB_`; kohärente Taktnetze mit definierter, zu A gespiegelter Führung.

## HOLD / TBD
Wie Sheet 03 · Kohärenz-Skew-Budget A↔B 📄 (→ G09) · LML-Bus-Aufteilung (gemeinsam/getrennt) 📄 (→ G04).
