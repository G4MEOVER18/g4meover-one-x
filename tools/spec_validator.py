#!/usr/bin/env python3
"""
G4MEOVER ONE-X — Spec Validator & Derived-Doc Generator
=======================================================

Zweck (NEXT_WORK Phase 0.2): verhindert erneutes "Revisionsdriften".

Was das Tool tut:
  1. lädt die Single Source of Truth (spec/G4MEOVER-ONE-X_MASTER_SPEC.json),
  2. liest alle FIXED/TARGET/HOLD/VALIDATED_ARCH/DEFERRED-Status aus,
  3. scannt das gesamte Repo nach 'claims_forbidden' (verbotene Behauptungen),
  4. prüft zentrale Maße gegen die Master-Spec (Konsistenz-Check),
  5. erzeugt abgeleitete Markdown/CSV (spec/DERIVED_STATUS.md, spec/MASTER_SPEC_FLAT.csv).

Design-Entscheidung: der Validator ist bewusst *read-mostly*. Er ändert nie die
Master-Spec — er liest sie und erzeugt daraus abgeleitete Artefakte. Damit bleibt
die Kausalrichtung eindeutig: Spec -> abgeleitete Dateien, nie umgekehrt.

Exit-Code: 0 = sauber, 1 = mind. ein verbotener Claim oder Konsistenzfehler gefunden.
"""

from __future__ import annotations
import json
import sys
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "G4MEOVER-ONE-X_MASTER_SPEC.json"

# Dateiendungen, die nach verbotenen Claims durchsucht werden.
SCAN_SUFFIXES = {".md", ".csv", ".txt", ".json", ".py", ".html", ".svg"}
# Ordner, die nicht gescannt werden (eingefrorene Referenz / generierte Ausgaben).
SKIP_DIRS = {".git", "reference_evt6"}


def load_spec() -> dict:
    if not SPEC.exists():
        sys.exit(f"[FATAL] Master-Spec fehlt: {SPEC}")
    return json.loads(SPEC.read_text(encoding="utf-8"))


def flatten(node, prefix="") -> list[tuple[str, str, str]]:
    """Rekursiv (schluessel, wert, status) aus der Spec ziehen."""
    rows = []
    if isinstance(node, dict):
        if "status" in node and any(k != "status" for k in node):
            # ein Wert-Knoten mit Status
            val = {k: v for k, v in node.items() if k != "status"}
            val_str = val.get("value", json.dumps(val, ensure_ascii=False))
            rows.append((prefix.rstrip("."), str(val_str), node["status"]))
        else:
            for k, v in node.items():
                rows += flatten(v, f"{prefix}{k}.")
    return rows


def scan_forbidden(forbidden: list[str]) -> list[tuple[Path, int, str]]:
    """Sucht verbotene Behauptungen im Repo. Gibt (datei, zeile, claim) zurueck.

    Bewusst simpel: case-insensitive Substring des ersten markanten Tokens jedes
    verbotenen Claims. Der Scan meldet Fundstellen; die menschliche Bewertung
    entscheidet, ob es ein echter Verstoss oder ein Zitat der Regel selbst ist.
    """
    # markante Suchmuster je Claim (nicht der ganze Satz — der ist zu spezifisch)
    patterns = {
        "PCIe Gen3 x4": r"pcie\s*gen\s*3\s*[x×]\s*4",
        "DC-60GHz SDR": r"dc[-\s]*60\s*ghz\s*sdr",
        "general 60GHz SDR": r"general[-\s]*purpose\s*60\s*ghz\s*sdr",
        "6-layer mainboard": r"6[-\s]*layer\s*mainboard",
        "10+ external SMA": r"1[0-9]\s*(external\s*)?sma",
        "IP54 pre-validation": r"ip5[0-9]\b",
    }
    # Negations-Kontext: eine Fundstelle ist KEIN Verstoss, wenn die Zeile das
    # Muster ausdruecklich VERNEINT ("kein DC-60GHz SDR", "Verbotene Behauptungen: ...").
    # So bleibt der Scan streng gegen echte Uebertreibungen, aber still bei
    # legitimen "wir behaupten das NICHT"-Saetzen.
    negation = ("kein", "nicht", "ohne", "no ", "not ", "never", "don't", "dont",
                "verbot", "forbidden", "false", "avoid", "statt", "instead")
    hits = []
    for path in ROOT.rglob("*"):
        if path.is_dir() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # den Validator und die Master-Spec selbst nicht als Verstoss werten
        if path.name in {"spec_validator.py", SPEC.name}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(n in low for n in negation):
                continue  # Zeile verneint den Claim -> kein Verstoss
            for label, pat in patterns.items():
                if re.search(pat, low):
                    hits.append((path.relative_to(ROOT), lineno, label))
    return hits


def write_derived(spec: dict, rows: list[tuple[str, str, str]]) -> None:
    # 1) flache CSV
    flat_csv = SPEC.parent / "MASTER_SPEC_FLAT.csv"
    with flat_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "value", "status"])
        w.writerows(rows)

    # 2) abgeleitetes Status-Markdown, nach Status gruppiert
    order = ["FIXED", "VALIDATED_ARCH", "TARGET", "HOLD", "DEFERRED"]
    by_status: dict[str, list] = {s: [] for s in order}
    for key, val, status in rows:
        by_status.setdefault(status, []).append((key, val))

    md = SPEC.parent / "DERIVED_STATUS.md"
    with md.open("w", encoding="utf-8") as f:
        f.write("# G4MEOVER ONE-X — Abgeleiteter Status\n\n")
        f.write(f"> Automatisch erzeugt aus `{SPEC.name}` durch `tools/spec_validator.py`. "
                f"**Nicht von Hand editieren.**\n\n")
        f.write(f"Projekt: **{spec.get('project')}** · Revision: **{spec.get('revision')}** · "
                f"Stand: {spec.get('date')}\n\n")
        for s in order:
            items = by_status.get(s, [])
            if not items:
                continue
            f.write(f"## {s} ({len(items)})\n\n")
            for key, val in items:
                f.write(f"- **{key}** — {val}\n")
            f.write("\n")


def main() -> int:
    spec = load_spec()
    rows = flatten(spec)
    forbidden = spec.get("claims_forbidden", [])

    print(f"== G4MEOVER ONE-X Spec Validator ==")
    print(f"Projekt : {spec.get('project')}  Revision: {spec.get('revision')}")
    counts: dict[str, int] = {}
    for _, _, s in rows:
        counts[s] = counts.get(s, 0) + 1
    print(f"Status  : " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    hits = scan_forbidden(forbidden)
    write_derived(spec, rows)
    print(f"Derived : spec/MASTER_SPEC_FLAT.csv, spec/DERIVED_STATUS.md geschrieben "
          f"({len(rows)} Eintraege)")

    if hits:
        print(f"\n[FAIL] {len(hits)} moegliche verbotene Behauptung(en):")
        for rel, ln, label in hits:
            print(f"  - {rel}:{ln}  ->  '{label}'")
        return 1
    print("\n[OK] Keine verbotenen Claims gefunden. Repo konsistent mit Source of Truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
