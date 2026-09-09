#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — fotorealistische Konzept-Renderings (SVG).

WAS DAS IST -- und was ausdruecklich nicht:

Erzeugt drei Ansichten des Geraets nach aktuellem Projektstand:

    product_front   Endprodukt, Frontansicht
    board_set       die sechs Platinen, massstaeblich nebeneinander
    internal_stack  Innenaufbau (Explosionsansicht)

Alle Aussenmasse, Bedienelemente und Board-Outlines kommen aus der
Master-Spec bzw. aus manufacturing/BOARD_SET.md -- sie sind FIXED und damit
echt. Alles andere ist Illustration.

DIE WICHTIGE EINSCHRAENKUNG:
`pcb.current_files_status` haelt fest, dass es NUR Floorplan-Boards gibt und
KEIN geroutetes Produktionslayout. Die Platinenbilder zeigen deshalb
Bauteil-BLOECKE auf massstaeblichen Outlines -- keine Leiterbahnen, keine
Pinbelegung, kein Layout. Jedes Blatt traegt diesen Hinweis sichtbar.

Ohne diesen Hinweis waere ein huebsches Platinenbild gegenueber einem
Fertiger eine stille Behauptung ("Layout fertig"), die nicht stimmt -- genau
die Sorte Aussage, die dieses Repo sonst verhindert. Aus demselben Grund
tragen HOLD-Positionen (LPDDR5-Topologie, UFS-MPN, FPGA-MPN) ihr Gate
sichtbar im Bild.

Aufruf:
    python tools/gen_renders.py [--out VERZEICHNIS]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

REPO = Path(__file__).resolve().parent.parent
SPEC = REPO / "spec" / "G4MEOVER-ONE-X_MASTER_SPEC.json"

# Markenfarben (branding/) -- dunkel, Akzent Cyan/Amber.
INK = "#0b0d10"
ACCENT = "#00d4c8"
AMBER = "#ffb020"
HOLD_RED = "#ff5a5f"


def spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


# --------------------------------------------------------------- Bausteine

def defs_common(px_mm: float) -> str:
    """Verlaeufe, Texturen und Schatten, die alle drei Ansichten teilen."""
    return f"""
<defs>
  <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#14181d"/><stop offset="1" stop-color="#080a0c"/>
  </linearGradient>

  <!-- Gehaeuse: Magnesium-/Verbundschale, Licht von oben links -->
  <linearGradient id="caseGrad" x1="0.1" y1="0" x2="0.75" y2="1">
    <stop offset="0"    stop-color="#5a626c"/>
    <stop offset="0.18" stop-color="#3d444d"/>
    <stop offset="0.55" stop-color="#2a3037"/>
    <stop offset="1"    stop-color="#171b20"/>
  </linearGradient>
  <linearGradient id="caseEdge" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#7d858f" stop-opacity="0.9"/>
    <stop offset="0.5" stop-color="#4a515a" stop-opacity="0.25"/>
    <stop offset="1" stop-color="#0d1014" stop-opacity="0.9"/>
  </linearGradient>

  <!-- Gummierte Griffzonen -->
  <linearGradient id="gripGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#22262b"/><stop offset="1" stop-color="#101317"/>
  </linearGradient>

  <!-- Displayglas: dunkel mit schraegem Reflex -->
  <linearGradient id="glassGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0"    stop-color="#1a2733"/>
    <stop offset="0.35" stop-color="#0b1016"/>
    <stop offset="1"    stop-color="#05080b"/>
  </linearGradient>
  <linearGradient id="glare" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0"   stop-color="#ffffff" stop-opacity="0.16"/>
    <stop offset="0.45" stop-color="#ffffff" stop-opacity="0.03"/>
    <stop offset="1"   stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>

  <!-- Metall (SMA, Ringfassung, Schrauben) -->
  <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0"    stop-color="#e8ecef"/>
    <stop offset="0.25" stop-color="#9aa3ac"/>
    <stop offset="0.5"  stop-color="#5c646d"/>
    <stop offset="0.75" stop-color="#98a1aa"/>
    <stop offset="1"    stop-color="#3a4149"/>
  </linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f6dd9a"/><stop offset="0.45" stop-color="#d3a943"/>
    <stop offset="1" stop-color="#8a6a1f"/>
  </linearGradient>

  <!-- Leiterplatte: Loetstopplack mit feiner Textur -->
  <linearGradient id="pcbGrad" x1="0" y1="0" x2="0.6" y2="1">
    <stop offset="0" stop-color="#12312a"/><stop offset="0.5" stop-color="#0c241f"/>
    <stop offset="1" stop-color="#071612"/>
  </linearGradient>
  <linearGradient id="pcbHdi" x1="0" y1="0" x2="0.6" y2="1">
    <stop offset="0" stop-color="#1b1f24"/><stop offset="0.5" stop-color="#121519"/>
    <stop offset="1" stop-color="#0a0c0f"/>
  </linearGradient>

  <!-- IC-Gehaeuse: geschliffener Kunststoff -->
  <linearGradient id="icGrad" x1="0.2" y1="0" x2="0.8" y2="1">
    <stop offset="0" stop-color="#3c4148"/><stop offset="0.5" stop-color="#23272c"/>
    <stop offset="1" stop-color="#15181c"/>
  </linearGradient>
  <!-- Abschirmblech -->
  <linearGradient id="shield" x1="0" y1="0" x2="0.8" y2="1">
    <stop offset="0" stop-color="#b9c1c9"/><stop offset="0.4" stop-color="#828b95"/>
    <stop offset="1" stop-color="#575f68"/>
  </linearGradient>

  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="7"/>
    <feColorMatrix type="saturate" values="0"/>
    <feComponentTransfer><feFuncA type="linear" slope="0.11"/></feComponentTransfer>
    <feComposite operator="in" in2="SourceGraphic"/>
  </filter>
  <filter id="softShadow" x="-30%" y="-30%" width="180%" height="190%">
    <feDropShadow dx="0" dy="{2.2 * px_mm:.1f}" stdDeviation="{2.0 * px_mm:.1f}"
                  flood-color="#000" flood-opacity="0.62"/>
  </filter>
  <filter id="tinyShadow" x="-40%" y="-40%" width="190%" height="200%">
    <feDropShadow dx="0" dy="{0.28 * px_mm:.2f}" stdDeviation="{0.22 * px_mm:.2f}"
                  flood-color="#000" flood-opacity="0.66"/>
  </filter>
  <filter id="innerGlow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="{0.9 * px_mm:.1f}"/>
  </filter>
</defs>"""


