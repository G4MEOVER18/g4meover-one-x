# Sheet 08 — USB-Host (USB-A)

Externer USB-Host-Port (USB-A) für Peripherie/Tools. RK3576 stellt USB-Host bereit; ggf. Hub, wenn mehr Ports als SoC-Controller. Status: TARGET (Port-Zahl/Hub nach Bauraum).

## Netze

| Netz | Funktion | Status |
|---|---|---|
| `USBA_SS_TX_P/N`, `USBA_SS_RX_P/N` | USB3-SuperSpeed | FIXED-Absicht |
| `USBA_D_P/N` | USB2 | FIXED |
| `USBA_VBUS` | Port-Power (geschaltet) | TARGET |
| `USBA_OC_n` | Overcurrent-Flag | TARGET |

## Power / Schutz
- `USBA_VBUS` über **Power-Switch mit Strombegrenzung** (`USBA_EN`/`USBA_OC_n`) aus `+5V_SYS` (Sheet 01).
- ESD/TVS nah am Connector; Ferrit/Bulk-Cap am VBUS.

## Kritische Design-Notizen
- **Hub (optional):** falls SoC-USB-Controller knapp → USB3-Hub; Power-Budget über `+5V_SYS` beachten.
- **SI:** USB3 100 Ω diff, kurze Stichleitungen, ESD-Kapazität gering halten.
- **Bring-up:** VBUS schaltbar (RP2350/RK3576) für Fehlersuche.
- **Testpunkte:** `USBA_VBUS`, `USBA_OC_n` (→ Sheet 18).

## ERC-Absicht
SS/HS-Paare `_P/_N`; VBUS-Switch als Power-Pfad; OC/EN als Signale mit Pulls.

## HOLD / TBD
- Port-Anzahl + Hub ja/nein (Bauraum) 📄.
- Gemeinsame vs. getrennte USB-Controller-Zuordnung (mit Sheet 07/12) 📄.
