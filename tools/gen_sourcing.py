#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Sourcing-Register: konkrete Bestellnummern zur BOM.

WARUM EIGENES REGISTER, NICHT NUR EINE SPALTE IN DER BOM:
Ein Bestell-MPN ohne Beleg ist eine Behauptung. Dieses Register haelt zu jeder
konkretisierten Position fest, WORAUF sie sich stuetzt (Hersteller-Datenblatt,
Distributorseite) und WELCHE Entscheidung dahintersteckt -- damit ein spaeterer
Leser die Wahl nachvollziehen und widerlegen kann.

DREI ZUSTAENDE, sauber getrennt:
  ENTSCHIEDEN  konkreter, bestellbarer MPN + Beleg. Bestellbar.
  WAHL_OFFEN   Familie steht fest, aber eine echte Entscheidung fehlt noch
               (Variante, Package, SoC vs. Modul). KEIN Raten -- die
               Entscheidung wird benannt, nicht vorweggenommen.
  HOLD         Externe Herstellerdaten noetig (Gate). Unveraendert gesperrt.

Erzeugt: manufacturing/SOURCING_REGISTER.md + manufacturing/BOM_ORDERABLE.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOM = REPO / "manufacturing" / "BOM_EVT.csv"

# ---------------------------------------------------------------------------
# Recherchierte Konkretisierungen.
#
# "evidence" ist die Quelle, auf die sich der MPN stuetzt. Wo keine belastbare
# Quelle vorlag, steht die Position bewusst unter WAHL_OFFEN statt mit einem
# plausibel klingenden, aber ungeprueften MPN.
# ---------------------------------------------------------------------------

DECIDED: dict[str, dict[str, str]] = {
    "U201": {
        "mpn": "W25Q128JVSIQ",
        "package": "SOIC-8 (208 mil)",
        "temp": "-40..+85 C",
        "why": "16 MB QSPI fuer den RP2350B (Spec: compute.control_mcu FIXED). "
               "Suffix SIQ = SOIC-8, Industrietemperatur, breit verfuegbar.",
        "evidence": "https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf "
                    "| DigiKey 5803943",
    },
    "U221": {
        "mpn": "MAX98357AETE+T",
        "package": "TQFN-16 (3x3 mm)",
        "temp": "-40..+85 C",
        "why": "I2S-Eingang (Variante A, nicht B = left-justified). TQFN statt WLP: "
               "auf einem EVT-Board loet- und nacharbeitbar.",
        "evidence": "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf",
    },
    "U300": {
        "mpn": "BQ25792RQMR",
        "package": "QFN-29 (4x4 mm)",
        "temp": "-40..+85 C",
        "why": "2S-Pack (Spec: 2S2P 4x21700). BQ25792 deckt 1-4 Zellen, 5 A, "
               "USB-PD-3.0-OTG ab und passt zum TPS25751A-PD-Pfad (Sheet 01).",
        "evidence": "https://www.ti.com/product/BQ25792 | LCSC C2862876",
    },
    "U400/U401": {
        "mpn": "RTL8211FI-CG",
        "package": "QFN-40",
        "temp": "-40..+85 C",
        "why": "BEWUSSTE AENDERUNG gegenueber '-CG': Das Suffix I ist die "
               "Industrievariante (-40..+85 C); die Handelsvariante endet bei "
               "+70 C. Fuer ein Feld-/Aussengeraet ist das die richtige Wahl. "
               "Pin- und funktionskompatibel.",
        "evidence": "https://www.realtek.com/en/products/communications-network-ics/item/rtl8211f-i-cg",
    },
    "U623": {
        "mpn": "NEO-F10N-00B-20",
        "package": "LCC-Modul",
        "temp": "siehe Datenblatt",
        "why": "Die Endung -20 ist NICHT beliebig: nur sie liefert "
               "Carrier-Phase-Rohdaten. Die Spec verlangt 'L1/L5 raw' -- "
               "die Variante -00 wuerde die Anforderung verfehlen.",
        "evidence": "https://content.u-blox.com/sites/default/files/documents/NEO-F10N_DataSheet_UBX-23002117.pdf",
    },
}

