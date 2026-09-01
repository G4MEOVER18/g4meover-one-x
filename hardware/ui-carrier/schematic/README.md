# ONE-X UI-Carrier — Schaltplan

UI-Carrier-Board (218 × 100 mm) — trägt Display-FPC, kapazitiven Touch, die physischen Bedienelemente (Touch-Ring, D-Pad, 5 Softkeys), Haptik und Status-LEDs. Gleiche Design-Spec-Methodik wie [Mainboard](../../mainboard/schematic/README.md): reviewbare Sheets, HOLD sichtbar, ERC-Absicht.

## Zwei-Domänen-Prinzip (wichtig)

Das Board bündelt zwei getrennte Anbindungen zum Mainboard über **einen** Verbinder `J_UI`:

| Domäne | Signale | Ziel-Silizium | Spec |
|---|---|---|---|
| **Anzeige/Touch** | 4-lane MIPI-DSI, Backlight, Touch-I²C+IRQ | **RK3576** (Linux-Framebuffer) | `display.*` (FIXED) |
| **Bedienung/Haptik** | Touch-Ring, D-Pad, 5 Softkeys, Haptik, Status-LEDs | **RP2350** (System-Manager) | `rp2350` „power/wake/buttons/…/haptics; **NOT main Linux framebuffer**" |

> **Design-Grundsatz:** Tasten/Ring/Haptik hängen bewusst am **RP2350** (funktioniert auch ohne Linux/vor Boot — Wake, Recovery, RF-Kill-Bestätigung). Nur Anzeige + kapazitiver Touch gehen an den RK3576. Der Carrier führt beide Domänen physisch, ohne sie zu vermischen.

## Sheet-Index

| # | Sheet | Kern | Status |
|---|---|---|---|
| 01 | Display / DSI | 4-lane MIPI-DSI-Durchführung (FPC), Backlight-Boost, Panel-Power/Reset | FIXED (Signale) / Timings TBD 📄 |
| 02 | Touch | kapazitiver Touch I²C + IRQ (GT911-Klasse) | FIXED (Bus) / MPN TARGET |
| 03 | Eingabe: Ring / D-Pad / Softkeys | Touch-Ring-AFE, D-Pad, 5 Softkeys → RP2350; Entprellung/ESD | TARGET (AFE-MPN TBD 📄) |
| 04 | Haptik / Status-LED / Connector | Haptik-Treiber, Status-LEDs, `J_UI` zum Mainboard | TARGET / Pinout TBD 📄 |

## Panel-Kandidat

`display.panel_candidate` = **Waveshare 5-DSI-TOUCH-B / äquivalent 5″ 720×1280 DSI**, ILI9881C-Klasse + GT911-Klasse, aktive Fläche ~110,4 × 62,1 mm. DSI-Init-Sequenz/Timings = TBD 📄 (Datenblatt; siehe `linux/panel/PANEL_CANDIDATE.md`, Bringup-Gate **G01**).

## Netz-Konventionen
Wie Mainboard. Zusätzlich: `DSI0_{CLK,D0..D3}_{P,N}` (diff), `TP_INT`/`TP_RST` (Touch), `KEY_<name>`, `RING_<seg>`, `HAPTIC_PWM`, `LED_<name>`.

## Statusdisziplin
Anzeige/Touch-**Bus** FIXED aus Spec; Panel-/Touch-**MPN** TARGET (Freeze mit Bringup G01). Ring-AFE + Softkey-Entprellung TARGET (MPN TBD). Keine DSI-Timings raten — die stehen erst nach Datenblatt/G01 fest.
