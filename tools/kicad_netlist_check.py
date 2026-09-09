#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Regelpruefung auf der ECHTEN Netzliste.

Warum zusaetzlich zu ERC und kicad_netcheck:
  * ERC prueft allgemeine elektrische Plausibilitaet (offene Pins, Konflikte).
    Es kennt die Regeln DIESES Geraets nicht.
  * kicad_netcheck prueft nur, ob Netz-NAMEN kanonisch sind.
  * Hier wird geprueft, ob die Schaltung die sicherheits- und
    schnittstellenrelevanten Zusagen der Design-Spec tatsaechlich EINHAELT --
    an der Netzliste, die KiCad aus dem Schaltplan rechnet.

Die wichtigste Regel stammt aus
hardware/rf-core/schematic/sheet_01_supervisor_rfkill.md:

    "Kein verdeckter TX-Pfad: Jedes Radio-Sheet muss seinen PA/TX-Enable
     explizit ueber PA_EN_<radio> (dieses Sheet) fuehren -- Review-Punkt
     fuer ERC/Design-Review."

Genau dieser Review-Punkt wird hier automatisiert: ein PA-Enable, das am
Supervisor vorbeifuehrt, faellt auf -- nicht erst im Design-Review.

Exit 0 = alle Regeln erfuellt. 1 = Verstoss. 2 = kicad-cli fehlt (SKIP).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_env import find_kicad_cli   # noqa: E402

REPO = Path(__file__).resolve().parent.parent

_NET_BLOCK = re.compile(r'\n\t\t\(net\n')
_NAME = re.compile(r'\(name "([^"]+)"\)')
_NODE = re.compile(r'\(ref "([^"]+)"\)\s*\n\s*\(pin "([^"]+)"\)')
# Bauteilwerte, um Treiber zu identifizieren (U30 = Supervisor-Gate usw.)
_COMP = re.compile(r'\(comp\s*\n\s*\(ref "([^"]+)"\)\s*\n\s*\(value "([^"]+)"\)', re.S)


def export_netlist(cli: str, sch: Path, tmp: Path) -> tuple[dict[str, list[tuple[str, str]]],
                                                            dict[str, str]]:
    out = tmp / (sch.stem + ".net")
    proc = subprocess.run(
        [cli, "sch", "export", "netlist", "--format", "kicadsexpr",
         "--output", str(out), str(sch)],
        capture_output=True, text=True)
    if not out.is_file():
        raise RuntimeError(proc.stderr.strip() or "Netzliste nicht erzeugt")

    text = out.read_text(encoding="utf-8", errors="replace")
    nets: dict[str, list[tuple[str, str]]] = {}
    for block in _NET_BLOCK.split(text)[1:]:
        m = _NAME.search(block)
        if m:
            # KiCad stellt LOKALEN Netzen den Blattpfad voran ("/PCIE_RX_P"),
            # globalen nicht. Ohne Normalisierung wuerde eine Regel, die auf
            # "PA_EN_" prueft, ein versehentlich lokales Label stillschweigend
            # ueberspringen -- eine Pruefung, die sich durch die Label-Sorte
            # umgehen laesst, ist keine.
            nets[m.group(1).lstrip("/")] = _NODE.findall(block)
    comps = dict(_COMP.findall(text))
    return nets, comps


# --------------------------------------------------------------- Regeln

def rule_pa_enables_go_through_gate(nets, comps, sheet: str) -> list[str]:
    """
    Sicherheitsregel (rf-core sheet_01): Jedes PA_EN_<radio> darf ausschliesslich
    vom zugehoerigen Gate getrieben werden -- nie direkt von einem Verbinder.
    Ein PA-Enable, das am Supervisor vorbeilaeuft, waere ein verdeckter
    TX-Pfad: der RF-Kill koennte ihn nicht mehr sperren.
    """
    bad = []
    for net, nodes in nets.items():
        if not net.startswith("PA_EN_"):
            continue
        gate_drivers = [r for r, p in nodes
                        if comps.get(r, "").startswith("PA_GATE_") and p == "3"]
        connectors = [r for r, _ in nodes if r.startswith("J")]
        if connectors:
            bad.append(f"{sheet}: {net} haengt direkt an {', '.join(connectors)} "
                       f"-- verdeckter TX-Pfad am Supervisor vorbei")
        if len(gate_drivers) != 1:
            bad.append(f"{sheet}: {net} hat {len(gate_drivers)} Gate-Treiber "
                       f"(genau 1 erwartet)")
    return bad


