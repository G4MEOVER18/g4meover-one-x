# Panel-/Touch-Kandidat — 5″ 720×1280 DSI

> **Status:** EVT-Referenz **TARGET**, Produktions-Klasse **TARGET**, Init/Timings **HOLD**.
> Diese Datei sammelt Datenpunkte für G01. Werte, die nicht mit Quelle belegt sind, bleiben **TBD** — nicht raten.

## Kandidat (EVT)

| Feld | Wert | Status | Quelle |
|---|---|---|---|
| EVT-Referenzmodul | Waveshare 5-DSI-TOUCH-B (oder äquivalentes 5″ 720×1280 DSI) | TARGET | Master-Spec `display.evt_reference` |
| Display-IC-Klasse | ILI9881C-Klasse | TARGET | Master-Spec `display.production_reference_class` |
| Touch-IC-Klasse | GT911-Klasse (Goodix) | TARGET | Master-Spec `display.production_reference_class` |
| Aktive Fläche | ca. 110,4 × 62,1 mm | TARGET | Master-Spec (Produktionsklasse) |
| Sichtbares Fenster (Mechanik) | 112,5 × 64,5 mm | FIXED | Master-Spec `mechanical.visible_display_window_mm` |
| Auflösung | 720×1280 (Portrait), Landscape per SW-Rotation | FIXED | Master-Spec `display.resolution_native` |
| Host-Interface | 4-lane MIPI-DSI | FIXED | Master-Spec `display.host_interface` |

## Für den Device-Tree benötigte Datenblatt-Werte (📄 = aus Panel-Datenblatt setzen, TBD bis dahin)

| Parameter | Symbol | Wert | Status |
|---|---|---|---|
| Pixelclock | `clock-frequency` | TBD | HOLD 📄 |
| H aktiv / V aktiv | `hactive`/`vactive` | 720 / 1280 | FIXED |
| H front/back/sync | `hfront-porch`/`hback-porch`/`hsync-len` | TBD | HOLD 📄 |
| V front/back/sync | `vfront-porch`/`vback-porch`/`vsync-len` | TBD | HOLD 📄 |
| DSI-Lanes | `dsi,lanes` | 4 | FIXED |
| DSI-Modus | Video/Command, Burst/Non-Burst | TBD | HOLD 📄 |
| Init-Sequenz | Panel-spezifische DCS-Kommandos | TBD | HOLD 📄 |
| Versorgung | VCC / IOVCC Spannungen | TBD | HOLD 📄 |
| Reset-Timing | t_reset, Power-Sequencing | TBD | HOLD 📄 |
| Backlight | PWM-Frequenz / Regler | TBD | HOLD 📄 |

## Treiber-Optionen (zu prüfen gegen BSP)

1. **Generischer ILI9881C-Treiber** (`ilitek,ili9881c`, `drivers/gpu/drm/panel/panel-ilitek-ili9881c.c`) — falls das Modul-Timing/Init dazu passt, minimaler Aufwand.
2. **`panel-simple`** mit expliziter `display-timing`-Node — nur wenn keine speziellen DCS-Init nötig sind (bei ILI9881C meist doch).
3. **Dediziertes Panel-DTS-Init-Array** — Init-Sequenz als `panel-init-sequence` (Rockchip-`panel-simple-dsi`/`rockchip,panel`-Erweiterung) direkt im Overlay.

> Welche Option gilt, entscheidet das **reale Panel-Datenblatt** + der DRM-Test aus der [Bringup-Checkliste](../BRINGUP_CHECKLIST_G01.md) Abschnitt 3–4.

## Offene Fragen (G01)
- Native Panel-Orientierung bestätigt Portrait (720 breit)? → Landscape-UI ausschließlich per SW-Rotation (Spec-FIXED).
- Touch-I²C-Adresse + IRQ/Reset-Pinning des konkreten Moduls?
- Backlight über SoC-PWM oder On-Modul-Regler?
