# Sheet 07 — USB-C (PD / USB3 / DP-Alt)

USB-C-Haupt-Port: Power-Delivery-Eingang, USB3-Daten und DisplayPort-Alt-Mode. Interface-Matrix: **FIXED** (USB3 + DP-Alt + PD); PD-Controller-Konfiguration ist Implementierungsarbeit (TARGET).

## Kern-Bauteile

| Ref | Bauteil | Rolle | Status |
|---|---|---|---|
| U302 | TI TPS25751A | USB-C-PD-Controller (Source/Sink, 5–20 V) | TARGET |
| J-USBC | USB-C-Buchse (24-pin) | Port | FIXED-Absicht |
| (Mux) | USB3/DP-Alt-Mux/Redriver | Orientierung + DP-Alt | TARGET |

## Netze / Signale

| Netz | Funktion | Ziel | Status |
|---|---|---|---|
| `VBUS_C` | Bus-Spannung (5–20 V neg.) | → Charger (Sheet 01) | TARGET |
| `CC1/CC2` | Configuration Channel | TPS25751A | FIXED |
| `USB3_TX_P/N`, `USB3_RX_P/N` | USB3.x-SuperSpeed | RK3576 (Sheet 03) | FIXED |
| `USB2_D_P/N` | USB2 | RK3576 | FIXED |
| `DP_LANE0..3_P/N`, `DP_AUX_P/N` | DisplayPort-Alt | RK3576 DP → Mux | FIXED |
| `SBU1/2` | Sideband (DP-Alt/AUX) | Mux | FIXED |
| `PD_INT_n`, `PD_I2C_*` | PD-Controller-Steuerung | RK3576/RP2350 | TARGET |

## Power-Bezug (Sheet 01)
- `VBUS_C` → BQ25792-Charger-Eingang; PD verhandelt bis 20 V / bis 5 A (Controller-Fähigkeit).
- Einschalt-/Verpolungsschutz + TVS/ESD am Port.

## Kritische Design-Notizen
- **Orientierung/Flip:** USB-C ist steckbar in beide Richtungen → Mux/Redriver für USB3+DP-Alt; `CC`-basierte Orientierungserkennung über TPS25751A.
- **DP-Alt-Mode:** RK3576-DP-Ausgang über Mux auf die USB-C-Lanes; Konfiguration (2-lane/4-lane DP vs. USB3) im PD-Controller festlegen (`CMD`/config, TARGET).
- **SI:** USB3 (100 Ω diff) + DP-Lanes impedanzkontrolliert, AC-Kopplung, kurze Stichleitungen; ESD nah am Connector (Kapazität beachten).
- **PD-EVM-Checkliste** von TI abarbeiten (Konfiguration, Flash-Config des TPS25751A).
- **Testpunkte:** `VBUS_C`, `CC1/2`, `PD_INT_n` (→ Sheet 18).

## ERC-Absicht
`VBUS_C` als Power-Output Richtung Charger; Datenpaare als reguläre Signale mit `_P/_N`; PD-I²C mit Pull-Ups. ESD/TVS als No-ERC-Impact-Bauteile korrekt geflaggt.

## HOLD / TBD
- Genaue DP-Lane-Zahl (2 vs. 4) + gleichzeitiger USB3-Betrieb → RK3576-DP-Fähigkeit prüfen 📄.
- TPS25751A-Flash-Konfiguration (Rollen, Spannungen) → PD-Design.
