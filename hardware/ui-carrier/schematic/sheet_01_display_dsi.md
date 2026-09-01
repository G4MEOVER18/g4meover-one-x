# UI-Carrier Sheet 01 — Display / MIPI-DSI

4-lane-MIPI-DSI-Anbindung des 5″-Panels, direkt vom RK3576 (über `J_UI`/`J_DSI` durchgeführt). Backlight-Boost, Panel-Power-Sequencing, Reset.

## Signale (aus `display.*`, FIXED)

| Netz | Rolle | Status |
|---|---|---|
| `DSI0_CLK_P/N` | DSI-Taktpaar (diff, ~80 Ω single / 100 Ω diff) | FIXED |
| `DSI0_D0..D3_P/N` | 4 Datenlanes (diff) | FIXED |
| `TP_INT` / `TP_RST` | Touch-IRQ / Reset (zu Sheet 02) | FIXED |
| `LCD_RST_n` | Panel-Reset | FIXED |
| `BL_EN` / `BL_PWM` | Backlight-Enable / Dimming-PWM | FIXED |
| `VLCD_3V3` | Panel-Logik-Rail | FIXED |
| `VBL` | Backlight-LED-String-Versorgung (Boost) | TARGET |

## Panel-Kandidat
Waveshare 5-DSI-TOUCH-B-Klasse (ILI9881C-Klasse), 720×1280, aktive Fläche ~110,4×62,1 mm. **DSI-Init-Sequenz, Lane-Timings, Backlight-String (V/I)** = TBD 📄 (Datenblatt, Freeze mit **G01**).

## Backlight
- **Boost-Treiber** (LED-String) mit `BL_EN` + `BL_PWM`-Dimming; String-Spannung/Strom = TBD 📄 (Panel-abhängig).
- PWM-Frequenz so, dass kein sichtbares Flimmern + keine DSI-/RF-Störung.

## Power-Sequencing
`VLCD_3V3` vor DSI-Aktivität; `LCD_RST_n` nach stabiler Versorgung freigeben; Backlight erst nach gültigem Videostrom (kein Weißblitz). Exakte Reihenfolge/Delays = Panel-Datenblatt (G01).

## Kritische Design-Notizen
- **Impedanz + Längenmatching** der DSI-Paare (intra-pair Skew klein); Rückpfad durchgehend (Layout-Review G08).
- **FPC-Führung** kurz, definierte Masse; Steckerhöhe gegen Gehäuse-Bauraum (Mechanik).
- **ESD** an FPC-Signalen (Panel wird berührt).

## ERC-Absicht
DSI-Paare als diff-Netze (ein Treiber = RK3576), `VLCD_3V3`/`VBL` Power-Flags, `LCD_RST_n`/`BL_*` eindeutig getrieben.

## HOLD / TBD
DSI-Init-Sequenz + Timings 📄 · Backlight-String V/I 📄 · Panel-MPN-Freeze (TARGET → G01).
