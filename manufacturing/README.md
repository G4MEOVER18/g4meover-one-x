# ONE-X — Fertigungs-Handoff (`manufacturing/`)

Dieser Ordner ist das **Übergabepaket** für die zwei angeschriebenen Fertigungs-/Engineering-Partner (Outreach-Phase, siehe [`../README.md`](../README.md)). Er macht ONE-X **an genau den Stellen weitergebbar, die diese Firmen schließen sollen** — ohne offene Herstellerdaten zu erfinden.

> **Wichtig — ehrlicher Reifegrad:** ONE-X ist **EVT/Engineering-Review** (`review_state: imported_under_review`). Es gibt **keine** finalen Produktions-Gerber/CPL, weil vier Kern-Gates **HOLD** sind (LPDDR5-Topologie, UFS-MPN, HyperRF-FPGA, HDI-Stackup). Diese HOLDs werden **durch die Partner** geschlossen:
> - **PCBWay** → HDI-Stackup/DFM (**G06**).
> - **Minewing** → Sourcing/Validierung der HOLD-/TARGET-Teile + Schaltplan-/Layout-Review (SI/PI, DFM).
>
> Ein RFQ/DFM-Paket ist der **korrekte erste Übergabestand** — nicht fertige Gerber. So werden die Gates auf dem richtigen Weg geschlossen.

## EVT-Umfang
- **Erstserie: 1–3 Einheiten** (EVT, gestaffelter Power-Up-Bringup).
- Ziel: Display (G01) → Core-Boot → RF-Kette schrittweise verifizieren, **bevor** DVT/Kleinserie.

## Paketinhalt

| Datei | Adressat | Zweck |
|---|---|---|
| [`MANUFACTURING_READINESS_REVIEW.md`](MANUFACTURING_READINESS_REVIEW.md) | intern/beide | Gate-für-Gate-Reifegrad-Scorecard (was ready, was HOLD, wer schließt es) |
| [`BOARD_SET.md`](BOARD_SET.md) | beide | 6-Board-Set: Outlines, Lagen, HDI-Bedarf, Schnittstellen |
| [`DFM_RFQ_PCBWAY.md`](DFM_RFQ_PCBWAY.md) | **PCBWay** | PCB-Fertigungs-/DFM-RFQ + präzise Fragen zum Stackup (G06) |
| [`ENGINEERING_HANDOFF_MINEWING.md`](ENGINEERING_HANDOFF_MINEWING.md) | **Minewing** | JDM/ODM-Scope, Sourcing-Aufträge für HOLD-Teile, Review-Umfang |
| [`BOM_EVT.csv`](BOM_EVT.csv) | beide | Fertigungs-BOM mit Status + Sourcing-Owner + Gate je Position |

Ergänzende Quellen im Repo: mechanische Referenz [`../mechanical/`](../mechanical/), Master-Spec [`../spec/`](../spec/) (BOM, Power-Tree, Interface-Matrix), Grafiken [`../docs/graphics/`](../docs/graphics/).

## Ownership (Annahme: Hybrid)
- **Schaltplan-Entwurf + BOM:** in diesem Repo (Phase 5, in Arbeit → [`../hardware/schematic/`](../hardware/schematic/)).
- **SI/PI-/DFM-Review + Sourcing der HOLD-Teile:** Minewing.
- **HDI-Fertigung + Stackup/DFM:** PCBWay.
> Falls du eine andere Aufteilung willst, hier anpassen.

## Was NICHT hier ist (bewusst)
- Keine finalen Gerber/CPL (blockiert durch HOLD-Gates — siehe MRR).
- Keine Kontaktnamen/Mailvorlagen (privat beim Owner, nicht im Repo — [[../README.md]] Outreach-Regel).
- Keine als „produktionsbestätigt" deklarierten HOLD-Werte.
