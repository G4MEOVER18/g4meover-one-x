# ONE-X — Mechanik / Gehäuse (`mechanical/`)

CadQuery-Quelle für Gehäuse, Board-Bauraum, Akku, Thermik und Antennen-Rail als **EVT-Referenz-/Kollisionsmodell**. Deckt die Industrie-Design-Ebene der [Roadmap](../docs/ROADMAP.md) (Phase 10) ab.

## Erzeugen

```sh
pip install cadquery      # einmalig
python generate_enclosure.py
```

Ausgabe: `../CAD_STEP/*.step` + `../STL/*.stl` je Bauteil, plus `ONE-X_EVT6_ASSEMBLY_REFERENCE.step`. Das Skript druckt am Ende eine Bounding-Box-Plausibilitätsprüfung gegen das FIXED-Envelope (230×110×64) und eine HOLD-Erinnerung.

## Formsprache (Querformat)

Konsistent mit [`../docs/graphics/front_layout.svg`](../docs/graphics/front_layout.svg):
**Touch-Ring Ø40 links · 5″-Display mittig · D-Pad 34×34 rechts · 5 Softkeys unten · 4× SMA oben.**

## Statusdisziplin

Jeder Maß-Parameter im Skript trägt seinen Spec-Key + Status:

| Ebene | Status | Quelle / Gate |
|---|---|---|
| Envelope 230×110×64, Fenster 112,5×64,5, Ring Ø40, D-Pad 34×34, Board-Outlines, Rail 150×18, 4× SMA, Akku-Topologie 2S2P/4×21700 | **FIXED** | Master-Spec `mechanical.*` / `pcb.*` / `battery.*` |
| Displaymodul-Außenmaß, aktive Fläche, 21700-Zellmaß, Wandstärke, Eck-Chamfer | **TARGET** | Bauteil-/DFM-abhängig |
| Thermik (Spreader/Fans/Kurven) | **HOLD** | Gate **G10** — reale P/Q-Kurven + CFD/Mess-EVT |
| Akku-Pack-Compliance (UN38.3/BMS/NTC/Schutz) | **HOLD** | Gate **G11** |
| finaler Eckenradius/Wandstärke/Stackup | **HOLD** | nach DFM (G06/G08) |

> Die STEP/STL sind **kein** Fertigungsfreigabe-Stand. Thermik und Akku-Compliance sind bewusst nicht validiert.
