# Sheet 16 — Debug / Recovery

Debug-Zugänge und Anti-Brick-Pfade für beide Rechner (RK3576 + RP2350B). Bring-up-kritisch.

## RK3576
| Netz | Funktion | Status |
|---|---|---|
| `DBG_UART_TX/RX` | serielle Konsole (früher Log) | FIXED-Absicht |
| `JTAG_*` / `SWD_*` | On-Chip-Debug | TARGET |
| `MASKROM_n` | Maskrom-Recovery erzwingen (Sheet 06) | FIXED |
| `RK_RESET_n` | System-Reset | FIXED |

## RP2350B
| Netz | Funktion | Status |
|---|---|---|
| `RP_SWD_IO/CLK` | Cortex-M33-Debug | FIXED-Absicht |
| `RP_BOOTSEL` | USB-BOOTSEL (DFU) | FIXED |
| `RP_RUN_n` | Reset | FIXED |
| `RP_USB_D_P/N` | RP2350-eigener USB (DFU/Recovery) | TARGET |

## Kritische Design-Notizen
- **Getrennte Recovery-Wege:** RK3576-Maskrom **und** RP2350-BOOTSEL unabhängig erreichbar → nie beide gleichzeitig gebrickt.
- **RP2350 kann RK3576-Recovery anstoßen** (`CMD_RECOVERY`, [ONE-X-Link](../../../firmware/rp2350/PROTOCOL.md)) — Reset/BootSel-Verdrahtung dazu (Sheet 13).
- **Debug-Header:** kompakter Tag-Connect/Pad-Footprint für UART+SWD/JTAG (EVT), nicht bestückt in Serie.
- **Konsolen-UART** immer herausgeführt (Testpunkte) — wichtigstes Bring-up-Werkzeug (G01/Core-Boot).
- **Schutz:** Debug-Pins in Serie/Pull, damit Feld-Sicherheit gewahrt (kein offener JTAG in Serie ohne Bedacht).

## ERC-Absicht
Debug-Busse konsistent; Reset/BootSel eindeutig; Header-Pins als reguläre Signale mit Pulls; unbestückte Optionen als DNP markiert.

## HOLD / TBD
- JTAG vs. SWD-only am RK3576 (Package/Referenz) 📄.
- Serien-Debug-Sicherheitsstrategie (Fuse/Disable) 📄.
