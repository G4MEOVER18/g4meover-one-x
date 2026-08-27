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
