# ONE-X M.2-Bridge — Schaltplan

M.2-Bridge-Board (30 × 52 mm) — die **High-Speed-Brücke** zwischen Mainboard und HyperRF: **PCIe 2.1 ×1 + USB3** (FIXED; **kein** Gen3 ×4). M.2 B-Key. Gleiche Design-Spec-Methodik wie [Mainboard](../../mainboard/schematic/README.md).

## Zweck
Trennt das High-Speed-Interface physisch als steckbare/kurze Brücke, damit HyperRF (136×72, HDI/RF) und Mainboard mechanisch/thermisch entkoppelt bleiben, aber die schnelle Datenverbindung impedanzkontrolliert kurz bleibt.

| Interface | Spec | Status |
|---|---|---|
| PCIe **2.1 ×1** | `host_hs`/`hyperrf.host_limit` — FPGA-Endpoint am HyperRF, Host = RK3576 | FIXED |
| USB3 (SS) | `M.2 B-Key … USB3/USB2 where routed` | FIXED |
| **NICHT** Gen3 ×4 | Forbidden-Claim | — |

## Sheet-Index

| # | Sheet | Kern | Status |
|---|---|---|---|
| 01 | High-Speed (PCIe/USB3) | M.2-B-Key-Connector, PCIe-×1-Diff, USB3-SS, RefClk, AC-Kopplung | FIXED (Signale) |
| 02 | Sideband / Power / Testpoints | PERST/CLKREQ/WAKE, Rails, `HYPERRF_AUX_5V`-Durchführung, TPs | FIXED / TBD 📄 |

## Netz-Konventionen
Wie Mainboard. `PERx_P/N` (PCIe RX), `PETx_P/N` (PCIe TX), `PE_REFCLK_P/N`, `USB3_SSRX/SSTX_P/N`, `PCIE_PERST_n`, `PCIE_CLKREQ_n`, `PCIE_WAKE_n`.

## Statusdisziplin
Signale FIXED; **M.2-Steckertyp/-höhe** und **AC-Kondensatorwerte/Längen** = TBD 📄 (Layout/SI-Review, Gate G08). Kein Gen3, kein ×4.
