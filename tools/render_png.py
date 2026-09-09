#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — SVG nach PNG rendern (Edge headless).

Die Fenstergroesse wird aus dem SVG-Attribut `width`/`height` gelesen, nicht
geraten. Beim ersten Versuch war sie fest gesetzt -- Folge: rechts ein
schwarzer Rand und die Statuslegende am unteren Rand fehlte im Bild
vollstaendig. Ein Rendering, das Teile des Inhalts abschneidet, ohne es zu
melden, ist genau die Sorte stiller Fehler, die dieses Repo sonst faengt.

Aufruf:
    python tools/render_png.py <quelle.svg|verzeichnis> [--out ZIEL] [--scale 1.5]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
_SIZE = re.compile(r'\b(width|height)="([\d.]+)"')


def find_edge() -> Path:
    for c in EDGE_CANDIDATES:
        if Path(c).is_file():
            return Path(c)
    raise SystemExit("[FEHLER] Microsoft Edge nicht gefunden.")


def svg_size(path: Path) -> tuple[int, int]:
    """Groesse aus dem oeffnenden <svg>-Tag."""
    head = path.read_text(encoding="utf-8")[:800]
    tag = head[head.index("<svg"):head.index(">", head.index("<svg"))]
    vals = dict(_SIZE.findall(tag))
    if "width" not in vals or "height" not in vals:
        raise SystemExit(f"[FEHLER] {path.name}: kein width/height im <svg>-Tag.")
    return int(float(vals["width"])), int(float(vals["height"]))


def main() -> int:
    ap = argparse.ArgumentParser(description="SVG -> PNG (Edge headless)")
    ap.add_argument("src", help="SVG-Datei oder Verzeichnis")
    ap.add_argument("--out", default=None, help="Zielverzeichnis (Vorgabe: neben der Quelle)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="Aufloesungsfaktor (z. B. 2 fuer Druck)")
    args = ap.parse_args()

    edge = find_edge()
    # Absolut aufloesen: Path.as_uri() verlangt einen absoluten Pfad, und ein
    # relativer Aufruf ("docs/graphics/renders") ist der Normalfall.
    src = Path(args.src).resolve()
    files = sorted(src.glob("*.svg")) if src.is_dir() else [src]
    if not files:
        raise SystemExit(f"[FEHLER] Keine SVG unter {src}")

    out_dir = Path(args.out) if args.out else (src if src.is_dir() else src.parent)
    out_dir.mkdir(parents=True, exist_ok=True)

    for svg in files:
        w, h = svg_size(svg)
        w, h = int(w * args.scale), int(h * args.scale)
        png = out_dir / (svg.stem + ".png")
        cmd = [str(edge), "--headless", "--disable-gpu", f"--screenshot={png}",
               f"--window-size={w},{h}", "--hide-scrollbars"]
        if args.scale != 1.0:
            cmd.append(f"--force-device-scale-factor={args.scale}")
        subprocess.run(cmd + [svg.as_uri()], capture_output=True)
        if not png.is_file():
            print(f"  [FEHLER] {svg.name} -> kein PNG erzeugt")
            continue
        print(f"  {png}  ({w} x {h} px, {png.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
