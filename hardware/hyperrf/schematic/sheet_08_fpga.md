# HyperRF Sheet 08 — FPGA (⛔ Platzhalter — HOLD → G04)

> **Dieses Sheet ist bewusst NICHT ausgearbeitet.** Der FPGA-MPN ist **HOLD** (`hyperrf.fpga`); er wird über die Scored Candidate Matrix in [`../fpga-selection/`](../fpga-selection/) und **Gate G04** gewählt. Genau wie die Mainboard-Sheets 04 (LPDDR5) / 05 (UFS) bleibt hier alles Herstellerspezifische offen, statt geraten. Forbidden-Claim: **kein** „Zynq UltraScale+", solange nicht explizit eingefroren.

## Rolle des FPGA (FIXED, unabhängig vom MPN)

| Funktion | Spec |
|---|---|
| **PCIe-2.1-x1-Endpoint** zum RK3576-Host | `hyperrf.host_limit` (FIXED) |
| **DSP / Channelization / Dezimation** vor dem Host-Link | `hyperrf.host_limit` — rohe 4-Kanal-Bandbreite nicht kontinuierlich streambar |
| **Digitale IQ-Anbindung** beider LMS7002M (LML-LVDS) | Sheets 03/04 |
| **Timestamping** (10 MHz + PPS) | Sheet 02 / `hyperrf.timing` |

## Was zum Schließen von G04 (und damit dieses Sheets) gebraucht wird
1. `../fpga-selection/CANDIDATE_MATRIX.csv` mit Datenblatt-/Verfügbarkeitswerten füllen → `score.py` → Gewinner.
2. Nach Freeze: Rail-Map (→ Sheet 01 `HRF_FPGA_*`), Bank-/IO-Zuordnung für LML (→ Sheets 03/04), PCIe-EP-Config/RefClk-Modus (→ M.2-Bridge Sheet 01), Timestamping-Pins (→ Sheet 02).
3. Erst dann wird dieses Sheet als vollwertiges Schaltplan-Sheet gezeichnet.

## Platzhalter-Netze (Namen stehen, Zuordnung HOLD)
`HRF_FPGA_*` (Rails) · `LMSA_LML_*` / `LMSB_LML_*` (Digital-IF) · PCIe-EP kanonisch `PCIE_TX_P/N`, `PCIE_RX_P/N`, `PCIE_REFCLK_P/N`, `PCIE_PERST_n`, `PCIE_CLKREQ_n`, `PCIE_WAKE_n` (siehe [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md)) · `FPGA_TS_CLK` (Timestamping) · `FPGA_CFG_*` (Konfig/Boot).

## Status
**⛔ HOLD → G04.** Kein MPN, kein Pinout, keine Rails geraten.
