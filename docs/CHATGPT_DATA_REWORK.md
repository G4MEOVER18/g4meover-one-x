# ChatGPT-Daten — Überarbeitungs-Tracker

> **Grundregel:** Das gesamte Ausgangsmaterial stammt aus einem ChatGPT-Handoff (ONE-X EVT6) und ist **nicht** als gesetzt zu betrachten. Jedes Artefakt wird kritisch geprüft, korrigiert und **unabhängig gegen echte Quellen** (Datenblätter, Hersteller-Referenzdesigns, Normen) verifiziert, bevor es als belastbar gilt.
>
> Original eingefroren unter `reference_evt6/` (read-only). Die Arbeitskopien liegen in `spec/`, `docs/`, `hardware/` usw.

## Legende
- 🔴 **offen** — noch nicht überarbeitet, ChatGPT-Stand.
- 🟡 **in Arbeit** — Prüfung läuft.
- 🟢 **verifiziert** — gegen echte Quelle geprüft/korrigiert.

## Artefakt-Status

| Artefakt | Herkunft | Rework-Status | Nächster Prüfschritt |
|---|---|---|---|
| `spec/G4MEOVER-ONE-X_MASTER_SPEC.json` | ChatGPT EVT6 | 🟡 importiert, rebranded | Jeden FIXED/TARGET-Wert gegen Datenblatt prüfen; Quellenspalte ergänzen |
| `spec/BOM.csv` | ChatGPT EVT6 | 🔴 offen | Jede MPN auf Existenz/Verfügbarkeit/Footprint prüfen; „class"-Platzhalter auflösen oder als HOLD |
| `spec/INTERFACE_MATRIX.csv` | ChatGPT EVT6 | 🔴 offen | Gegen RK3576-TRM (Pin-Mux, verfügbare Controller) verifizieren |
| `spec/POWER_TREE.csv` | ChatGPT EVT6 | 🔴 offen | Gegen RK806S-5-Referenz-Rail-Map prüfen (aktuell HOLD) |
| `docs/ARCHITECTURE.md` | eigen (aus EVT6) | 🟡 | Bandbreiten-/PCIe-Aussagen rechnerisch belegen |
| Thermal-Precheck (2D) | ChatGPT EVT6 | 🔴 offen | Modellannahmen offenlegen; als PRELIM behalten bis 3D/Mess-EVT |
| CAD/STEP/STL | ChatGPT EVT6 | 🔴 offen | Bauteilhöhen gegen reale Datenblätter, Kollisionscheck neu rechnen |
| KiCad-Floorplans | ChatGPT EVT6 | 🔴 offen | Als „NOT FOR FAB" behalten; Outlines gegen Spec prüfen |
| Provider-Pakete | eigen (neu) | 🟢 | — (neu erstellt, nicht ChatGPT) |

## Bekannte Prüf-Schwerpunkte (Priorität)
1. **BOM-Verifikation** — „…-class"/„TBD"-Einträge sind ChatGPT-Platzhalter. Jeder muss zu einem realen, verfügbaren Bauteil aufgelöst oder klar als HOLD markiert werden. Höchste Priorität, weil die BOM alles Nachgelagerte trägt.
2. **RK3576-Fähigkeiten** — DSI-Lanes, UFS-Host, PCIe-Version, RGMII-Anzahl, LPDDR5-Support: gegen das offizielle Rockchip-TRM/Datenblatt prüfen, nicht gegen ChatGPT-Behauptung.
3. **RF-Frequenzaussagen** — LMS7002M-Range (100 kHz–3,8 GHz nativ), 6-GHz-Umsetzung, 60-GHz-Radar-Trennung: gegen Lime-/TI-Datenblätter.
4. **Batterie-Rechnung** — 2S2P × 5 Ah × 3,6 V = 72 Wh nachrechnen und Molicel-P50B-Datenblatt bestätigen.
5. **Verbotene Claims** — `spec_validator.py` läuft bei jeder Änderung; hält ChatGPT-typische Übertreibungen (Gen3 ×4, DC-60GHz-SDR …) draußen.

## Vorgehen je Eintrag
Prüfen → korrigieren/bestätigen → Quelle notieren → Status 🟢 → Worklog-Eintrag → Validator → Commit.
