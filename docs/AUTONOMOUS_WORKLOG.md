# G4MEOVER ONE-X — Autonomes Arbeitsprotokoll

> Dieses Projekt hat **absolute Priorität** und wird autonom kontinuierlich vorangetrieben.
> Jede Session trägt hier ihren Fortschritt ein (neueste oben). Regeln in `CLAUDE.md`.

## Arbeitszyklus (jede Session)
1. `docs/ROADMAP.md` öffnen → höchste unerledigte Phase / nächstes Gate.
2. Master-Spec lesen, betroffene FIXED/TARGET/HOLD prüfen (nichts raten).
3. **Einen** kohärenten Engineering-Schritt umsetzen.
4. `python tools/spec_validator.py` (muss Exit 0 liefern).
5. Diesen Worklog + Roadmap-Status fortschreiben, committen, pushen.

---

## 2026-08-28 — Session 2 (Rework-Direktive + Design-Neuaufbau, Teil 1)

**Neue Owner-Direktive (2026-08-28):** Das Projekt wird **komplett neu umgesetzt** — „alles überarbeiten, auch designtechnisch". Vier Design-Ebenen betroffen (Industrie-/Produktdesign, Visual-/Marken-Auftritt, Engineering-Architektur, Software-/UI). Vorgehen: **sofort autonom bauen**. **Design-Orientierung: letzte ChatGPT-Vorlagen** (`ONE-X_EVT6_VERIFIED_GRAPHICS_PACKAGE`, `…MASTER_ALL_FILES…2026-08-27`). **Alle KiCad/PCB-Dateien = Vorerzeugnisse** (Drafts), nicht als final behandeln. HOLD-Disziplin bleibt ([[feedback-chatgpt-data-rework]], [[feedback-no-unconfirmed-partners]]).

**ChatGPT-Design-Vorlagen gesichtet (verbindliche Formsprache):** Querformat-Handheld, Touch-Ring Ø40 links · 5″-Display mittig (Bezel) · D-Pad rechts · 5 Softkeys unten · 4× SMA oben. Interface-Architektur = RK3576-Hub mit sichtbaren HOLD-Badges an LPDDR5/UFS.

**Umgesetzt:**
- **`docs/graphics/front_layout.svg` komplett neu** — vorher inkonsistentes **Hochformat**, jetzt maßstäbliches **Querformat** (1 mm = 8 px), exakt in ChatGPT-EVT6-Formsprache. Alle Maße FIXED aus Master-Spec (Envelope 230×110×64, Recess 138×81, Fenster 112,5×64,5, Ring Ø40, D-Pad 34×34, 5 Softkeys, 4× SMA). Titelblock + Bemaßung (230/110 mm) + Provenienz + FIXED/HOLD-Legende.
- **`docs/graphics/architecture.svg` komplett neu** — professionelles System-Diagramm, 4 farbkodierte Domänen (Compute/Control/HyperRF/RF-Core), HOLD an LPDDR5 (Gate G02) und UFS (Gate G03) sichtbar gebadged, HyperRF-FPGA→G04-HOLD markiert. Host-I/O-Subpanel, Bus-Labels, Legende, Provenienz.
- **`docs/graphics/rf_coverage.svg` komplett neu** — professionelles Spektrum (log-Achse 100 kHz–100 GHz), Bänder nach **Reifegrad-Status** gefärbt (FIXED/VALIDATED_ARCH/TARGET/HOLD) statt nach Optik, nach Domänen gruppiert (HyperRF/RF-Core/Spezial), inkl. **Forbidden-Claim-Guard-Box** (kein 60-GHz-SDR, UWB-Suffix HOLD/G05, GNSS nur L1/L5, FPGA HOLD/G04). Jedes Band mit MPN-„-Klasse"-Bezeichnung.
- Alle drei Grafiken via Edge-Headless gerendert und visuell verifiziert.

**Sponsor-Compliance (Owner-Freigabe „De-Claim + entfernen"):** `providers/` aus Public-Repo entfernt (Unterlagen privat unter `C:\Data\KI\_private_one-x\providers\`); „Sponsor aktiv"→„Outreach/keine Zusage" in README/Präsentation/CLAUDE/ROADMAP. Grund: Validator scannt NUR Spec-Claims, nicht den Doku-Fließtext.

**Validator:** `python tools/spec_validator.py` → Exit 0 (FIXED=47, HOLD=8, TARGET=17; keine verbotenen Claims).

**Nächster Schritt (Session 3):** `presentation/index.html` (inline-SVGs) an die neuen Vorlagen angleichen; parallel Phase 1/G01 `linux/`-Display-Bringup-Skelett beginnen (Device-Tree + DSI-Panel-Checkliste RK3576 + 5″ 720×1280).

**Offene HOLDs (unverändert):** LPDDR5-Topologie (G02), UFS-MPN (G03), FPGA-MPN (G04), DW3000-Suffix (G05), HDI-Stackup (G06), finale Thermik (G10), Akku-Compliance (G11).

---

## 2026-08-27 — Session 1 (Projektgründung)
**Umgesetzt (Phase 0 ✅):**
- Repo `flipper/g4meover-one-x` angelegt (Public Open-Source, GitHub G4MEOVER18).
- Rebranding EVT6 → **G4MEOVER ONE-X**; Master-Spec als Single Source of Truth importiert.
- `tools/spec_validator.py` (FIXED/TARGET/HOLD-Auswertung + forbidden-claim-Scan + derived docs).
- Flaggschiff-README, CLAUDE.md, ARCHITECTURE, ROADMAP (G01–G11), COMPARISON (vs. Flipper One), LICENSE (CERN-OHL-S / MIT / CC-BY-SA).
- Sponsor-Pakete PCBWay + Minewing (Mail-Vorlagen + Datenpakete + Versand-Anleitung).
- Konzept-Präsentation (Artifact) + Konzept-Grafiken (SVG).
- Branding-Tokens/Logo.

**Nächster Schritt (Session 2):** Phase 1 / G01 vorbereiten — Display-Bringup-Plan:
`linux/` Device-Tree-Skelett + DSI-Panel-Bringup-Checkliste für RK3576 + 5″ 720×1280,
sowie `firmware/rp2350/` Modul-/Protokoll-Architektur (Phase 2) als parallelen Strang.

**Offene HOLDs (unverändert, nicht raten):** LPDDR5-Topologie, UFS-MPN, FPGA-MPN, DW3000-Suffix, HDI-Stackup, finale Thermik, Akku-Compliance.