def _has_supervisor(comps) -> bool:
    """Enthaelt dieses Blatt das Supervisor-Gate? Nur dann gelten die
    RF-Kill-Regeln -- auf der M.2-Bridge waeren sie sinnlos."""
    return any(v == "TX_GATE" for v in comps.values())


def rule_gate_feedback_is_downstream(nets, comps, sheet: str) -> list[str]:
    """
    TX_GATE_OK muss den Ausgang der Gate-Logik fuehren, nicht deren Eingang.
    Die Firmware vergleicht ihren Befehl gegen dieses Signal (onex_rfkill.c);
    laege der Abgriff vor dem Gate, waere er mit dem Befehl identisch und der
    Vergleich koennte nie eine Abweichung finden.

    WICHTIG -- die Regel prueft zuerst die EXISTENZ: Verschmilzt TX_GATE_OK
    mit einem anderen Netz (etwa weil es faelschlich vor dem Gate abgegriffen
    wird), benennt KiCad das gemeinsame Netz nach nur einem der beiden Namen.
    Ein blosses nets.get(...) faende dann nichts und wuerde Schweigen als
    Zustimmung werten -- genau der Fall, den die Regel fangen soll.
    """
    if not _has_supervisor(comps):
        return []
    nodes = nets.get("TX_GATE_OK")
    if nodes is None:
        return [f"{sheet}: Blatt enthaelt das Supervisor-Gate, aber kein Netz "
                f"TX_GATE_OK -- vermutlich mit einem anderen Netz verschmolzen"]
    sup_out = [r for r, p in nodes if comps.get(r, "") == "TX_GATE" and p == "3"]
    if not sup_out:
        return [f"{sheet}: TX_GATE_OK wird nicht vom Supervisor-Ausgang getrieben "
                f"-- die Rueckmeldung waere identisch mit dem Befehl"]
    return []


def rule_kill_inputs_reach_gate(nets, comps, sheet: str) -> list[str]:
    """RF_KILL und RF_KILL_SW_n muessen beide am Supervisor-Gate ankommen.
    Faellt einer weg, ist der Kill nur noch einfach abgesichert."""
    if not _has_supervisor(comps):
        return []
    bad = []
    for net in ("RF_KILL", "RF_KILL_SW_n"):
        nodes = nets.get(net)
        if nodes is None:
            # Auch hier: fehlendes Netz ist ein Befund, kein Freibrief.
            bad.append(f"{sheet}: Netz {net} fehlt, obwohl das Supervisor-Gate "
                       f"auf diesem Blatt sitzt")
            continue
        if not any(comps.get(r, "") == "TX_GATE" for r, _ in nodes):
            bad.append(f"{sheet}: {net} erreicht das Supervisor-Gate nicht")
    return bad


def rule_diff_pairs_complete(nets, comps, sheet: str) -> list[str]:
    """
    Zu jedem _P gehoert ein _N mit gleich vielen Knoten. Ein halbes Diff-Paar
    ist auf einer Highspeed-Strecke immer ein Fehler -- und faellt sonst erst
    im Layout oder gar erst am Messplatz auf.
    """
    bad = []
    for net, nodes in nets.items():
        if not net.endswith("_P"):
            continue
        partner = net[:-2] + "_N"
        if partner not in nets:
            bad.append(f"{sheet}: {net} ohne Gegenstueck {partner}")
        elif len(nets[partner]) != len(nodes):
            bad.append(f"{sheet}: {net}/{partner} unterschiedlich verdrahtet "
                       f"({len(nodes)} vs {len(nets[partner])} Knoten)")
    return bad


