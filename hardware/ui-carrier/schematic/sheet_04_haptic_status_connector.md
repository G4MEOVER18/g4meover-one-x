# UI-Carrier Sheet 04 — Haptik / Status-LED / Connector

Haptik-Treiber, Status-LEDs und der Sammel-Verbinder `J_UI` zurück zum Mainboard (Sheet 17).

## Haptik
| Netz | Rolle | Status |
|---|---|---|
| `HAPTIC_PWM` / `HAPTIC_EN` | Ansteuerung vom RP2350 | TARGET |
| `VHAPTIC` | Aktuator-Versorgung | TARGET |

- **Treiber:** LRA-/ERM-Haptik-Treiber (MPN TBD 📄). Aktuator-Typ (LRA vs. ERM) = TBD 📄 → bestimmt Resonanz/Ansteuerung.
- Freilauf/Snubber je nach Aktuator; RP2350 steuert (haptisches Feedback an Tasten/Ring).

## Status-LEDs
| Netz | Rolle |
|---|---|
| `LED_PWR` | Power/Charge-Status |
| `LED_RFKILL` | **RF-Kill aktiv** (rot) — gespiegelt aus `TX_GATE_OK`/RP2350-Telemetrie |
| `LED_ACT` | Aktivität/Funk-TX |

- **`LED_RFKILL` sicherheitsrelevant:** zeigt den physischen Kill-Zustand (Bezug RF-Core `sheet_01_supervisor_rfkill.md`, UI `linux/ui/`). Treiber-Quelle = RP2350 (nicht Linux), damit der Zustand auch ohne Linux korrekt leuchtet.
- Strombegrenzung je LED; Helligkeit blendfrei.

## Connector `J_UI` (zum Mainboard, Sheet 17)
Führt **beide Domänen** gebündelt:
- **RK3576-Domäne:** `DSI0_*` (diff), `TP_SCL/SDA/INT/RST`, `LCD_RST_n`, `BL_*`, `VLCD_3V3`.
- **RP2350-Domäne:** `KEY_*`, `RING_*`, `HAPTIC_*`, `LED_*`.
- **Power/Masse:** Rails + durchgehende Masse-Kontakte.

**Pin-Budget → Steckertyp/-höhe = TBD 📄** (nach Summierung aller Signale; Höhe gegen Gehäuse-Bauraum, Mechanik). Verpolungs-/Fehlsteckschutz + eindeutige Kodierung (anderer Typ als `J_RFCORE`/`J_M2`).

## Kritische Design-Notizen
- **Diff-Paare + langsame Signale getrennt führen** (DSI weg von PWM/Haptik-Störern).
- **Masse-Rückführung** an genug Kontakten für DSI-Rückpfad.
- Testpunkte an `LED_RFKILL`, `HAPTIC_EN`, Touch-Reset (→ Mainboard Sheet 18).

## ERC-Absicht
`J_UI` als Multi-Pin-Symbol mit exakt zum Mainboard gespiegelten Netznamen; Power-Kontakte als Power-Flags; ungenutzte Pins No-Connect.

## HOLD / TBD
Haptik-Treiber-/Aktuator-MPN 📄 · `J_UI`-Pin-Budget + Steckertyp/-höhe 📄 · LED-Bins (TARGET).