def header(title: str, sub: str, w: float, note: str) -> str:
    return f"""
<rect width="{w}" height="100%" fill="url(#bgGrad)"/>
<text x="56" y="70" font-family="Inter,Segoe UI,sans-serif" font-size="40"
      font-weight="700" fill="#eef2f5" letter-spacing="1.5">G4MEOVER ONE-X</text>
<text x="56" y="108" font-family="Inter,Segoe UI,sans-serif" font-size="23"
      fill="{ACCENT}" letter-spacing="0.6">{title}</text>
<text x="56" y="140" font-family="Inter,Segoe UI,sans-serif" font-size="17"
      fill="#8d99a5">{sub}</text>
<text x="{w - 56}" y="70" text-anchor="end" font-family="Inter,Segoe UI,sans-serif"
      font-size="15" fill="#6f7b87">{note}</text>"""


def status_note(x: float, y: float, lines: list[tuple[str, str]], w: float = 560) -> str:
    """Kasten mit Statuslegende. lines = [(Farbe, Text), ...]"""
    h = 30 + 26 * len(lines)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
           f'fill="#0e1216" stroke="#2a3138" stroke-width="1.5"/>']
    for i, (col, txt) in enumerate(lines):
        cy = y + 30 + 26 * i
        out.append(f'<circle cx="{x + 20}" cy="{cy - 5}" r="5.5" fill="{col}"/>')
        out.append(f'<text x="{x + 36}" y="{cy}" font-family="Inter,Segoe UI,sans-serif" '
                   f'font-size="15" fill="#b7c2cc">{txt}</text>')
    return "\n".join(out)


# ------------------------------------------------------- 1) Produkt (Front)

