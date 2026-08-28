# G01 — 5″-DSI-Display-Bringup-Checkliste (RK3576)

Ziel: **5,0″ 720×1280 MIPI-DSI-Panel + I²C-Touch** auf RK3576 unter Linux (DRM/KMS) reproduzierbar zum Laufen bringen, inkl. Suspend/Resume — auf einem **Devboard**, unabhängig vom noch offenen ONE-X-Mainboard-Layout.

Gate G01 gilt erst als **geschlossen**, wenn alle Punkte mit ✅ real auf Hardware belegt sind (kein Simulations-/Papier-Nachweis). Bis dahin bleibt `display.driver_gate` in der Master-Spec **HOLD**.

Legende: ☐ offen · 🔧 benötigt Hardware/Messung · 📄 aus Datenblatt/BSP zu setzen (nicht raten)

---

## 0. Voraussetzungen
- ☐ RK3576-Devboard mit erreichbarem 4-lane-MIPI-DSI-Connector 🔧
- ☐ 5″ 720×1280 DSI-Panel (EVT-Referenz: Waveshare 5-DSI-TOUCH-B / äquiv., ILI9881C-Klasse) 🔧
- ☐ Panel-Datenblatt vorhanden (DSI-Timings, Init-Sequenz, Lane-Zahl, Spannungen, Reset-Timing) 📄
- ☐ Rockchip-BSP-Kernel (6.1-Klasse) oder Mainline mit RK3576-DSI/VOP-Support, Cross-Toolchain, Boot-Medium
- ☐ Serielle Debug-Konsole (früher Log ohne Display) 🔧

## 1. Panel-Stromversorgung & Reset
- ☐ VCC/IOVCC-Rails und Reset-GPIO am Devboard identifizieren 📄🔧
- ☐ Reset-Timing (t_reset, Power-Sequencing) aus Datenblatt notieren 📄
- ☐ Backlight-Pfad klären (PWM vs. konstant; separater Regler) 📄
- ✅-Kriterium: Panel-Rails messbar, Reset toggelt sauber (Oszi) 🔧

## 2. DSI-Lanes & PHY
- ☐ 4 Datenlanes + Clocklane elektrisch prüfen (Kontinuität, Impedanz grob) 🔧
- ☐ DSI-PHY-Frequenz aus Pixelclock ableiten: `f_pixel = 720×1280×60 + Blanking` → Bitrate/Lane 📄
- ☐ Node-Labels im RK3576-DTSI verifizieren (`&dsi*`, `&mipidcphy*`, `&vop*`) — **können vom RK3588 abweichen** 📄
- ✅-Kriterium: DSI-Controller probed ohne PHY-Fehler im dmesg

## 3. Device-Tree-Overlay
- ☐ `device-tree/rk3576-one-x-panel5.dtso` an Devboard anpassen: I²C-Bus-Nr., GPIOs, Panel-Compatible 📄
- ☐ Panel-Init-Sequenz aus Datenblatt eintragen (falls kein generischer `panel-simple`/`ilitek,ili9881c`-Treiber passt) 📄
- ☐ DSI-Timings (hactive/vactive/h-/v-front/back/sync) exakt aus Datenblatt 📄
- ☐ Overlay bauen (`make`) und beim Boot laden
- ✅-Kriterium: `modetest` listet den Connector als **connected** mit 720×1280

## 4. DRM/KMS-Modeset
- ☐ `modetest -M rockchip -s <conn>:<crtc>:720x1280` → Testbild sichtbar 🔧
- ☐ Farb-/Timing-Artefakte prüfen (Tearing, Shift, falsche Polarität) 🔧
- ☐ Bei Fehlbild: Lane-Reihenfolge, Sync-Polarität, PHY-Timing korrigieren 📄
- ✅-Kriterium: stabiles, korrektes Vollbild über ≥10 min

## 5. Rotation → Landscape (1280×720)
- ☐ SW-Rotation setzen (DRM plane/Compositor-Transform, **kein** natives Landscape-Panel)
- ☐ Weston/Wayland `transform=270` (o.ä.) → UI erscheint Landscape
- ✅-Kriterium: ONE-X-UI startet in 1280×720-Landscape, Touch-Achsen passen (siehe 6)

## 6. Touch (I²C)
- ☐ Touch-Controller am I²C erkennen (`i2cdetect`), Adresse + IRQ/Reset-GPIO 📄🔧
- ☐ `goodix`/passender Treiber lädt, `/dev/input/eventX` entsteht
- ☐ `evtest` → Koordinaten; Achsen-Mapping zur Rotation korrigieren (`touchscreen-swapped-x-y`, `-inverted-*`)
- ☐ RP2350-Rolle: **nur Wake-IRQ überwachen**, Touch-Datenpfad bleibt beim RK3576 (Spec-FIXED)
- ✅-Kriterium: Touch trifft Pixel-genau in Landscape

## 7. Suspend/Resume
- ☐ `echo mem > /sys/power/state` → Panel + Touch aus, Rails/Backlight korrekt runter 🔧
- ☐ Resume: Panel re-init, DRM-Restore, Touch-Re-Probe, kein Flackern/Hänger 🔧
- ☐ Wake-Quelle definieren (Touch-IRQ / Power-Taste über RP2350) — Datenpfad-Trennung wahren
- ✅-Kriterium: 20× Suspend/Resume-Zyklen ohne Fehler

## 8. Abschluss G01
- ☐ dmesg-Log (sauber), `modetest`-Dump, Foto Testbild, Suspend-Zyklen-Log in `validation/` ablegen
- ☐ Verifizierte Werte (Node-Labels, Timings, Pins, Panel-Compatible) ins Overlay committen
- ☐ **Master-Spec:** `display.driver_gate` von HOLD → VALIDATED_ARCH ändern (per Change-Request-Prozess in CLAUDE.md), Roadmap G01 → geschlossen
- ☐ `docs/AUTONOMOUS_WORKLOG.md` fortschreiben

> Erst wenn Abschnitt 8 vollständig ist, darf irgendein Artefakt das Display als „validiert" darstellen.
