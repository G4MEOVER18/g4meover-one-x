# ONE-X HyperRF — Schaltplan

HyperRF-Board (136 × 72 mm, HDI + RF) — das Wideband-SDR-Subsystem: **2× LMS7002M** (kohärent 4RX/4TX), High-Band-Conversion, **FPGA** (MPN **HOLD → G04**), plus Modul-Bays (5G/NTN/LoRa-Sat/GNSS), UWB und 60-GHz-Radar-Kachel. Gleiche Design-Spec-Methodik wie [Mainboard](../../mainboard/schematic/README.md) und [RF-Core](../../rf-core/schematic/README.md).

## Partitionierung nach Abhängigkeit (wichtig)

Das Board ist bewusst so geschnitten, dass die **FPGA-Unbekannte (G04)** isoliert bleibt. Alles, was nicht vom FPGA-MPN abhängt, ist hier als Design-Spec ausgearbeitet; der FPGA selbst ist ein **Platzhalter-Sheet** (wie LPDDR5/UFS im Mainboard).

| Abhängig von G04 (FPGA-MPN)? | Sheets |
|---|---|
| **Nein** — jetzt ausgearbeitet | 01 Power · 02 Takt/Referenz · 03/04 LMS7002M A/B · 05 High-Band · 06 Modul-Bays · 07 UWB/Radar |
| **Ja** — Platzhalter bis G04 | 08 FPGA (PCIe-EP + DSP/Channelization + LMS-Digital-IF) |

## Sheet-Index

| # | Sheet | Kern | Status |
|---|---|---|---|
| 01 | Power | `HYPERRF_AUX_5V` (5 A) → Point-of-Load-Rails für RF/Analog/Module | Architektur ✅ / FPGA-Rails TBD 📄 |
| 02 | Takt / Referenz | 10 MHz-Ref + Verteilung, kohärente LO/Sampling-Sync, GNSS-PPS | TARGET |
| 03 | LMS7002M A | SDR-RFIC A, 4RX/4TX-Frontend, Power-Seq, Digital-IF | TARGET |
| 04 | LMS7002M B | SDR-RFIC B, kohärent zu A | TARGET |
| 05 | High-Band-Conversion | 3,8→6 GHz via Up/Down-Conversion + Filter | TARGET |
| 06 | Modul-Bays | 5G / NTN / LoRa-Sat / GNSS (modul-basiert) | TARGET |
| 07 | UWB / Radar | DW3000 (Suffix **HOLD → G05**) + 60-GHz-Radar-Kachel | HOLD / TARGET |
| 08 | **FPGA** (Platzhalter) | PCIe-2.1-x1-EP + DSP/Channelization + LMS-Digital-IF | **⛔ HOLD → G04** |

## Bandgrenzen (Spec, nicht überschreiten)

| Aussage | Status | Quelle |
|---|---|---|
| LMS7002M nativ ~100 kHz–3,8 GHz | VALIDATED_ARCH | `hyperrf.native_sdr_range` |
| Erweiterung 100 kHz–6 GHz via High-Band-Translation/Filter | **TARGET** | `hyperrf.extended_sdr_target` |
| **Kein** allgemeiner 60-GHz-SDR | FIXED | `hyperrf.not_claimed` (Radar = separate Kachel, kein SDR) |
| Host-Link nur **PCIe 2.1 ×1** → FPGA muss dezimieren/kanalisieren | FIXED | `hyperrf.host_limit` |

## Netz-Konventionen
Wie Mainboard. Zusätzlich: `LMSx_{RX,TX}<n>_{P,N}` (Analog-RF diff), `LMSx_LML_*` (Digital-IF), `REF_10M`, `LO_COH_*`, `PPS_IN`, `HYPERRF_AUX_5V`, `HRF_<rail>`.

## Statusdisziplin
SDR-Kette TARGET (Kohärenz/High-Band-Freeze auf EVT); UWB-Suffix HOLD (G05); FPGA-MPN HOLD (G04, siehe [`../fpga-selection/`](../fpga-selection/)). RF-Matching auf realer HW (G09). **Kein** FPGA-Bauteil, kein 60-GHz-SDR, keine 6-GHz-Nativ-Behauptung.
