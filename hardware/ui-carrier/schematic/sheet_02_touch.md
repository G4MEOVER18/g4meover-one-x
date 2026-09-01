# UI-Carrier Sheet 02 — Kapazitiver Touch

Kapazitiver Multitouch-Controller (GT911-Klasse) am I²C-Bus des RK3576 mit Interrupt + Reset. Der Touch bedient die **Anzeige-Domäne** (Linux), nicht die physischen Tasten (Sheet 03).

## Signale (aus `display.touch_interface`, FIXED-Bus)

| Netz | Rolle | Status |
|---|---|---|
| `TP_SCL` / `TP_SDA` | I²C zum RK3576 | FIXED |
| `TP_INT` | Touch-Interrupt (aktiv-low, edge) | FIXED |
| `TP_RST` | Touch-Controller-Reset | FIXED |
| `VDD_TP_3V3` | Touch-Rail | FIXED |

## Controller
GT911-Klasse (5″, 720×1280, aktive Fläche ~110,4×62,1 mm). **I²C-Adresse, Init-Register, Reset-/INT-Timing** = TBD 📄 (Datenblatt; oft adressabhängig von `TP_INT/TP_RST`-Pegel während Reset → Boot-Sequenz beachten).

## Kritische Design-Notizen
- **Adress-Strapping:** GT911-Klasse wählt I²C-Adresse über `INT`/`RST`-Pegel beim Reset — Reset-Sequenz definieren (Bezug G01-Bringup).
- **Pull-ups** an `TP_SCL/SDA` (ein Satz pro Bus; Doppel-Pull-up vermeiden, falls Bus geteilt).
- **ESD** an `SCL/SDA/INT` (berührte Oberfläche).
- **Verlegung** von INT/RST kurz, entkoppelt vom DSI-Takt.

## ERC-Absicht
I²C als bidirektionales Netz mit genau einem Pull-up-Satz; `TP_INT` ein Treiber (Controller) → RK3576-GPIO; `VDD_TP_3V3` Power-Flag.

## HOLD / TBD
I²C-Adresse + Init-Register 📄 · Reset/INT-Timing 📄 · Touch-MPN-Freeze (TARGET → G01).
