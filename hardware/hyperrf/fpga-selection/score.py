#!/usr/bin/env python3
"""G4MEOVER ONE-X -- Gate G04: HyperRF-FPGA Candidate Scoring.

Liest CANDIDATE_MATRIX.csv, wendet die Knockout-Filter (K*) an und rechnet den
gewichteten Score (S*). Bewusst HOLD-treu: solange eine relevante Zelle 'TBD'
ist, wird KEINE Scheinzahl ausgegeben, sondern 'INSUFFICIENT DATA -- HOLD'.

Bewertungskonvention in der CSV:
  Knockout-Zellen (K*):  PASS | FAIL | TBD
  Score-Zellen   (S*):   0..5 | TBD

Aufruf:  python score.py [pfad/zu/CANDIDATE_MATRIX.csv]
Exit 0 immer (Report-Tool); Gate-Entscheidung steht im Text.
"""
import csv
import sys
from pathlib import Path

# Windows-Konsolen (cp1252) koennen sonst an Unicode scheitern -> auf UTF-8 zwingen.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

MATRIX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("CANDIDATE_MATRIX.csv")


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    meta = ("axis_id", "description", "type", "weight")
    candidates = [c for c in rows[0].keys() if c not in meta]
    return rows, candidates


def check_weights(rows):
    total = sum(int(r["weight"]) for r in rows if r["type"] == "score" and r["weight"].strip())
    return total


def evaluate(rows, cand):
    """-> (verdict, score_or_None, notes[])"""
    notes = []
    # Stufe 1: Knockout
    for r in rows:
        if r["type"] != "knockout":
            continue
        val = r[cand].strip().upper()
        if val == "FAIL":
            return ("DISQUALIFIED", None, [f"{r['axis_id']} FAIL -- {r['description']}"])
        if val in ("", "TBD"):
            notes.append(f"{r['axis_id']} offen (TBD)")
    # Stufe 2: Score
    weighted = 0.0
    for r in rows:
        if r["type"] != "score":
            continue
        val = r[cand].strip()
        if val in ("", "TBD"):
            notes.append(f"{r['axis_id']} offen (TBD)")
            continue
        try:
            pts = float(val)
        except ValueError:
            notes.append(f"{r['axis_id']} ungueltig ('{val}')")
            continue
        weighted += pts * int(r["weight"])
    if notes:
        return ("INSUFFICIENT DATA -- HOLD", None, notes)
    return ("SCORED", round(weighted / 100.0, 3), [])


def main():
    if not MATRIX.exists():
        print(f"[FEHLER] Matrix nicht gefunden: {MATRIX}")
        return 0
    rows, candidates = load(MATRIX)

    wsum = check_weights(rows)
    print("== G4MEOVER ONE-X -- Gate G04: HyperRF-FPGA Scoring ==")
    print(f"Matrix : {MATRIX.name}   Kandidaten: {len(candidates)}")
    ok = "OK" if wsum == 100 else "WARNUNG"
    print(f"Gewichtssumme (S*): {wsum} [{ok} -- Soll 100]")
    print("-" * 60)

    results = []
    for cand in candidates:
        verdict, score, notes = evaluate(rows, cand)
        results.append((cand, verdict, score, notes))
        line = f"{cand:14s} : {verdict}"
        if score is not None:
            line += f"   score={score}/5.0"
        print(line)
        for n in notes:
            print(f"                 - {n}")

    print("-" * 60)
    scored = [r for r in results if r[1] == "SCORED"]
    if not scored:
        print("Gate G04 bleibt HOLD: kein Kandidat vollstaendig bewertet.")
        print("-> CANDIDATE_MATRIX.csv mit Datenblatt-/Verfuegbarkeitswerten fuellen.")
    else:
        scored.sort(key=lambda r: r[2], reverse=True)
        best = scored[0]
        print(f"Fuehrend: {best[0]}  (score={best[2]}/5.0)")
        print("Freeze erst nach Owner-Review der Gewichtung + belegten Quellen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
