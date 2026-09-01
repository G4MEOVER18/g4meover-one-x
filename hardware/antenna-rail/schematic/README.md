# ONE-X Antenna-Rail — Schaltplan

Antenna-Rail-Board (150 × 18 mm) — trägt die **4× externen SMA-Ports** (FIXED) mit vorbereiteten Filter-/Matching-Plätzen, ESD-Schutz und definierter Masse-/Rückführung. Gleiche Design-Spec-Methodik wie [Mainboard](../../mainboard/schematic/README.md).

## Rahmen (FIXED aus Spec)

| Punkt | Wert | Quelle |
|---|---|---|
| Outline | 150 × 18 mm | `pcb.antenna_rail_mm` |
| SMA-Ports | **4×** (nicht mehr) | Spec; Forbidden-Claim „10+ external SMA ports" |
| Anbindung | `J_ANT` (Mainboard Sheet 17) | Interface-Matrix |

> **Kein Über-Claim:** Genau **4** SMA. Die Rail führt Feeds von RF-Core/HyperRF nach außen; sie ist **kein** zusätzliches Radio.

## Sheet-Index

| # | Sheet | Kern | Status |
|---|---|---|---|
| 01 | SMA-Feeds / Matching / ESD | 4× SMA, Filter-/Matching-Footprints, ESD, Masse-Rückführung, Feed-Zuordnung | 4 SMA FIXED / Werte TBD 📄 (G09) |

## Netz-Konventionen
`ANT_<n>` (Feed 1..4, koax/impedanzkontrolliert 50 Ω), `ANT<n>_GND`.

## Statusdisziplin
**4 SMA + 50-Ω-Ziel** FIXED. **Filter-/Matching-Bauteilwerte** und die **exakte Band-/Radio-Zuordnung je Port** = TBD 📄 — Matching wird **auf realer Hardware getunt** (Gate **G09**), nie nur aus Simulation eingefroren.
