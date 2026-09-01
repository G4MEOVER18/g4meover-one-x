#!/usr/bin/env python3
"""G4MEOVER ONE-X -- KiCad-Ableitung (deterministisch) aus den Schaltplan-Design-Specs.

Erzeugt je Board aus hardware/<board>/schematic/*.md:
  - <board>/kicad/<board>.kicad_pro   : KiCad-Projektdatei (JSON, minimal, valide)
  - <board>/kicad/hierarchy.json      : maschinenlesbares Hierarchie-/Netz-Manifest
  - <board>/kicad/KICAD_BUILD_PLAN.md : menschlicher Bauplan (welche Sheets, welche
                                        Global-Labels je Sheet, Inter-Board markiert)

Bewusst KEINE .kicad_sch-S-Expressions: Ohne installiertes KiCad nicht gegen das
Binaerformat verifizierbar; echte Symbole brauchen Hersteller-Pinouts (Vendor-Libs),
die nicht geraten werden. Dieses Skript liefert die verifizierbare, reproduzierbare
Grundlage; die Zeichnung selbst (Symbole/Wiring) ist der KiCad-Schritt darauf.

Deterministisch: UUIDs via uuid5 (fester Namespace + Name) -> reproduzierbar, diff-bar.
Aufruf:  python tools/gen_kicad_project.py [--check]
"""
import json
import re
import sys
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"
NS = uuid.UUID("0e1x0e1x-0000-4000-8000-000000000001".replace("x", "0"))  # fester Namespace

BOARDS = ["mainboard", "rf-core", "ui-carrier", "m2-bridge", "antenna-rail", "hyperrf"]

# Kanonische Inter-Board-Netz-Staemme (Quelle: hardware/INTERFACE_NETS.md)
INTERBOARD_STEMS = [
    "PCIE_TX", "PCIE_RX", "PCIE_REFCLK", "PCIE_PERST_n", "PCIE_CLKREQ_n", "PCIE_WAKE_n",
    "USB3_M2_TX", "USB3_M2_RX", "USB2_M2_D",
    "DSI0_", "LCD_RST_n", "BL_EN", "BL_PWM", "VLCD_3V3",
    "TP_SCL", "TP_SDA", "TP_INT", "TP_RST", "VDD_TP_3V3",
    "RFC_SPI", "RFC_UART", "RFC_I2C", "RFC_IRQ", "RF_KILL", "RF_KILL_SW_n", "TX_GATE_OK",
    "ANT_1", "ANT_2", "ANT_3", "ANT_4",
    "HYPERRF_AUX_5V", "BAT_2S2P",
]

