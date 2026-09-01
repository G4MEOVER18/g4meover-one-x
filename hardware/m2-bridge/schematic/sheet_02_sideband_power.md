# M.2-Bridge Sheet 02 — Sideband / Power / Testpoints

PCIe-Sideband, Versorgungen (inkl. `HYPERRF_AUX_5V`-Durchführung) und Testpunkte.

## Sideband (FIXED-Signale)

| Netz | Rolle |
|---|---|
| `PCIE_PERST_n` | PCIe-Reset vom Host (RK3576) an den EP |
| `PCIE_CLKREQ_n` | Clock-Request (EP→Host / bidir je Modus) |
| `PCIE_WAKE_n` | Wake vom EP an den Host |
| `M2_CONFIG/RSVD` | M.2-Konfig-Pins je B-Key-Definition | 

Reset-/CLKREQ-/WAKE-Verhalten koppelt an den FPGA-EP (G04) und die RK3576-PCIe-Controller-Config.

## Power
| Rail | Rolle | Status |
|---|---|---|
| `+3V3` | M.2-Logik/Referenz | FIXED |
| `HYPERRF_AUX_5V` | **Durchführung** zum HyperRF (bis 5 A), aus Mainboard Sheet 12/17 | FIXED (Signal) / Strom-Pinbudget TBD 📄 |
| `GND` | massive Rückführung | FIXED |

- **`HYPERRF_AUX_5V`:** hoher Strom → genug Kontakte/Kupfer am Connector; nicht über die HS-Paare stören. IR-Drop prüfen (Layout G08).
- Entkopplung an `+3V3` nahe EP.

## Testpoints (→ Sinn wie Mainboard Sheet 18)
`PCIE_PERST_n`, `PCIE_CLKREQ_n`, `PCIE_REFCLK`, `+3V3`, `HYPERRF_AUX_5V` — für gestaffelten Bring-up messbar.

## Kritische Design-Notizen
- **Power-vor-Reset-Sequenz:** `+3V3`/`HYPERRF_AUX_5V` stabil, dann `PCIE_PERST_n` freigeben (EP-Enumeration).
- **Fehlsteckschutz:** Bridge-Stecker eindeutig kodiert (anderer Typ als `J_UI`/`J_RFCORE`).

## ERC-Absicht
Sideband eindeutig getrieben; Rails als Power-Flags; Hochstrom-Rail mit Strom-annotierten Netzen; ungenutzte M.2-Pins No-Connect.

## HOLD / TBD
`HYPERRF_AUX_5V`-Kontakt-/Strombudget 📄 · Reset/CLKREQ/WAKE-Timing (→ FPGA-EP, G04) · M.2-B-Key-Pin-Mapping-Freeze 📄.
