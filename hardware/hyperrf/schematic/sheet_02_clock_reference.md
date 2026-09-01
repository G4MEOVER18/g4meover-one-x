# HyperRF Sheet 02 — Takt / Referenz

Gemeinsame Frequenzreferenz + Verteilung für **kohärenten** Betrieb beider LMS7002M, plus GNSS-PPS-Eingang und die Timestamping-Kopplung zum FPGA. `hyperrf.timing`: „10 MHz Referenz + GNSS-Zeitpuls + FPGA-Timestamping".

## Referenz + Verteilung

| Netz | Rolle | Status |
|---|---|---|
| `REF_10M` | 10 MHz-Systemreferenz (TCXO/OCXO-Klasse) | TARGET |
| `REF_CLK_A` / `REF_CLK_B` | verteilte Referenz an LMS A / B | TARGET |
| `LO_COH_*` | gemeinsame/verkoppelte LO- bzw. Sampling-Takte für Kohärenz | TARGET |
| `PPS_IN` | GNSS-Sekundenpuls (aus Sheet 06 GNSS-Modul) | TARGET |
| `FPGA_TS_CLK` | Timestamping-Takt/-Referenz zum FPGA | **HOLD → G04** (FPGA-Seite) |

## Kohärenz (Kern-Alleinstellungsmerkmal)
- **Gemeinsame Referenz + phasenstabile Verteilung** an beide LMS7002M, damit 4RX/4TX **kohärent** samplen (`hyperrf.sdr` „coherent-capable").
- **Clock-Fanout mit geringem Skew** (Verteilbaustein) statt Daisy-Chain; gleiche Leitungslängen A/B.
- Ob LO-Sharing oder nur gemeinsame Sampling-Referenz → Kohärenz-Konzept = TBD 📄 (EVT-Entscheidung, Freeze G09).

## Timestamping
- `PPS_IN` (GNSS) + `REF_10M` → **FPGA-Timestamping** (Sample-genaue Zeitstempel). Die FPGA-seitige Erfassung/Pins hängen am FPGA-MPN → **HOLD → G04**. Die Referenz-/PPS-Erzeugung selbst ist hier design-bar.

## Kritische Design-Notizen
- **Phasenrauschen** der Referenz bestimmt die SDR-Güte → rauscharmer TCXO/OCXO; saubere, rauscharme Versorgung (Sheet 01 `HRF_1V8_ANA`).
- **Skew-Matching** der Verteilleitungen A/B (Kohärenz).
- **Isolation** der Taktleitungen von Schaltreglern/Digital-IF.

## ERC-Absicht
`REF_10M` als Single-Source-Takt; Verteilausgänge genau ein Treiber je Ziel; `PPS_IN` ein Treiber (GNSS) → FPGA; FPGA-seitige Taktnetze als Platzhalter bis G04.

## HOLD / TBD
Referenz-Typ (TCXO/OCXO) + Phasenrausch-Ziel 📄 · Kohärenz-Konzept (LO-Share vs. Sampling-Ref) 📄 (→ G09) · **FPGA-Timestamping-Interface HOLD → G04**.