NET_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,}[A-Za-z0-9_./*<>-]*)`")
HEADING_RE = re.compile(r"^#\s+(.*)$", re.M)
# Ein Sheet ist ein Stub NUR bei echtem Platzhalter-Marker (nicht schon, weil irgendwo "HOLD" steht):
STUB_RE = re.compile(r"⛔|Platzhalter|bewusst NICHT ausgearbeitet", re.I)


def is_interboard(net):
    """Praezise: exakter Kanonik-Name oder Kanonik-Bus-Praefix + '_'.
    Verhindert Fehltreffer wie ANT_2G4 (lokal) fuer ANT_2 (Connector-Netz)."""
    for s in INTERBOARD_STEMS:
        if s.endswith("_"):
            if net.startswith(s):           # Bus-Praefix, z.B. DSI0_
                return True
        elif net == s or net.startswith(s + "_"):   # exakt oder Suffix, z.B. PCIE_TX / PCIE_TX_P
            return True
    return False


def det_uuid(*parts):
    return str(uuid.uuid5(NS, "|".join(parts)))


def clean_net(tok):
    # Wildcards/Suffix-Rauschen abschneiden; nur den Stamm behalten
    tok = tok.split("/")[0].rstrip("*<>._-")
    return tok


def parse_sheet(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = HEADING_RE.search(text)
    title = m.group(1).strip() if m else path.stem
    nets = sorted({clean_net(t) for t in NET_RE.findall(text) if clean_net(t)})
    is_hold = bool(STUB_RE.search(title))   # Stub-Marker steht im Titel, nicht in Prosa-Erwaehnungen
    return title, nets, is_hold


def sheet_num(path):
    m = re.match(r"sheet_(\d+)", path.stem)
    return m.group(1) if m else "00"


def gen_board(board):
    sdir = HW / board / "schematic"
    if not sdir.exists():
        return None
    sheets_md = sorted([p for p in sdir.glob("sheet_*.md")], key=lambda p: sheet_num(p))
    root_uuid = det_uuid(board, "root")

    sheets = []
    net_index = {}
    for p in sheets_md:
        num = sheet_num(p)
        title, nets, is_hold = parse_sheet(p)
        ib = sorted({n for n in nets if is_interboard(n)})
        sheets.append({
            "num": num,
            "file": p.name,
            "kicad_file": p.stem + ".kicad_sch",
            "title": title,
            "uuid": det_uuid(board, "sheet", num),
            "nets": nets,
            "interboard_nets": ib,
            "hold_stub": is_hold,
        })
        for n in nets:
            net_index.setdefault(n, []).append(num)

    manifest = {
        "board": board,
        "root_uuid": root_uuid,
        "sheet_count": len(sheets),
        "generator": "tools/gen_kicad_project.py",
        "source": f"hardware/{board}/schematic/",
        "sheets": sheets,
        "net_index": {k: sorted(set(v)) for k, v in sorted(net_index.items())},
    }

    kdir = HW / board / "kicad"
    kdir.mkdir(exist_ok=True)

    # 1) hierarchy.json
    (kdir / "hierarchy.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2) minimal .kicad_pro (JSON, KiCad ergaenzt den Rest beim Oeffnen)
    pro = {
        "meta": {"filename": f"{board}.kicad_pro", "version": 1},
        "board": {},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "schematic": {},
        "sheets": [[s["uuid"], f"{s['num']}:{s['title']}"] for s in sheets],
        "text_variables": {},
    }
    (kdir / f"{board}.kicad_pro").write_text(json.dumps(pro, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3) Bauplan
    lines = [
        f"# KiCad-Bauplan — {board}",
        "",
        "> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.",
        "> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der",
        "> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).",
        "",
        "## Hierarchie",
        f"- Root-Sheet `{board}.kicad_sch` instanziiert **{len(sheets)}** Sub-Sheets.",
        f"- Root-UUID (fix): `{root_uuid}`",
        "",
        "## Sub-Sheets (Reihenfolge + Global-Labels)",
        "",
        "| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |",
        "|---|---|---|---|---|",
    ]
    for s in sheets:
        ib = ", ".join(f"`{n}`" for n in s["interboard_nets"]) or "—"
        status = "⛔ HOLD-Stub" if s["hold_stub"] else "zeichnen"
        lines.append(f"| {s['num']} | `{s['kicad_file']}` | {s['title']} | {ib} | {status} |")
    lines += [
        "",
        "## Regeln",
        "- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus",
        "  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).",
        "- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).",
        "- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.",
        "- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.",
    ]
    (kdir / "KICAD_BUILD_PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return manifest


def self_check(manifests):
    print("\n== Selbstpruefung ==")
    ok = True
    for m in manifests:
        board = m["board"]
        kdir = HW / board / "kicad"
        # JSON re-parse
        try:
            json.loads((kdir / "hierarchy.json").read_text(encoding="utf-8"))
            json.loads((kdir / f"{board}.kicad_pro").read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  FAIL {board}: JSON kaputt: {e}")
            ok = False
            continue
        # jede Sheet-Quelle existiert
        for s in m["sheets"]:
            if not (HW / board / "schematic" / s["file"]).exists():
                print(f"  FAIL {board}: Quelle fehlt: {s['file']}")
                ok = False
        print(f"  ok   {board}: {m['sheet_count']} Sheets, {len(m['net_index'])} Netze")
    return ok


def main():
    print("== G4MEOVER ONE-X -- KiCad-Projekt-Ableitung ==")
    manifests = []
    for b in BOARDS:
        m = gen_board(b)
        if m:
            manifests.append(m)
            ibn = sum(len(s["interboard_nets"]) for s in m["sheets"])
            holds = sum(1 for s in m["sheets"] if s["hold_stub"])
            print(f"  {b:13s}: {m['sheet_count']:2d} Sheets, {len(m['net_index']):3d} Netze, {ibn:2d} Inter-Board-Label-Refs, {holds} HOLD-Stub(s)")
    ok = self_check(manifests)
    print("\n" + ("Alle Manifeste/Projekte generiert und selbstgeprueft." if ok else "FEHLER in Selbstpruefung."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