def render_product(s: dict) -> str:
    m = s["mechanical"]
    W = m["device_envelope_mm"]["x"]          # 230  FIXED
    H = m["device_envelope_mm"]["y"]          # 110  FIXED
    rec_w = m["front_display_recess_mm"]["x"]  # 138 FIXED
    rec_h = m["front_display_recess_mm"]["y"]  # 81  FIXED
    win_w = m["visible_display_window_mm"]["x"]  # 112.5 FIXED
    win_h = m["visible_display_window_mm"]["y"]  # 64.5  FIXED
    ring_d = m["touch_ring_outer_diameter_mm"]["value"]   # 40 FIXED
    dpad = m["dpad_envelope_mm"]["x"]          # 34 FIXED
    n_keys = m["softkeys"]["count"]            # 5  FIXED
    n_sma = m["external_sma_ports"]["count"]   # 4  FIXED

    K = 9.0                                    # px je mm
    OX, OY = 130, 250                          # Ursprung Gehaeuseecke
    CW, CH = W * K, H * K
    SW, SH = int(CW + 2 * OX), int(CH + OY + 430)

    def X(mm): return OX + mm * K
    def Y(mm): return OY + mm * K

    # Positionen exakt wie im maßstaeblichen docs/graphics/front_layout.svg
    ring_cx, ring_cy = 26.0, 55.0
    dpad_cx, dpad_cy = 207.0, 55.0
    rec_x, rec_y = (W - rec_w) / 2, (H - rec_h) / 2
    win_x, win_y = (W - win_w) / 2, (H - win_h) / 2

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
         f'viewBox="0 0 {SW} {SH}">', defs_common(K),
         header("Endprodukt — Frontansicht",
                f"Massstabsgetreu · Gehaeuse {W:.0f} × {H:.0f} × "
                f"{m['device_envelope_mm']['z']:.0f} mm (FIXED)",
                SW, "Konzept-Rendering · kein Foto")]

    # --- Gehaeusekoerper -----------------------------------------------
    o.append(f'<g filter="url(#softShadow)">')
    o.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{CW}" height="{CH}" rx="{16 * K}" '
             f'fill="url(#caseGrad)" stroke="#0a0d10" stroke-width="2"/>')
    o.append('</g>')
    # Fase entlang der Kante
    o.append(f'<rect x="{X(0) + 3}" y="{Y(0) + 3}" width="{CW - 6}" height="{CH - 6}" '
             f'rx="{16 * K - 3}" fill="none" stroke="url(#caseEdge)" stroke-width="3.5"/>')
    # feine Oberflaechentextur
    o.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{CW}" height="{CH}" rx="{16 * K}" '
             f'fill="#8899aa" filter="url(#grain)" opacity="0.5"/>')

    # --- gummierte Griffzonen links/rechts ------------------------------
    for gx in (2.5, W - 2.5 - 46):
        o.append(f'<rect x="{X(gx)}" y="{Y(8)}" width="{46 * K}" height="{(H - 16) * K}" '
                 f'rx="{9 * K}" fill="url(#gripGrad)" opacity="0.92"/>')
        for i in range(13):     # Rillen
            ry = Y(14 + i * 6.2)
            o.append(f'<rect x="{X(gx + 4)}" y="{ry}" width="{38 * K}" height="2.0" '
                     f'rx="1" fill="#000" opacity="0.30"/>')
            o.append(f'<rect x="{X(gx + 4)}" y="{ry + 2.2}" width="{38 * K}" height="1.2" '
                     f'rx="1" fill="#59626c" opacity="0.22"/>')

    # --- 4x SMA an der Oberkante (FIXED) --------------------------------
    for i in range(n_sma):
        sx = W * (i + 1) / (n_sma + 1)
        o.append(f'<rect x="{X(sx - 5.4)}" y="{Y(-2.5)}" width="{10.8 * K}" height="{7 * K}" '
                 f'rx="{1.2 * K}" fill="#242a31" stroke="#141a1f" stroke-width="1.4"/>')
        o.append(f'<rect x="{X(sx - 4.6)}" y="{Y(-9.5)}" width="{9.2 * K}" height="{10 * K}" '
                 f'rx="{1.6 * K}" fill="url(#metal)" stroke="#20262c" stroke-width="1.6"/>')
        for k in range(4):      # Raendelung
            o.append(f'<rect x="{X(sx - 4.2 + k * 2.3)}" y="{Y(-9.0)}" width="{1.1 * K}" '
                     f'height="{8.6 * K}" fill="#000" opacity="0.20"/>')
        o.append(f'<circle cx="{X(sx)}" cy="{Y(-4.6)}" r="{2.5 * K}" fill="url(#gold)"/>')
        o.append(f'<circle cx="{X(sx)}" cy="{Y(-4.6)}" r="{0.8 * K}" fill="#15181c"/>')
        o.append(f'<text x="{X(sx)}" y="{Y(-12.5)}" text-anchor="middle" font-size="15" '
                 f'font-family="Inter,Segoe UI,sans-serif" fill="#7f8b96">ANT {i + 1}</text>')

    # --- Display-Recess + Glas ------------------------------------------
    o.append(f'<rect x="{X(rec_x)}" y="{Y(rec_y)}" width="{rec_w * K}" height="{rec_h * K}" '
             f'rx="{3.5 * K}" fill="#0a0c0f" stroke="#3b434c" stroke-width="2"/>')
    o.append(f'<rect x="{X(rec_x) + 4}" y="{Y(rec_y) + 4}" width="{rec_w * K - 8}" '
             f'height="{rec_h * K - 8}" rx="{3.0 * K}" fill="url(#glassGrad)"/>')
    # aktives Bild
    o.append(f'<rect x="{X(win_x)}" y="{Y(win_y)}" width="{win_w * K}" height="{win_h * K}" '
             f'fill="#04070a"/>')
    o.append(_screen_content(X(win_x), Y(win_y), win_w * K, win_h * K))
    # Glasreflex ueber dem gesamten Recess
    o.append(f'<path d="M {X(rec_x) + 4} {Y(rec_y) + 4} L {X(rec_x + rec_w * 0.62)} '
             f'{Y(rec_y) + 4} L {X(rec_x) + 4} {Y(rec_y + rec_h * 0.86)} Z" fill="url(#glare)"/>')
    o.append(f'<text x="{X(rec_x + rec_w / 2)}" y="{Y(H) + 30}" '
             f'text-anchor="middle" font-size="16" font-family="Inter,Segoe UI,sans-serif" '
             f'fill="#8d99a5">5" IPS · 1280 × 720 quer · 4-Lane MIPI-DSI (FIXED)</text>')

    # --- Touch-Ring Ø40 links -------------------------------------------
    o.append(f'<circle cx="{X(ring_cx)}" cy="{Y(ring_cy)}" r="{ring_d / 2 * K}" '
             f'fill="#12161a" stroke="url(#metal)" stroke-width="{1.6 * K}"/>')
    o.append(f'<circle cx="{X(ring_cx)}" cy="{Y(ring_cy)}" r="{ring_d / 2 * K - 5}" '
             f'fill="none" stroke="#000" stroke-width="2" opacity="0.7"/>')
    o.append(f'<circle cx="{X(ring_cx)}" cy="{Y(ring_cy)}" r="{12.5 * K}" '
             f'fill="url(#caseGrad)" stroke="#565e68" stroke-width="1.5"/>')
    for i in range(24):         # Segmentmarken des kapazitiven Rings
        import math
        a = i * math.pi / 12
        r1, r2 = 14.0 * K, 17.2 * K
        x1 = X(ring_cx) + math.cos(a) * r1
        y1 = Y(ring_cy) + math.sin(a) * r1
        x2 = X(ring_cx) + math.cos(a) * r2
        y2 = Y(ring_cy) + math.sin(a) * r2
        col = ACCENT if i % 6 == 0 else "#4a545e"
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{col}" stroke-width="2.4" opacity="0.85"/>')
    o.append(f'<text x="{X(ring_cx)}" y="{Y(ring_cy + ring_d / 2 + 7)}" text-anchor="middle" '
             f'font-size="14" font-family="Inter,Segoe UI,sans-serif" '
             f'fill="{HOLD_RED}">Ring Ø40 FIXED · AFE HOLD</text>')

    # --- D-Pad rechts ----------------------------------------------------
    a = dpad * K
    o.append(f'<circle cx="{X(dpad_cx)}" cy="{Y(dpad_cy)}" r="{a * 0.62}" '
             f'fill="#14181d" stroke="#454d56" stroke-width="2"/>')
    arm, thick = a * 0.46, a * 0.30
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        cx_, cy_ = X(dpad_cx) + dx * arm * 0.55, Y(dpad_cy) + dy * arm * 0.55
        w_ = thick if dx == 0 else arm
        h_ = arm if dx == 0 else thick
        o.append(f'<rect x="{cx_ - w_ / 2}" y="{cy_ - h_ / 2}" width="{w_}" height="{h_}" '
                 f'rx="{thick * 0.28}" fill="url(#caseGrad)" stroke="#5d666f" '
                 f'stroke-width="1.4" filter="url(#tinyShadow)"/>')
    o.append(f'<circle cx="{X(dpad_cx)}" cy="{Y(dpad_cy)}" r="{thick * 0.44}" '
             f'fill="#1b2026" stroke="#5d666f" stroke-width="1.4"/>')
    o.append(f'<text x="{X(dpad_cx)}" y="{Y(dpad_cy + dpad / 2 + 7)}" text-anchor="middle" '
             f'font-size="14" font-family="Inter,Segoe UI,sans-serif" fill="#7f8b96">'
             f'D-Pad 34 × 34 FIXED</text>')

    # --- 5 Softkeys unten ------------------------------------------------
    kw, kh = 17.0, 7.0
    span = rec_w * 0.92
    for i in range(n_keys):
        kx = W / 2 - span / 2 + span * (i + 0.5) / n_keys - kw / 2
        ky = H - 12.5
        o.append(f'<rect x="{X(kx)}" y="{Y(ky)}" width="{kw * K}" height="{kh * K}" '
                 f'rx="{2.2 * K}" fill="url(#caseGrad)" stroke="#5d666f" stroke-width="1.4" '
                 f'filter="url(#tinyShadow)"/>')
        o.append(f'<rect x="{X(kx) + 3}" y="{Y(ky) + 3}" width="{kw * K - 6}" '
                 f'height="{kh * K * 0.42}" rx="{1.6 * K}" fill="#fff" opacity="0.07"/>')
        o.append(f'<text x="{X(kx + kw / 2)}" y="{Y(ky + kh / 2) + 6}" text-anchor="middle" '
                 f'font-size="15" font-family="Inter,Segoe UI,sans-serif" '
                 f'fill="#9aa5b0">F{i + 1}</text>')

    # --- Status-LEDs + Marke ---------------------------------------------
    for i, (col, lab) in enumerate(((ACCENT, "PWR"), (HOLD_RED, "RF-KILL"), (AMBER, "ACT"))):
        lx = 62 + i * 11
        o.append(f'<circle cx="{X(lx)}" cy="{Y(6.0)}" r="{1.5 * K}" fill="{col}" '
                 f'opacity="0.95"/>')
        o.append(f'<circle cx="{X(lx)}" cy="{Y(6.0)}" r="{2.6 * K}" fill="{col}" '
                 f'opacity="0.22" filter="url(#innerGlow)"/>')
        o.append(f'<text x="{X(lx + 3.2)}" y="{Y(7.2)}" font-size="12.5" '
                 f'font-family="Inter,Segoe UI,sans-serif" fill="#78838e">{lab}</text>')
    o.append(f'<text x="{X(W / 2)}" y="{Y(H - 2.0)}" text-anchor="middle" font-size="17" '
             f'font-weight="600" letter-spacing="4" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#5d676f">G4MEOVER ONE-X</text>')

    # --- Bemassung --------------------------------------------------------
    dy_ = Y(H) + 76
    o.append(f'<line x1="{X(0)}" y1="{dy_}" x2="{X(W)}" y2="{dy_}" stroke="#4c565f" '
             f'stroke-width="1.5"/>')
    for xx in (0, W):
        o.append(f'<line x1="{X(xx)}" y1="{dy_ - 9}" x2="{X(xx)}" y2="{dy_ + 9}" '
                 f'stroke="#4c565f" stroke-width="1.5"/>')
    o.append(f'<rect x="{X(W / 2) - 52}" y="{dy_ - 15}" width="104" height="30" rx="6" '
             f'fill="#0b0e11"/>')
    o.append(f'<text x="{X(W / 2)}" y="{dy_ + 6}" text-anchor="middle" font-size="17" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#c3ccd4">{W:.0f} mm</text>')
    dx_ = X(W) + 52
    o.append(f'<line x1="{dx_}" y1="{Y(0)}" x2="{dx_}" y2="{Y(H)}" stroke="#4c565f" '
             f'stroke-width="1.5"/>')
    o.append(f'<text x="{dx_ + 10}" y="{Y(H / 2)}" font-size="17" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#c3ccd4">{H:.0f} mm</text>')

    o.append(status_note(56, SH - 210, [
        ("#7bd88f", "FIXED — Aussenmasse, Display-Fenster, Touch-Ring Ø40, D-Pad, "
                    "5 Softkeys, 4× SMA: aus der Master-Spec"),
        (AMBER, "TARGET — Masse 800–950 g, Panel-Referenzklasse, Akku 72 Wh"),
        (HOLD_RED, "HOLD — Touch-Ring-AFE (G07) · Panel-Bringup (G01) · "
                   "keine IP-Schutzart behauptet (DEFERRED)"),
        ("#6f7b87", "Oberflaechen, Farben und Beschriftung sind Illustration — "
                    "kein Industriedesign-Freeze."),
    ], w=SW - 112))
    o.append("</svg>")
    return "\n".join(o)


