# Sheet 04 — LPDDR5 ⛔ BLOCKIERT (Gate G02)

16 GB LPDDR5 am RK3576. **Kapazität FIXED (16 GB)**, aber **Topologie/MPN HOLD** — dieses Sheet wird **bewusst nicht finalisiert**, bis G02 mit Rockchip-gestützten Daten geschlossen ist.

> Interface-Matrix: „Do not route before Rockchip-supported topology confirmation." Forbidden Claim: „16GB LPDDR5 exact topology production-confirmed".

## Warum blockiert
LPDDR5-Routing ist von der **exakten Topologie** abhängig (Anzahl Kanäle/Dies, x16/x32-Aggregat, Ranks, ODT/Training). Diese Werte zu raten würde ein Board erzeugen, das das Memory-Training nicht besteht. Die Topologie muss **Rockchip-RK3576-gestützt** sein (→ Minewing-Sourcing, [`../../../manufacturing/ENGINEERING_HANDOFF_MINEWING.md`](../../../manufacturing/ENGINEERING_HANDOFF_MINEWING.md)).

## Anforderungen (was feststeht / zu klären ist)

| Punkt | Wert/Status |
|---|---|
| Kapazität | 16 GB — **FIXED** |
| Technologie | LPDDR5 — **FIXED** |
| Aggregat | dual-channel ×16 / ×32 (Interface-Matrix) — **zu bestätigen** 📄 |
| Exakte MPN + Die/Channel-Topologie | **HOLD (G02)** 📄 |
| `VDD_DDR`-Rail (Sheet 02) | folgt Topologie — **HOLD** 📄 |
| Training/ODT/Impedanz | nach Topologie + Rockchip-Referenz 📄 |

## Was zum Schließen von G02 gebraucht wird
1. Rockchip-**RK3576-Referenz** für unterstützte 16-GB-LPDDR5-Topologien.
2. Qualifizierte, beziehbare **MPN** (Second-Source wünschenswert).
3. Referenz-Training-/Layout-Guidelines (Fly-by/Point-to-Point, Längen/Skew, Impedanz).

## Nach G02 (dann erst)
Vollständiges Sheet: Byte-Lane-Zuordnung, `VDD_DDR`/`VDDQ`, Entkopplung, `CA`/`DQ`/`DQS`/`CK`-Netze, Termination — plus Layout-Constraints für Sheet-08-SI/PI (Länge/Skew/Impedanz, Return-Path).

**Status: ⛔ nicht routen, nicht als produktionsbestätigt darstellen.**
