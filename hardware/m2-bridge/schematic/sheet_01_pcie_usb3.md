# M.2-Bridge Sheet 01 — High-Speed (PCIe 2.1 ×1 / USB3)

Die High-Speed-Diff-Paare über den M.2-B-Key-Connector. Host = RK3576 (Mainboard `J_M2`, Sheet 12); Endpoint = HyperRF-FPGA (Gate G04).

## Signale (FIXED)

| Netz | Rolle | Impedanz-Ziel |
|---|---|---|
| `PETx0_P/N` | PCIe TX (Host→EP), AC-gekoppelt | 85 Ω diff |
| `PERx0_P/N` | PCIe RX (EP→Host) | 85 Ω diff |
| `PE_REFCLK_P/N` | 100 MHz PCIe-Referenztakt | 85–100 Ω diff |
| `USB3_SSTX_P/N` | USB3 SuperSpeed TX, AC-gekoppelt | 90 Ω diff |
| `USB3_SSRX_P/N` | USB3 SuperSpeed RX | 90 Ω diff |
| `USB2_DP/DM` | USB2 (Fallback/Sideband, wo geroutet) | 90 Ω diff |

## AC-Kopplung
- **PCIe TX** + **USB3 TX** AC-gekoppelt (Serien-Cs am Sender-Ende). Werte = TBD 📄 (Spec-üblich, im SI-Review G08 bestätigen).
- RX-Seite je nach EP-Anforderung.

## RefClk
- PCIe-2.1-RefClk 100 MHz differenziell; **Common-Clock oder SRIS** = TBD 📄 (hängt von FPGA-EP-IP ab, G04). `PCIE_CLKREQ_n` in Sheet 02.

## Kritische Design-Notizen
- **Kurz + impedanzkontrolliert:** Brücke bewusst klein (30×52) → kurze HS-Längen; Rückpfad durchgehend, Referenzlage massiv.
- **Längen-/Skew-Matching** intra-pair eng; TX/RX-Paare untereinander toleranter.
- **Kein Gen3 ×4** — nur ×1, Gen2-Rate (PCIe 2.1). ERC-/Design-Review-Guard.
- **ESD** an USB3/USB2 (steckbare/externe Nähe je nach Einbau).

## ERC-Absicht
Alle HS-Netze als diff-Paare mit genau einem Treiber je Richtung; AC-Cs in Serie im TX-Pfad; RefClk als diff-Quelle (ein Treiber).

## HOLD / TBD
AC-Kondensatorwerte 📄 · RefClk-Modus (Common-Clock/SRIS) 📄 (→ FPGA-EP, G04) · Längen/Impedanz-Freeze (→ SI-Review G08) · M.2-Steckertyp/-höhe 📄.