def _screen_content(x: float, y: float, w: float, h: float) -> str:
    """Launcher-Oberflaeche im Display (spiegelt linux/ui/mockup_home.svg)."""
    o = [f'<g clip-path="url(#scr)">',
         f'<defs><clipPath id="scr"><rect x="{x}" y="{y}" width="{w}" height="{h}"/>'
         f'</clipPath></defs>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#070b10"/>']
    # Statusleiste
    bh = h * 0.115
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{bh}" fill="#0d141c"/>')
    o.append(f'<text x="{x + w * 0.02}" y="{y + bh * 0.70}" font-size="{bh * 0.52:.1f}" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="{ACCENT}">ONE-X</text>')
    o.append(f'<rect x="{x + w * 0.34}" y="{y + bh * 0.20}" width="{w * 0.22}" '
             f'height="{bh * 0.58}" rx="{bh * 0.29}" fill="#2a0e12" stroke="{HOLD_RED}" '
             f'stroke-width="1.2"/>')
    o.append(f'<text x="{x + w * 0.45}" y="{y + bh * 0.68}" text-anchor="middle" '
             f'font-size="{bh * 0.42:.1f}" font-family="Inter,Segoe UI,sans-serif" '
             f'fill="{HOLD_RED}">RF-KILL AKTIV</text>')
    o.append(f'<text x="{x + w * 0.97}" y="{y + bh * 0.70}" text-anchor="end" '
             f'font-size="{bh * 0.45:.1f}" font-family="Inter,Segoe UI,sans-serif" '
             f'fill="#8e9aa6">72 Wh</text>')
    # Vier Funkdomaenen als Kacheln (Farben wie architecture.svg)
    tiles = [("Sub-GHz", "#3ba7ff"), ("2,4 GHz", "#7bd88f"),
             ("NFC / RFID", AMBER), ("HyperRF SDR", "#c58cff")]
    tw, th = w * 0.225, h * 0.40
    for i, (lab, col) in enumerate(tiles):
        tx = x + w * 0.025 + i * (tw + w * 0.0165)
        ty = y + bh + h * 0.07
        o.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="{th * 0.13}" '
                 f'fill="#101820" stroke="{col}" stroke-width="1.6" opacity="0.95"/>')
        o.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th * 0.18}" '
                 f'rx="{th * 0.09}" fill="{col}" opacity="0.30"/>')
        fs = min(th * 0.19, tw * 1.55 / max(6, len(lab)))
        o.append(f'<text x="{tx + tw / 2}" y="{ty + th * 0.62}" text-anchor="middle" '
                 f'font-size="{fs:.1f}" font-family="Inter,Segoe UI,sans-serif" '
                 f'fill="{col}">{lab}</text>')
    # Spektrum-Streifen
    sy = y + bh + h * 0.55
    o.append(f'<rect x="{x + w * 0.025}" y="{sy}" width="{w * 0.95}" height="{h * 0.22}" '
             f'rx="{h * 0.02}" fill="#0a1018" stroke="#1c2731" stroke-width="1.2"/>')
    import math
    pts = []
    for i in range(120):
        px = x + w * 0.03 + i * (w * 0.94 / 119)
        v = (math.sin(i * 0.55) * 0.30 + math.sin(i * 0.13 + 1.1) * 0.42
             + math.sin(i * 1.9) * 0.14)
        py = sy + h * 0.19 - abs(v) * h * 0.155
        pts.append(f"{px:.1f},{py:.1f}")
    o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{ACCENT}" '
             f'stroke-width="1.6" opacity="0.95"/>')
    # Softkey-Leiste
    ky = y + h * 0.90
    for i, lab in enumerate(("SCAN", "TX", "LOG", "MAP", "SYS")):
        kx = x + w * 0.025 + i * (w * 0.19)
        o.append(f'<text x="{kx + w * 0.085}" y="{ky + h * 0.06}" text-anchor="middle" '
                 f'font-size="{h * 0.055:.1f}" font-family="Inter,Segoe UI,sans-serif" '
                 f'fill="#6f7d8a">{lab}</text>')
    o.append("</g>")
    return "\n".join(o)


