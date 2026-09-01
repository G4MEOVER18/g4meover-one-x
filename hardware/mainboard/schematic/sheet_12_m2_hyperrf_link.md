# Sheet 12 — M.2 / HyperRF-Link

Brücke Mainboard ↔ **HyperRF-Modul** über die M.2-Bridge (30 × 52 mm). Trägt **PCIe 2.1 ×1 + USB3** (Interface-Matrix **FIXED**). **Kein PCIe Gen3 ×4** (Forbidden Claim).

## Schnittstellen

| Netz | Funktion | Quelle/Ziel | Status |
|---|---|---|---|
| `PCIE_TX_P/N`, `PCIE_RX_P/N` | PCIe 2.1 ×1 | RK3576 (Sheet 03) ↔ HyperRF-FPGA | FIXED |
| `PCIE_REFCLK_P/N` | 100-MHz-Referenz | RK3576/Clockgen | FIXED |
| `PCIE_PERST_n`, `PCIE_CLKREQ_n`, `PCIE_WAKE_n` | PCIe-Steuerung | — | FIXED |
| `USB3_M2_TX_P/N`, `USB3_M2_RX_P/N` | USB3 (5G/HyperRF) | RK3576 | FIXED |
| `USB2_M2_D_P/N` | USB2-Fallback | RK3576 | FIXED |
| M.2-Sideband | `I2C`, `GPIO`, `PCIE_PERST_n`, `LED` | RK3576/RP2350 | TARGET |

## Power / Arbitrierung
- HyperRF versorgt sich über `HYPERRF_AUX_5V` (Sheet 01, 5 A) + ggf. lokale Regler auf dem HyperRF-Board.
- **Bandbreiten-/Power-Arbitrierung nötig** (Interface-Matrix): PCIe 2.1 ×1 kann die rohe 4-Kanal-SDR-Bandbreite **nicht** kontinuierlich streamen → FPGA-Dezimierung/Channelization (HOLD-FPGA, Gate G04) reduziert die Datenrate.

## Kritische Design-Notizen
- **PCIe SI:** 100 Ω diff, `REFCLK`-Jitter, AC-Kopplung im TX-Pfad, Länge/Skew, Return-Path über durchgehende Referenz-Plane (Layout G08).
- **USB3 SI:** 100 Ω diff, Redriver falls Länge kritisch.
- **Steckverbinder:** M.2-Key + mechanische Halterung; Pinbelegung an das gewählte HyperRF-Interface anpassen (kein Standard-M.2-NGFF-Zwang, da custom Modul) 📄.
- **FPGA-Abhängigkeit:** finale PCIe-Endpoint-Fähigkeit hängt am FPGA (G04, HOLD) — Lane-Count/Gen bleibt 2.1 ×1 fixiert, aber Endpoint-IP/Timing erst nach FPGA-Freeze.
- **Testpunkte/Bring-up:** `PCIE_PERST_n`, `PCIE_REFCLK`, Link-LED (→ Sheet 18).

## ERC-Absicht
Differentielle Paare konsistent `_P/_N`; PCIe-Steuernetze eindeutig; `HYPERRF_AUX_5V` als Power-Input am Connector. Kein Doppel-Treiber auf `REFCLK`.

## HOLD / TBD
- **FPGA-PCIe-Endpoint** (G04) — bestimmt Timing/IP.
- Genaue **M.2-Pinbelegung** des Custom-Moduls 📄.
- Redriver ja/nein (nach Layout-Länge).
