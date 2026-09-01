# KiCad-Bauplan — antenna-rail

> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.
> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der
> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).

## Hierarchie
- Root-Sheet `antenna-rail.kicad_sch` instanziiert **1** Sub-Sheets.
- Root-UUID (fix): `dd085160-008d-5a06-a5bf-11c24b5deae0`

## Sub-Sheets (Reihenfolge + Global-Labels)

| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |
|---|---|---|---|---|
| 01 | `sheet_01_sma_feeds.kicad_sch` | Antenna-Rail Sheet 01 — SMA-Feeds / Matching / ESD | `ANT_1`, `ANT_2`, `ANT_3`, `ANT_4` | zeichnen |

## Regeln
- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus
  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).
- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).
- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.
- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.