# ------------------------------------------------------------ 2) Board-Set

# (Name, Breite, Hoehe, Lagen, Prozess, Fuellung) -- Outlines aus BOARD_SET.md
BOARDS = [
    ("Mainboard", 210, 92, "12 Lagen · HDI", "pcbHdi"),
    ("UI-Carrier", 218, 100, "Lagen TBD", "pcbGrad"),
    ("HyperRF", 136, 72, "HDI wahrscheinlich", "pcbHdi"),
    ("RF-Core", 92, 66, "Standard + RF", "pcbGrad"),
    ("Antenna-Rail", 150, 18, "RF", "pcbGrad"),
    ("M.2-Bridge", 30, 52, "Standard", "pcbGrad"),
]

# Bauteil-Bloecke je Board: (x, y, w, h, Beschriftung, Typ, Status)
#   Typ: bga | qfn | shield | conn | passive | sma | module
#   Status: "" | "HOLD Gxx"
PARTS = {
    "Mainboard": [
        (86, 30, 30, 30, "RK3576", "bga", ""),
        (52, 26, 22, 20, "LPDDR5 16 GB", "bga", "HOLD G02"),
        (52, 52, 22, 14, "UFS 256 GB", "bga", "HOLD G03"),
        (124, 26, 26, 22, "RK806S PMIC", "qfn", ""),
        (124, 54, 20, 14, "RP2350B", "qfn", ""),
        (150, 54, 14, 12, "QSPI 16 MB", "qfn", ""),
        (10, 22, 26, 20, "USB-C PD", "conn", ""),
        (10, 50, 26, 18, "2× GbE PHY", "qfn", ""),
        (170, 20, 32, 26, "Wi-Fi 6E / BT", "shield", ""),
        (170, 54, 32, 16, "M.2 Key-B", "conn", ""),
        (86, 68, 30, 14, "Audio + Sensoren", "qfn", ""),
        (44, 6, 120, 10, "Power-Tree · Rails", "passive", ""),
    ],
    "UI-Carrier": [
        (60, 18, 98, 60, "Display-FPC-Zone (5\" DSI)", "module", ""),
        (14, 24, 34, 34, "Touch-Ring-AFE", "qfn", "HOLD G07"),
        (170, 24, 34, 34, "D-Pad-Matrix", "passive", ""),
        (66, 84, 86, 10, "5 Softkeys", "passive", ""),
        (14, 66, 30, 14, "Haptik-Treiber", "qfn", ""),
        (170, 66, 34, 14, "Status-LEDs", "passive", ""),
        (96, 4, 26, 8, "J_UI", "conn", ""),
    ],
    "HyperRF": [
        (46, 28, 34, 25, "FPGA", "bga", "HOLD G04"),
        (8, 10, 30, 26, "LMS7002M A", "shield", ""),
        (8, 42, 30, 26, "LMS7002M B", "shield", ""),
        (88, 8, 40, 22, "High-Band-Conversion", "shield", ""),
        (88, 34, 40, 16, "5G / NTN-Bay", "module", ""),
        (88, 54, 22, 14, "GNSS L1/L5", "shield", ""),
        (114, 54, 14, 14, "UWB", "shield", "HOLD G05"),
        (46, 8, 34, 16, "Takt kohaerent", "qfn", ""),
        (46, 62, 34, 8, "60-GHz-Radar-Tile", "module", ""),
    ],
    "RF-Core": [
        (6, 8, 24, 18, "CC1101", "shield", ""),
        (34, 8, 24, 18, "SX1262", "shield", ""),
        (62, 8, 24, 18, "CC2652P7", "shield", ""),
        (6, 30, 24, 16, "PN7160 NFC", "shield", ""),
        (34, 30, 24, 16, "LF-RFID-AFE", "qfn", ""),
        (62, 30, 24, 16, "EFR32ZG23", "shield", ""),
        (6, 50, 34, 12, "UHF-RAIN E710", "shield", ""),
        (44, 50, 20, 12, "IR / 1-Wire", "qfn", ""),
        (68, 50, 18, 12, "RF-KILL", "qfn", "SAFETY"),
    ],
    "Antenna-Rail": [
        (12, 4, 10, 10, "SMA 1", "sma", ""),
        (48, 4, 10, 10, "SMA 2", "sma", ""),
        (92, 4, 10, 10, "SMA 3", "sma", ""),
        (128, 4, 10, 10, "SMA 4", "sma", ""),
    ],
    "M.2-Bridge": [
        (4, 6, 22, 16, "PCIe 2.1 ×1", "qfn", ""),
        (4, 26, 22, 12, "USB3-Bruecke", "qfn", ""),
        (4, 41, 22, 7, "J_M2", "conn", ""),
    ],
}


