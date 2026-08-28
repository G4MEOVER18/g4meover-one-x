# Sheet 09 — HDMI / DP-Out

Externer Video-Ausgang des RK3576 (zusätzlich zum internen 5″-DSI-Panel und zum USB-C-DP-Alt in Sheet 07). Status: Video-Out FIXED-Absicht; genaue Ausführung (HDMI vs. dediziertes DP) TARGET.

## Netze

| Netz | Funktion | Status |
|---|---|---|
| `HDMI_TX0..2_P/N`, `HDMI_CLK_P/N` | TMDS-Lanes + Clock | FIXED-Absicht |
| `HDMI_HPD` | Hot-Plug-Detect | FIXED |
| `HDMI_CEC` | CEC | TARGET |
| `HDMI_DDC_SCL/SDA` | EDID/DDC | FIXED |
| `+5V_HDMI` | Connector-5V (begrenzt) | TARGET |

## Kritische Design-Notizen
- **ESD/Level:** TMDS mit ESD-Schutz (geringe Kapazität) nah am Connector; HPD/CEC/DDC mit Pegel-/Pull-Beschaltung.
- **SI:** TMDS 100 Ω diff, Längenabgleich, Referenz-Plane; kurze Stichleitungen.
- **Quelle klären:** ob HDMI nativ vom RK3576 oder über DP→HDMI-Bridge 📄 (RK3576-Video-Out-Fähigkeit prüfen — Anzahl gleichzeitiger Displays: DSI + HDMI + DP-Alt).
- **Testpunkte:** `HDMI_HPD`, `DDC` (→ Sheet 18).

## ERC-Absicht
TMDS-Paare `_P/_N`; DDC als I²C; HPD/CEC als Signale; `+5V_HDMI` als begrenzter Power-Output.

## HOLD / TBD
- **Gleichzeitige Display-Pfade:** DSI (intern) + HDMI + USB-C-DP-Alt — max. Anzahl/Kombination aus RK3576-VOP-Fähigkeit 📄.
- HDMI nativ vs. DP-Bridge.