def rule_no_single_node_local_nets(nets, comps, sheet: str) -> list[str]:
    """
    Ein Netz mit nur einem Knoten verbindet nichts.

    Erlaubt ist das nur, wo der zweite Knoten auf einem Blatt liegt, das es
    noch NICHT gibt -- die Radio-Blaetter 02-06 des RF-Core brauchen alle eine
    Hersteller-Pinbelegung und sind gesperrt. Bis dahin ist ein Feed, der von
    dort kommt, zeichnerisch einseitig, ohne dass etwas falsch waere.

    Bewusst KEINE Praefix-Familie: die Ausnahme gilt genau diesen Netzen und
    soll verfallen, sobald ihr Quell-Blatt gezeichnet ist. Ein weiches
    "^ANT_" haette jeden kuenftigen Antennen-Namen mit abgedeckt -- auch den,
    bei dem der fehlende zweite Knoten ein echter Fehler waere.
    """
    allowed = re.compile(
        r'^(TXREQ_|PA_EN_|TX_GATE_OK$|RF_KILL'
        r'|ANT_SUBGHZ$|ANT_2G4$|ANT_ZWAVE$|ANT_UHF$)')
    bad = []
    for net, nodes in nets.items():
        if len(nodes) < 2 and not allowed.match(net):
            bad.append(f"{sheet}: Netz {net} hat nur einen Knoten "
                       f"({nodes[0][0]}.{nodes[0][1]})" if nodes else
                       f"{sheet}: Netz {net} ohne Knoten")
    return bad


RULES = [
    ("PA-Enables laufen ueber den Supervisor", rule_pa_enables_go_through_gate),
    ("TX_GATE_OK wird hinter dem Gate abgegriffen", rule_gate_feedback_is_downstream),
    ("Beide Kill-Eingaenge erreichen das Gate", rule_kill_inputs_reach_gate),
    ("Diff-Paare vollstaendig und symmetrisch", rule_diff_pairs_complete),
    ("Keine Netze mit nur einem Knoten", rule_no_single_node_local_nets),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Regelpruefung auf der Netzliste")
    ap.add_argument("--check", action="store_true", help="leise Ausgabe")
    args = ap.parse_args()

    cli = find_kicad_cli()
    if cli is None:
        print("[UEBERSPRUNGEN] kicad-cli nicht gefunden.")
        return 2

    # Board-Roots: die Netzliste eines Boards enthaelt die Netze ALLER seiner
    # Blaetter, blattuebergreifend zusammengefuehrt. Nur so laesst sich pruefen,
    # ob ein PA-Enable irgendwo am Supervisor vorbeigefuehrt wird.
    sheets = sorted(
        p for p in REPO.glob("hardware/*/kicad/*.kicad_sch")
        if p.stem == p.parent.parent.name
    )
    if not sheets:
        print("[UEBERSPRUNGEN] Noch keine Board-Roots.")
        return 2

    if not args.check:
        print("=" * 64)
        print(" ONE-X -- Regelpruefung auf der Netzliste")
        print("=" * 64)

    violations: list[str] = []
    total_nets = 0
    with tempfile.TemporaryDirectory(prefix="onex_net_") as td:
        tmp = Path(td)
        for sch in sheets:
            rel = str(sch.relative_to(REPO))
            try:
                nets, comps = export_netlist(cli, sch, tmp)
            except RuntimeError as e:
                violations.append(f"{rel}: Netzliste nicht exportierbar ({e})")
                continue
            total_nets += len(nets)
            for _label, fn in RULES:
                violations.extend(fn(nets, comps, sch.stem))

    if violations:
        print("  [FEHLER] Regelverstoesse auf der Netzliste:")
        for v in violations:
            print(f"           {v}")
        return 1

    if not args.check:
        print(f"  [OK] {len(sheets)} Boards, {total_nets} Netze, "
              f"{len(RULES)} Regeln erfuellt:")
        for label, _ in RULES:
            print(f"       - {label}")
    else:
        print(f"Netzlisten-Regeln erfuellt ({total_nets} Netze, {len(RULES)} Regeln).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