def _part(x, y, w, h, label, kind, status, K, ox, oy, board_h=1e9) -> str:
    """Zeichnet einen Bauteil-Block in PCB-Optik."""
    px, py, pw, ph = ox + x * K, oy + y * K, w * K, h * K
    o = []
    if kind == "bga":
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{0.5 * K}" '
                 f'fill="url(#icGrad)" stroke="#0a0c0e" stroke-width="1.4" '
                 f'filter="url(#tinyShadow)"/>')
        o.append(f'<rect x="{px + 2}" y="{py + 2}" width="{pw - 4}" height="{ph * 0.30}" '
                 f'fill="#fff" opacity="0.055"/>')
        o.append(f'<circle cx="{px + pw * 0.16}" cy="{py + ph * 0.20}" r="{0.7 * K}" '
                 f'fill="#8b949d" opacity="0.55"/>')     # Pin-1-Marke
    elif kind == "qfn":
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{0.35 * K}" '
                 f'fill="url(#icGrad)" stroke="#0a0c0e" stroke-width="1.2" '
                 f'filter="url(#tinyShadow)"/>')
        n = max(3, int(w / 2.4))
        for i in range(n):                                # Gullwing-Pins
            gx = px + pw * (i + 0.5) / n
            o.append(f'<rect x="{gx - 1.1}" y="{py - 2.4}" width="2.2" height="2.4" '
                     f'fill="url(#gold)" opacity="0.85"/>')
            o.append(f'<rect x="{gx - 1.1}" y="{py + ph}" width="2.2" height="2.4" '
                     f'fill="url(#gold)" opacity="0.85"/>')
    elif kind == "shield":
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{0.6 * K}" '
                 f'fill="url(#shield)" stroke="#3f464e" stroke-width="1.3" '
                 f'filter="url(#tinyShadow)"/>')
        for i in range(int(h / 3.2) + 1):                 # Sicken im Blech
            o.append(f'<line x1="{px + 3}" y1="{py + 4 + i * 3.2 * K}" '
                     f'x2="{px + pw - 3}" y2="{py + 4 + i * 3.2 * K}" '
                     f'stroke="#5b636c" stroke-width="0.7" opacity="0.5"/>')
    elif kind == "conn":
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{0.4 * K}" '
                 f'fill="#15181c" stroke="#3a4149" stroke-width="1.3" '
                 f'filter="url(#tinyShadow)"/>')
        n = max(4, int(w / 1.8))
        for i in range(n):
            gx = px + 3 + (pw - 6) * i / max(1, n - 1)
            o.append(f'<rect x="{gx - 0.9}" y="{py + ph * 0.30}" width="1.8" '
                     f'height="{ph * 0.42}" fill="url(#gold)"/>')
    elif kind == "sma":
        o.append(f'<circle cx="{px + pw / 2}" cy="{py + ph / 2}" r="{pw * 0.52}" '
                 f'fill="url(#metal)" stroke="#20262c" stroke-width="1.4"/>')
        o.append(f'<circle cx="{px + pw / 2}" cy="{py + ph / 2}" r="{pw * 0.22}" '
                 f'fill="url(#gold)"/>')
    elif kind == "module":
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{0.5 * K}" '
                 f'fill="#182028" stroke="{ACCENT}" stroke-width="1.3" opacity="0.9" '
                 f'stroke-dasharray="5 3"/>')
    else:  # passive: Feld aus MLCCs
        o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{0.3 * K}" '
                 f'fill="#0b1a16" stroke="#1d3a31" stroke-width="1"/>')
        cols, rows = max(2, int(w / 3.4)), max(1, int(h / 3.4))
        for r in range(rows):
            for c in range(cols):
                cx_ = px + pw * (c + 0.5) / cols
                cy_ = py + ph * (r + 0.5) / rows
                o.append(f'<rect x="{cx_ - 1.6}" y="{cy_ - 0.9}" width="3.2" height="1.8" '
                         f'rx="0.5" fill="#9a7b52" opacity="0.85"/>')
    # Beschriftung (Silkscreen)
    fs = max(9.5, min(15.0, pw / max(6, len(label)) * 1.65))
    # Bei Steckern sitzen mittig die Goldkontakte -- Text daher darueber.
    ty_lab = (py - 4) if kind == "conn" else (py + ph / 2 + fs * 0.34)
    o.append(f'<text x="{px + pw / 2}" y="{ty_lab}" text-anchor="middle" '
             f'font-size="{fs:.1f}" font-family="Inter,Segoe UI,sans-serif" '
             f'fill="#e6edf3" opacity="0.92">{label}</text>')
    if status:
        col = HOLD_RED if status.startswith("HOLD") else AMBER
        # Unter dem Bauteil, solange die Platine dort noch Platz hat -- sonst
        # klappt die Marke nach oben. Andernfalls haengt sie ueber dem
        # Board-Rand und sieht aus, als gehoere sie zum naechsten Board.
        ty_ = (py + ph + 13) if (y + h + 4.2 < board_h) else (py - 5)
        o.append(f'<text x="{px + pw / 2}" y="{ty_}" text-anchor="middle" '
                 f'font-size="11.5" font-family="Inter,Segoe UI,sans-serif" '
                 f'fill="{col}">{status}</text>')
    return "\n".join(o)


