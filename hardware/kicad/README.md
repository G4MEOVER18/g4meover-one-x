# ONE-X — KiCad-Ableitung (deterministisch)

Übersetzung der reviewbaren Schaltplan-Design-Specs (`hardware/<board>/schematic/*.md`) in die KiCad-Welt. **Deterministisch generiert** von [`../../tools/gen_kicad_project.py`](../../tools/gen_kicad_project.py) — reproduzierbar, diff-bar, aus der Single Source abgeleitet.

## Was generiert wird (je Board unter `hardware/<board>/kicad/`)

| Datei | Inhalt | Verifiziert? |
|---|---|---|
| `<board>.kicad_pro` | KiCad-Projektdatei (JSON, minimal — KiCad ergänzt beim Öffnen) | JSON-Parse ✅ |
| `hierarchy.json` | maschinenlesbares Manifest: Sheets, je Sheet Netze + Inter-Board-Labels, globaler Netz-Index, feste uuid5 | JSON-Parse ✅ |
| `KICAD_BUILD_PLAN.md` | menschlicher Bauplan: Sheet-Reihenfolge, Global-Labels je Sheet, Inter-Board-/HOLD-Stub-Markierung | — |

## Was **nicht** generiert wird — und warum (Ehrlichkeitsdisziplin)

- **Keine `.kicad_sch`-S-Expressions.** In dieser Umgebung ist **kein KiCad installiert** (`kicad-cli` fehlt) → generierte Schaltplan-Dateien wären **nicht gegen das Binärformat verifizierbar**. „KiCad-Schaltplan erzeugt" ohne Nachweis, dass er öffnet, wäre ein unbestätigter Claim ([[feedback-chatgpt-data-rework]]-Disziplin gilt auch hier).
- **Keine Bauteil-Symbole/Pinouts.** Echte Symbole brauchen **Hersteller-Symbol-Libs** (Pin-Zuordnung je MPN). Die wird **nicht geraten** — gleiche Regel wie bei den HOLD-MPNs.

Dieses Verzeichnis liefert also die **verifizierbare, reproduzierbare Grundlage**; die eigentliche Zeichnung (Symbole platzieren, Global-Labels setzen, wiring) ist der nächste, KiCad-gebundene Schritt — geführt vom `KICAD_BUILD_PLAN.md` je Board.

## Ablauf der Zeichnung (pro Board)

1. `<board>.kicad_pro` in KiCad öffnen (bestätigen, dass Projekt lädt).
2. Root-Schaltplan anlegen, die im Bauplan gelisteten Sub-Sheets als Hierarchie-Sheets einfügen (Dateinamen aus dem Plan).
3. Je Sub-Sheet die **Inter-Board-Global-Labels** exakt nach [`../INTERFACE_NETS.md`](../INTERFACE_NETS.md) setzen (Namen von `schematic_netcheck.py` geprüft).
4. Symbole aus Vendor-Libs zuweisen (Pinouts aus Datenblatt) — pro Radio/IC ein Sheet.
5. **HOLD-Stub-Sheets** (im Plan markiert) bleiben leer bis zum jeweiligen Gate (Mainboard 04/05 → G02/G03, HyperRF 08 → G04).
6. ERC → Ziel **Gate G07** (ERC clean).

## Reihenfolge (Roadmap)
**Mainboard** + **RF-Core** zuerst (Kern + sicherheitskritischer RF-Kill), dann UI-Carrier / M.2-Bridge / Antenna-Rail, HyperRF zuletzt (FPGA-Stub bis G04).

## Regenerieren
```
python tools/gen_kicad_project.py     # erzeugt alle 6 Boards neu + Selbstprüfung
```
Läuft nach jeder Änderung an den Schaltplan-Specs erneut (die generierten Dateien sind abgeleitet, nicht handgepflegt).