# Positionen, bei denen eine echte Entscheidung offen ist. Bewusst NICHT
# geraten -- jede Zeile benennt die konkrete Frage.
OPEN_CHOICE: dict[str, dict[str, str]] = {
    "U624": {
        "family": "Qorvo DW3000-Serie",
        "question": "Welche der vier Varianten? Die Nomenklatur ist DW3<Package><Ports>0: "
                    "DW31x0 = WLCSP, DW32x0 = uQFN; DWx1x0 = 1 Antennenport, "
                    "DWx2x0 = 2 Ports (PDoA/Winkelmessung).",
        "tradeoff": "uQFN gibt ~2 dB weniger TX-Leistung als WLCSP, ist aber auf "
                    "einem HDI-EVT deutlich besser zu bestuecken und nachzuarbeiten. "
                    "PDoA kostet nochmals ~1 dB, ermoeglicht aber Winkelmessung.",
        "recommendation": "DW3220 (uQFN, 2 Ports), falls Winkelmessung gewuenscht ist; "
                          "sonst DW3210. Die Master-Spec fordert nur 'DW3000-series' -- "
                          "PDoA ist damit eine Produktentscheidung, keine Vorgabe.",
        "gate": "G05",
        "evidence": "https://www.qorvo.com/products/p/DW3210 | "
                    "https://forum.qorvo.com/t/dw3000-series-options/13450",
    },
    "U503": {
        "family": "Silicon Labs Z-Wave 800",
        "question": "SoC (EFR32ZG23, QFN40 5x5 oder QFN48 6x6) oder vorzertifiziertes "
                    "Modul (ZGM230S, 6,5x6,5 mm)?",
        "tradeoff": "Der SoC ist kleiner und guenstiger, verlangt aber eigene "
                    "Funkzulassung. Das Modul bringt die Zulassung mit -- bei einem "
                    "Geraet mit dieser Zahl an Funkstrecken ein erheblicher Unterschied "
                    "in Aufwand und Risiko.",
        "recommendation": "ZGM230S, solange die Stueckzahl klein ist. Erst bei "
                          "Serienvolumen lohnt der SoC-Weg.",
        "gate": "G09",
        "evidence": "https://www.silabs.com/wireless/z-wave/800-series-modem-soc",
    },
}


def load_bom() -> list[dict[str, str]]:
    with BOM.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def classify(row: dict[str, str]) -> str:
    ref = row["Ref"]
    # HOLD zuerst: eine Recherche darf ein HOLD nicht wegsortieren. Fuer U624
    # ist die Varianten-Nomenklatur inzwischen geklaert -- das Gate G05 bleibt
    # davon unberuehrt, bis die Wahl getroffen und in der Spec eingetragen ist.
    if row["Status"] == "HOLD":
        return "HOLD"
    if ref in DECIDED:
        return "ENTSCHIEDEN"
    if ref in OPEN_CHOICE:
        return "WAHL_OFFEN"
    mpn = (row["MPN / class"] or "")
    if "class" in mpn.lower() or "TBD" in mpn.upper():
        return "WAHL_OFFEN"
    return "ENTSCHIEDEN"


def build_csv(rows: list[dict[str, str]]) -> str:
    out = ["Ref,Subsystem,Qty,Manufacturer,Order_MPN,Package,Temp,Sourcing_State,Gate,Evidence"]
    for r in rows:
        state = classify(r)
        d = DECIDED.get(r["Ref"], {})
        mpn = d.get("mpn", r["MPN / class"] if state == "ENTSCHIEDEN" else "")
        fields = [
            r["Ref"], r["Subsystem"], r["Qty"], r["Manufacturer"],
            mpn, d.get("package", ""), d.get("temp", ""),
            state, r["Gate"], d.get("evidence", OPEN_CHOICE.get(r["Ref"], {}).get("evidence", "")),
        ]
        out.append(",".join('"' + f.replace('"', "'") + '"' for f in fields))
    return "\n".join(out) + "\n"


