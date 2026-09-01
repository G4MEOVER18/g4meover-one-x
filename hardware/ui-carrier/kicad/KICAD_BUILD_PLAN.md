# KiCad-Bauplan — ui-carrier

> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.
> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der
> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).

## Hierarchie
- Root-Sheet `ui-carrier.kicad_sch` instanziiert **4** Sub-Sheets.
- Root-UUID (fix): `892ab209-16d5-585f-ab6b-5acb3bb567e5`

## Sub-Sheets (Reihenfolge + Global-Labels)

| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |
|---|---|---|---|---|
| 01 | `sheet_01_display_dsi.kicad_sch` | UI-Carrier Sheet 01 — Display / MIPI-DSI | `BL_EN`, `BL_PWM`, `DSI0_CLK_P`, `DSI0_D0..D3_P`, `LCD_RST_n`, `TP_INT`, `TP_RST`, `VLCD_3V3` | zeichnen |
| 02 | `sheet_02_touch.kicad_sch` | UI-Carrier Sheet 02 — Kapazitiver Touch | `TP_INT`, `TP_RST`, `TP_SCL`, `TP_SDA`, `VDD_TP_3V3` | zeichnen |
| 03 | `sheet_03_input_ring_dpad_keys.kicad_sch` | UI-Carrier Sheet 03 — Eingabe: Touch-Ring / D-Pad / Softkeys | — | zeichnen |
| 04 | `sheet_04_haptic_status_connector.kicad_sch` | UI-Carrier Sheet 04 — Haptik / Status-LED / Connector | `LCD_RST_n`, `TP_SCL`, `TX_GATE_OK`, `VLCD_3V3` | zeichnen |

## Regeln
- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus
  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).
- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).
- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.
- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.