def render_boards() -> str:
    K = 3.5                                  # px je mm
    PAD, GAP = 60, 46
    # zweispaltige Anordnung
    rows = [["Mainboard"], ["UI-Carrier"], ["HyperRF", "RF-Core"],
            ["Antenna-Rail", "M.2-Bridge"]]
    bmap = {b[0]: b for b in BOARDS}

    SW = 1600
    y_cur = 210
    body = []
    for row in rows:
        x_cur = PAD + 40
        row_h = 0
        for name in row:
            _, w, h, layers, fill = bmap[name]
            bw, bh = w * K, h * K
            body.append(_board(name, w, h, layers, fill, x_cur, y_cur, K))
            x_cur += bw + GAP + 210
            row_h = max(row_h, bh)
        y_cur += row_h + 96
    SH = int(y_cur + 230)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
         f'viewBox="0 0 {SW} {SH}">', defs_common(K),
         header("Platinen-Set — 6 Boards, massstaeblich zueinander",
                "Outlines FIXED aus manufacturing/BOARD_SET.md · Bauteillage = Floorplan",
                SW, "Floorplan-Konzept · KEIN geroutetes Layout")]
    o += body
    o.append(status_note(PAD, SH - 190, [
        (HOLD_RED, "KEIN LAYOUT: Es existieren nur Floorplan-Boards "
                   "(pcb.current_files_status). Keine Leiterbahnen, keine Pinbelegung."),
        ("#7bd88f", "FIXED — alle sechs Outlines und die 12 Lagen des Mainboards."),
        (AMBER, "TBD — Lagenzahl der uebrigen Boards (Minewing-Review)."),
        (HOLD_RED, "HOLD — LPDDR5-Topologie (G02) · UFS-MPN (G03) · FPGA-MPN (G04) · "
                   "UWB-Suffix (G05) · HDI-Stackup (G06)"),
    ], w=SW - 2 * PAD))
    o.append("</svg>")
    return "\n".join(o)