def build_md(rows: list[dict[str, str]]) -> str:
    states = {"ENTSCHIEDEN": [], "WAHL_OFFEN": [], "HOLD": []}
    for r in rows:
        states[classify(r)].append(r)

    n = len(rows)
    lines = [
        "# Sourcing-Register — von der BOM zur Bestellung",
        "",
        "> Erzeugt von `tools/gen_sourcing.py`. **Nicht von Hand bearbeiten** —",
        "> Änderungen gehören in das Werkzeug, damit Beleg und Begründung",
        "> zusammen mit dem Bauteil versioniert bleiben.",
        "",
        "Eine Stückliste wird nicht dadurch bestellbar, dass eine Bauteilfamilie",
        "dasteht. Erst ein konkreter Hersteller-MPN mit Package, Temperaturbereich",
        "und Beleg lässt sich einkaufen. Dieses Register trennt deshalb drei",
        "Zustände — und **rät nichts**.",
        "",
        "| Zustand | Bedeutung | Positionen |",
        "|---|---|---|",
        f"| **ENTSCHIEDEN** | konkreter, bestellbarer MPN + Beleg | {len(states['ENTSCHIEDEN'])} von {n} |",
        f"| **WAHL_OFFEN** | Familie steht, echte Entscheidung fehlt | {len(states['WAHL_OFFEN'])} von {n} |",
        f"| **HOLD** | externe Herstellerdaten nötig (Gate) | {len(states['HOLD'])} von {n} |",
        "",
        "---",
        "",
        "## Konkretisiert in dieser Runde",
        "",
        "Jede Zeile stützt sich auf ein Hersteller-Datenblatt oder eine",
        "Distributorseite. Zwei davon sind **inhaltliche Korrekturen**, keine",
        "bloßen Ergänzungen:",
        "",
    ]
    for ref, d in DECIDED.items():
        lines += [
            f"### `{ref}` → **{d['mpn']}**",
            "",
            f"- **Package:** {d['package']} · **Temperatur:** {d['temp']}",
            f"- **Begründung:** {d['why']}",
            f"- **Beleg:** {d['evidence']}",
            "",
        ]

    lines += [
        "---",
        "",
        "## Offene Bauteilentscheidungen",
        "",
        "Hier fehlt **kein Herstellerdatum**, sondern eine Produktentscheidung.",
        "Sie wird benannt statt vorweggenommen — ein plausibel klingender MPN wäre",
        "hier genau die Sorte stiller Festlegung, die dieses Repo vermeidet.",
        "",
        "> `U624` erscheint zusätzlich in der HOLD-Tabelle und **bleibt dort**.",
        "> Die Varianten-Nomenklatur ist zwar geklärt, aber ein Gate schließt sich",
        "> erst, wenn die Wahl getroffen und in der Master-Spec eingetragen ist —",
        "> nicht dadurch, dass jemand die Auswahl verstanden hat.",
        "",
    ]
    for ref, o in OPEN_CHOICE.items():
        lines += [
            f"### `{ref}` — {o['family']} (Gate {o['gate']})",
            "",
            f"**Frage:** {o['question']}",
            "",
            f"**Abwägung:** {o['tradeoff']}",
            "",
            f"**Empfehlung:** {o['recommendation']}",
            "",
            f"**Beleg:** {o['evidence']}",
            "",
        ]

    lines += [
        "---",
        "",
        "## Weiterhin ohne konkreten MPN",
        "",
        "Diese Positionen tragen noch eine Familien- oder Klassenangabe. Sie sind",
        "**nicht** durch fehlende Herstellerdaten blockiert — es fehlt schlicht die",
        "Auswahlrunde. Sie sind der nächste sinnvolle Arbeitsschritt.",
        "",
        "| Ref | Subsystem | Familie | Gate |",
        "|---|---|---|---|",
    ]
    for r in states["WAHL_OFFEN"]:
        if r["Ref"] in OPEN_CHOICE:
            continue
        lines.append(f"| `{r['Ref']}` | {r['Subsystem']} | {r['MPN / class']} | {r['Gate']} |")

    lines += [
        "",
        "## HOLD — nur mit externen Daten lösbar",
        "",
        "| Ref | Was fehlt | Von wem | Gate |",
        "|---|---|---|---|",
    ]
    holds = {
        "U102": ("Exakte LPDDR5-Topologie und qualifiziertes Teil", "Rockchip (Referenzdesign)", "G02"),
        "U103": ("Für RK3576 validiertes 256-GB-UFS-Teil", "Rockchip / UFS-Hersteller", "G03"),
        "U610": ("FPGA-MPN mit PCIe-2.1-Endpoint + DSP/BRAM", "Auswahlverfahren `hardware/hyperrf/fpga-selection/`", "G04"),
        "U624": ("Variantenwahl (siehe oben)", "Produktentscheidung", "G05"),
    }
    for r in states["HOLD"]:
        what, who, gate = holds.get(r["Ref"], ("—", "—", r["Gate"]))
        lines.append(f"| `{r['Ref']}` | {what} | {who} | {gate} |")

    lines += [
        "",
        "---",
        "",
        "## Was das für die Produktionsfreigabe heißt",
        "",
        "Solange Positionen in **HOLD** oder **WAHL_OFFEN** stehen, gibt es keine",
        "vollständige Bestell-BOM und damit auch keine Produktionsfreigabe. Das ist",
        "kein Formalismus: Ein Board, dessen Speicher-Topologie nicht feststeht,",
        "lässt sich weder routen noch bestücken.",
        "",
        "Der ehrliche Übergabestand an einen Fertiger ist deshalb weiterhin ein",
        "**DFM-/RFQ-Paket** (siehe [`DFM_RFQ_PCBWAY.md`](DFM_RFQ_PCBWAY.md) und",
        "[`ENGINEERING_HANDOFF_MINEWING.md`](ENGINEERING_HANDOFF_MINEWING.md)) —",
        "keine Gerber-Freigabe.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sourcing-Register erzeugen")
    ap.add_argument("--check", action="store_true", help="nur pruefen, nichts schreiben")
    args = ap.parse_args()

    rows = load_bom()
    artifacts = [
        (REPO / "manufacturing" / "BOM_ORDERABLE.csv", build_csv(rows)),
        (REPO / "manufacturing" / "SOURCING_REGISTER.md", build_md(rows)),
    ]

    ok = True
    for path, content in artifacts:
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                print(f"  [VERALTET] {path.relative_to(REPO)}")
                ok = False
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
            print(f"  geschrieben: {path.relative_to(REPO)}")

    if args.check:
        if ok:
            print(f"  [OK] Sourcing-Register aktuell ({len(artifacts)} Dateien).")
        return 0 if ok else 1

    dec = sum(1 for r in rows if classify(r) == "ENTSCHIEDEN")
    print(f"\nBestellbar: {dec}/{len(rows)} Positionen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
