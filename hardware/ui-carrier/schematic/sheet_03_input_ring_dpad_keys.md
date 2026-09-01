# UI-Carrier Sheet 03 — Eingabe: Touch-Ring / D-Pad / Softkeys

Die **physischen** Bedienelemente. Alle hängen am **RP2350** (System-Manager), nicht am RK3576 — damit Wake, Menü-Navigation vor Linux-Boot, Recovery und RF-Kill-Bestätigung ohne laufendes Linux funktionieren (`rp2350`: „buttons/… NOT main Linux framebuffer").

## Elemente (Geometrie FIXED aus `mechanical.*`)

| Element | Geometrie | Netze | Status |
|---|---|---|---|
| **Touch-Ring** | Ø40 mm (kapazitiv, segmentiert) | `RING_<seg>` / `RING_I2C` | TARGET (AFE-MPN TBD 📄) |
| **D-Pad** | 34×34 mm Envelope | `KEY_UP/DOWN/LEFT/RIGHT/CENTER` | FIXED (Geometrie) / TARGET |
| **5 Softkeys** | untere Reihe | `KEY_SK1..SK5` | FIXED (Anzahl) / TARGET |

## Touch-Ring
- **Kapazitiver Ring-AFE** (dedizierter Cap-Touch-Controller **oder** RP2350-eigene Touch-Sensing-Fähigkeit) — MPN/Architektur = TBD 📄. Anbindung an RP2350 (I²C **oder** direkte Sense-Pins).
- Segmentzahl/Auflösung = TBD 📄 (bestimmt Scroll-/Tuning-Feinheit; UI erwartet Ring als Dreh-/Scroll-Geber, siehe `linux/ui/README.md`).
- Guard-Ring/Masse-Fläche gegen Fehlauslösung; Abstand zu RF-Fenstern.

## D-Pad + Softkeys
- **Mechanische Taster** (oder Dome-Array): je Taste `KEY_*` → RP2350-GPIO.
- **Entprellung:** RC + Firmware-Debounce (RP2350). Aktiv-low mit Pull-up Richtung Ruhezustand.
- **ESD** an allen berührten Tasteneingängen.
- **Blindbedienbarkeit:** Tastenraster + Ring so, dass ohne Hinsehen bedienbar (UX-Vorgabe der UI).

## Kritische Design-Notizen
- **RP2350-Pin-Budget:** D-Pad (5) + Softkeys (5) + Ring-Sense/-I²C summieren → gegen RP2350-GPIO-Karte prüfen (Firmware `onex_modules.h`, Pins HOLD bis Gate G07).
- **Kein Eingabepfad über RK3576** für diese Elemente (Design-Review-Punkt).
- Ruhezustand definiert (keine schwebenden Eingänge → kein Phantom-Wake).

## ERC-Absicht
Jeder `KEY_*` ein Eingang mit definiertem Pull; Ring-Bus mit einem Pull-up-Satz; alle Ziele = RP2350.

## HOLD / TBD
Ring-AFE-MPN/-Architektur 📄 · Segmentzahl 📄 · RP2350-Pin-Zuordnung (HOLD → G07) · Taster-/Dome-Typ (TARGET).