def _board(name, w, h, layers, fill, ox, oy, K) -> str:
    bw, bh = w * K, h * K
    o = [f'<g filter="url(#softShadow)">',
         f'<rect x="{ox}" y="{oy}" width="{bw}" height="{bh}" rx="{2.5 * K}" '
         f'fill="url(#{fill})" stroke="#04100c" stroke-width="1.6"/>', '</g>']
    # Kupferflaeche + Textur
    o.append(f'<rect x="{ox}" y="{oy}" width="{bw}" height="{bh}" rx="{2.5 * K}" '
             f'fill="#7fd0b0" filter="url(#grain)" opacity="0.30"/>')
    # Montagebohrungen
    for hx, hy in ((3.5, 3.5), (w - 3.5, 3.5), (3.5, h - 3.5), (w - 3.5, h - 3.5)):
        o.append(f'<circle cx="{ox + hx * K}" cy="{oy + hy * K}" r="{1.6 * K}" '
                 f'fill="#05100d" stroke="url(#gold)" stroke-width="1.6"/>')
    # Vias als feines Raster (Andeutung, kein Layout)
    step = 7
    for gx in range(step, int(w), step):
        for gy in range(step, int(h), step):
            if (gx // step + gy // step) % 3:
                continue
            o.append(f'<circle cx="{ox + gx * K}" cy="{oy + gy * K}" r="0.9" '
                     f'fill="#c9a44a" opacity="0.35"/>')
    # Bauteile
    for p in PARTS.get(name, []):
        o.append(_part(*p, K, ox, oy, board_h=h))
    # Silkscreen-Beschriftung des Boards
    o.append(f'<text x="{ox + 9 * K}" y="{oy + bh - 6}" font-size="13" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#cfe3d8" opacity="0.55">'
             f'G4MEOVER ONE-X · {name.upper()}</text>')
    # Bezeichner rechts daneben
    tx = ox + bw + 26
    o.append(f'<text x="{tx}" y="{oy + 24}" font-size="24" font-weight="700" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#eef2f5">{name}</text>')
    o.append(f'<text x="{tx}" y="{oy + 52}" font-size="17" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="{ACCENT}">'
             f'{w:.0f} × {h:.0f} mm</text>')
    o.append(f'<text x="{tx}" y="{oy + 78}" font-size="15" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#8d99a5">{layers}</text>')
    return "\n".join(o)


# --------------------------------------------------------- 3) Innenaufbau

def render_stack(s: dict) -> str:
    """
    Isometrische Explosionsansicht.

    Erster Versuch war unbrauchbar: gerade Platten, zu grosser Massstab und ein
    Versatz kleiner als die Plattenhoehe -- die Ebenen deckten einander zu und
    die Beschriftung lief aus dem Bild. Jetzt bestimmt der Versatz die
    Bildhoehe (nicht umgekehrt), und die Beschriftungen haengen an einer festen
    Spalte rechts statt an der Plattenkante.
    """
    import math
    m = s["mechanical"]
    W = m["device_envelope_mm"]["x"]
    H = m["device_envelope_mm"]["y"]
    Z = m["device_envelope_mm"]["z"]

    K = 2.75                       # px je mm
    TILT = 0.13                    # Neigung der Vorderkante
    DEPTH = 0.52                   # Verkuerzung der Tiefe
    SKEW = 0.34                    # seitlicher Versatz (Isometrie)
    DY = 116                       # Versatz je Ebene
    OX, OY = 210, 300

    # (Beschriftung, Breite, Hoehe, Farbe, Zusatz, Statusmarke)
    layers = [
        ("Frontschale + 5\" Touchpanel", W, H, "#39414a",
         "Recess 138 × 81 · Fenster 112,5 × 64,5 (FIXED)", ""),
        ("UI-Carrier  218 × 100", 218, 100, "#0e2a24",
         "Touch-Ring-AFE · 5 Softkeys · Haptik · Status-LEDs", "AFE HOLD G07"),
        ("Mainboard  210 × 92 · 12 Lagen HDI", 210, 92, "#15191e",
         "RK3576 · RP2350B · PMIC · 2× GbE · USB-C PD", "LPDDR5 G02 · UFS G03"),
        ("HyperRF 136 × 72  +  RF-Core 92 × 66", 210, 78, "#0e2a24",
         "2× LMS7002M · High-Band  |  8 Radios + HW-RF-Kill", "FPGA HOLD G04"),
        ("Akku 2S2P · 4 × 21700 · 72 Wh", 200, 76, "#2a1d10",
         "7,2 V nominal · BQ28Z620-Gauge · Pack-Schutz + NTC", "Compliance HOLD G11"),
        ("Rueckschale + Kuehlung", W, H, "#39414a",
         "Getrennte Spreader Main / HyperRF · 2 Blower", "Thermik HOLD G10"),
    ]

    max_bw = W * K + H * K * SKEW
    LABEL_X = OX + max_bw + 96
    SW = int(LABEL_X + 560)
    SH = int(OY + (len(layers) - 1) * DY + H * K * DEPTH + 300)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
         f'viewBox="0 0 {SW} {SH}">', defs_common(K),
         header("Innenaufbau — Explosionsansicht",
                f"Gehaeuse {W:.0f} × {H:.0f} × {Z:.0f} mm (FIXED) · "
                f"Stapelreihenfolge schematisch",
                SW, "Konzept · Bauraum nicht kollisionsgeprueft")]

    for i, (lab, lw, lh, col, extra, mark) in enumerate(layers):
        bw, bd = lw * K, lh * K * DEPTH
        sh = lh * K * SKEW
        # zentriert ueber der breitesten Ebene
        px = OX + (max_bw - (bw + sh)) / 2
        py = OY + i * DY
        thick = 7 if lw >= 200 else 5

        A = (px + sh, py)
        B = (px + sh + bw, py - bw * TILT)
        C = (px + bw, py - bw * TILT + bd)
        D = (px, py + bd)
        top = f"{A[0]:.1f},{A[1]:.1f} {B[0]:.1f},{B[1]:.1f} {C[0]:.1f},{C[1]:.1f} {D[0]:.1f},{D[1]:.1f}"

        o.append('<g filter="url(#softShadow)">')
        o.append(f'<polygon points="{top}" fill="{col}" stroke="#05080b" stroke-width="1.5"/>')
        o.append('</g>')
        o.append(f'<polygon points="{top}" fill="#9fc4b6" filter="url(#grain)" opacity="0.16"/>')
        # Materialstaerke: Vorderkante + linke Kante
        o.append(f'<polygon points="{D[0]:.1f},{D[1]:.1f} {C[0]:.1f},{C[1]:.1f} '
                 f'{C[0]:.1f},{C[1] + thick:.1f} {D[0]:.1f},{D[1] + thick:.1f}" '
                 f'fill="#000" opacity="0.55"/>')
        o.append(f'<polygon points="{A[0]:.1f},{A[1]:.1f} {D[0]:.1f},{D[1]:.1f} '
                 f'{D[0]:.1f},{D[1] + thick:.1f} {A[0]:.1f},{A[1] + thick:.1f}" '
                 f'fill="#000" opacity="0.38"/>')
        # Glanzkante oben
        o.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" '
                 f'stroke="#fff" stroke-width="1.3" opacity="0.13"/>')

        # Fuehrungslinie zur Beschriftungsspalte
        ax, ay = C[0], C[1] - bd * 0.45
        ly = py + bd * 0.30
        o.append(f'<path d="M {ax:.1f} {ay:.1f} L {LABEL_X - 34:.1f} {ly:.1f} '
                 f'L {LABEL_X - 12:.1f} {ly:.1f}" fill="none" stroke="{ACCENT}" '
                 f'stroke-width="1.4" opacity="0.6"/>')
        o.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="3.4" fill="{ACCENT}" opacity="0.85"/>')

        o.append(f'<text x="{LABEL_X}" y="{ly + 5}" font-size="20" font-weight="700" '
                 f'font-family="Inter,Segoe UI,sans-serif" fill="#eef2f5">{lab}</text>')
        o.append(f'<text x="{LABEL_X}" y="{ly + 29}" font-size="14.5" '
                 f'font-family="Inter,Segoe UI,sans-serif" fill="#8d99a5">{extra}</text>')
        if mark:
            o.append(f'<text x="{LABEL_X}" y="{ly + 50}" font-size="13.5" '
                     f'font-family="Inter,Segoe UI,sans-serif" fill="{HOLD_RED}">{mark}</text>')

        # Ebenennummer links
        o.append(f'<circle cx="{px - 40:.1f}" cy="{py + bd * 0.3:.1f}" r="15" '
                 f'fill="#0e1216" stroke="{ACCENT}" stroke-width="1.5"/>')
        o.append(f'<text x="{px - 40:.1f}" y="{py + bd * 0.3 + 6:.1f}" text-anchor="middle" '
                 f'font-size="16" font-family="Inter,Segoe UI,sans-serif" '
                 f'fill="{ACCENT}">{i + 1}</text>')

    # Bauhoehen-Hinweis
    o.append(f'<text x="{OX - 60}" y="{SH - 250}" font-size="15" '
             f'font-family="Inter,Segoe UI,sans-serif" fill="#6f7b87">'
             f'Bauhoehe gesamt {Z:.0f} mm (FIXED) — Aufteilung auf die Ebenen offen '
             f'bis Mechanik-EVT (Phase 10).</text>')

    o.append(status_note(56, SH - 200, [
        ("#7bd88f", "FIXED — Gehaeuse-Envelope, alle Board-Outlines, "
                    "Akku-Topologie 2S2P / 4× 21700, 12 Lagen Mainboard."),
        (AMBER, "TARGET — 72 Wh Energieinhalt, Zelltyp, Geraetemasse 800–950 g."),
        (HOLD_RED, "HOLD — finale Thermik (G10) · Akku-Transport-/Pack-Compliance (G11) · "
                   "HDI-Stackup (G06) · LPDDR5 (G02) · UFS (G03) · FPGA (G04)"),
        ("#6f7b87", "Stapelreihenfolge und Bauraum sind schematisch — keine Kollisions- "
                    "oder Montagepruefung."),
    ], w=SW - 112))
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Konzept-Renderings erzeugen")
    ap.add_argument("--out", default=str(REPO / "docs" / "graphics" / "renders"),
                    help="Zielverzeichnis fuer die SVGs")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    s = spec()

    files = {
        "one-x_product_front.svg": render_product(s),
        "one-x_board_set.svg": render_boards(),
        "one-x_internal_stack.svg": render_stack(s),
    }
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
        print(f"  geschrieben: {out / name}")
    print(f"\n{len(files)} Rendering(s) in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
