# CLAUDE.md — G4MEOVER ONE-X

## 0. Rolle & Auftrag

Du arbeitest an **G4MEOVER ONE-X**, einem realen Hardware-/Produkt-Engineering-Projekt (Codename ONE-X, Marke G4MEOVER, Owner Yanis Ameseder / G4MEOVER18). Ziel: das synchronisierte EVT6-Konzept in einen fertigbaren, testbaren Linux-Handheld überführen — bei konsequenter Revisionskonsistenz.

**Dieses Projekt hat absolute Priorität und soll autonom kontinuierlich vorangetrieben werden.** Bei jeder Session: `docs/AUTONOMOUS_WORKLOG.md` lesen, nächsten offenen Punkt aus `docs/ROADMAP.md` ziehen, einen kohärenten Schritt umsetzen, Worklog fortschreiben.

Behandle dieses Repository als Engineering-Projekt, nicht als Brainstorming.

## 1. Die eine Regel über allem

Die verbindliche Projektdefinition ist:

`spec/G4MEOVER-ONE-X_MASTER_SPEC.json` — **Single Source of Truth.**

Kein CAD, KiCad, BOM, Mail, Diagramm, Doku, Code oder Grafik darf ihr widersprechen. Bei Änderung eines FIXED/TARGET/HOLD-Werts:

1. betroffene Spec-Keys identifizieren,
2. Auswirkung erklären,
3. Master-Spec zuerst aktualisieren,
4. abgeleitete Artefakte nachziehen,
5. `python tools/spec_validator.py` laufen lassen,
6. Revision dokumentieren.

**Nie still das Design ändern. Fehlende Herstellerdaten nie erfinden — HOLD setzen.**

## 2. Status-Semantik

FIXED · VALIDATED_ARCH · TARGET · HOLD · DEFERRED (Definitionen in der Master-Spec).
Ein HOLD muss in Code, Docs, Schaltplänen, BOMs, Grafiken und Providerdaten sichtbar HOLD bleiben.

## 3. Arbeitsweise pro Schritt

1. Master-Spec lesen. 2. Betroffene FIXED/TARGET/HOLD prüfen. 3. Unklares nicht raten.
4. Eine kohärente Änderung. 5. Bei Architekturänderung Source of Truth zuerst.
6. Abgeleitetes nachziehen. 7. Validator laufen lassen. 8. Berichten: was, warum, betroffene Dateien, neue Risiken, verbleibende HOLDs.

Kleine, prüfbare Schritte statt riesiger unverifizierter Rewrites.

## 4. Release-Gates

Keine Produktions-Gerber/CPL für das direkte RK3576-Mainboard, bevor die Gates in `docs/ROADMAP.md` (G01–G11) geschlossen sind. Aktueller Schwerpunkt: G01 (Display-Bringup), G06 (PCBWay-HDI-DFM, Sponsor aktiv), G04 (FPGA-Auswahl).

## 5. Provider / Sponsoren

`providers/pcbway/` und `providers/minewing/` enthalten Mail-Vorlagen + Datenpakete. **Mails werden nicht autonom versendet** — Vorlagen bereitstellen, Versand macht der Owner.

## 6. Dateiregeln

Vollständige korrigierte Dateien schreiben (keine Fragmente). Generierte Dateien reproduzierbar aus Quelle halten. Engineering-Annahmen kommentieren. Nie still ein Bauteil durch ein anderes ersetzen. Nie ein HOLD in eine Tatsache verwandeln. Provenienz-/Versions-Header wo sinnvoll.

## 7. Sprache

Antworten und Doku auf **Deutsch** (Fachbegriffe/Identifier im Original). Vollständige Orthografie inkl. Umlaute.
