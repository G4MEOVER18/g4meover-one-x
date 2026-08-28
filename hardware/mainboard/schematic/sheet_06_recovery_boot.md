# Sheet 06 — Recovery / Boot (SPI-NOR)

Boot-/Recovery-Flash (U104, 32 MB SPI-NOR, Winbond/MXIC-Klasse) + Anti-Brick-Pfad. Status: SPI-NOR **TARGET** (exakte MPN nach Boot-Design). Boot-Straps liegen physisch am RK3576 (Sheet 03); dieses Sheet definiert Flash + Recovery-Logik.

## Bauteile / Netze

| Netz | Funktion | Ziel | Status |
|---|---|---|---|
| `SPI_NOR_SCK/CSn/IO0..3` | QSPI zum Boot-Flash | RK3576-SPI/FSPI | TARGET |
| `SPI_NOR_WPn`, `SPI_NOR_HOLDn` | Schutz | — | TARGET |
| `BOOT_SEL[..]` | Boot-Quellen-Straps (Werte 📄 aus TRM) | RK3576 (Sheet 03) | HOLD 📄 |
| `MASKROM_n` | Maskrom/Recovery erzwingen | Taster/Testpunkt | FIXED-Absicht |
| `RECOVERY_BTN_n` | Recovery-Taster (opt.) | — | TARGET |

## Boot-Strategie
- **Primär-Boot:** UFS/eMMC (Sheet 05, G03) bzw. SD (falls vorhanden); **SPI-NOR** hält Bootloader/Recovery.
- **Anti-Brick:** Maskrom-Boot des RK3576 muss **immer** erreichbar sein (Taster/Testpunkt `MASKROM_n`) → Wiederherstellung auch bei korruptem Flash.
- **RP2350-Recovery** ist getrennt (Sheet 16): der Always-On-Manager kann RK3576-Recovery anstoßen (`CMD_RECOVERY`, [ONE-X-Link](../../../firmware/rp2350/PROTOCOL.md)).

## Kritische Design-Notizen
- **Boot-Straps** mit definierten Pulls; nicht mit anderen Pin-Funktionen kollidieren lassen (TRM prüfen 📄).
- **SPI-NOR-Spannung** (1V8 vs 3V3) an RK3576-Bank anpassen.
- **Schreibschutz** (`WPn`) für Recovery-Region vorsehen.
- **Testpunkte:** `MASKROM_n`, `SPI_NOR_*`, Boot-Straps (→ Sheet 18) — Bring-up-kritisch.

## ERC-Absicht
QSPI-Bus konsistent; Straps mit Pull + Testpunkt; `MASKROM_n` eindeutig (ein Treiber/Taster). SPI-NOR-Rail als Power-Input.

## HOLD / TBD
- **Boot-Strap-Werte** (RK3576-TRM) 📄.
- Exakte SPI-NOR-MPN + Kapazitätsaufteilung (Bootloader/Recovery) nach Boot-Design.
