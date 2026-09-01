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

## 2026-09-01 — Session 12 (Board-Schaltpläne: UI-Carrier / M.2-Bridge / Antenna-Rail)

**Umgesetzt:** die drei **nicht-HOLD-blockierten** Board-Schaltpläne als Design-Spec (gleiche Methodik wie Mainboard/RF-Core) — damit ist der Schaltplan-Satz für **5 von 6 Boards** komplett (nur HyperRF bleibt FPGA-/HOLD-blockiert bis G04).
- **`hardware/ui-carrier/schematic/`** (218×100) — README + 4 Sheets. Kern-Designentscheidung: **Zwei-Domänen-Trennung** über einen `J_UI` — Anzeige/kap. Touch → RK3576 (DSI+I²C), physische Bedienung (Ring/D-Pad/5 Softkeys/Haptik/LEDs) → **RP2350** (funktioniert vor/ohne Linux, für Wake/Recovery/RF-Kill-Bestätigung). Sheet 01 DSI/Backlight · 02 Touch(GT911-Klasse, Adress-Strapping-Gotcha) · 03 Ring-AFE/D-Pad/Softkeys · 04 Haptik/Status-LED (`LED_RFKILL` aus RP2350, nicht Linux)/`J_UI`.
- **`hardware/m2-bridge/schematic/`** (30×52) — README + 2 Sheets. High-Speed-Brücke **PCIe 2.1 ×1 + USB3** (FIXED; **kein** Gen3 ×4). Sheet 01 PCIe/USB3-Diff-Paare + AC-Kopplung + RefClk · 02 Sideband(PERST/CLKREQ/WAKE) + Power inkl. `HYPERRF_AUX_5V`-Durchführung + TPs.
- **`hardware/antenna-rail/schematic/`** (150×18) — README + 1 Sheet. **Genau 4× SMA** (Forbidden „10+ SMA" respektiert), 50-Ω-Feeds, Pi/L-Matching- + SAW-Footprints (DNP bis G09), ESD je Port, Masse-Rückführung. Band-/Radio-Zuordnung je SMA = TBD 📄; Matching wird **auf realer HW getunt (G09)**, nie nur Simulation.

**Statusdisziplin durchgehend:** Busse/Signale FIXED aus Spec; alle Herstellerwerte (DSI-Timings, Touch-Register, Ring-AFE-MPN, AC-Cs, Steckertyp/-höhe, Matching-Werte) sichtbar `TBD 📄`/TARGET statt geraten. Kein Gate geschlossen. Validator Exit 0.

**Nächster Schritt (Session 13+):** (a) KiCad-Zeichnung aus den fertigen Mainboard-/RF-Core-Specs beginnen (Richtung G07 ERC), (b) HyperRF-Schaltplan-Sheets, soweit **nicht** FPGA-abhängig (LMS-Analog-Frontend, Power, Clock), vorbereiten, (c) auf Vendor-Rückmeldungen (PCBWay/Minewing) warten und HOLDs schließen.

---

## 2026-09-01 — Session 11 (Phase 8 / Gate G04 — HyperRF-FPGA Scored Candidate Matrix)

**Kontext-Fix zuerst:** Session 10 (RF-Core-Schaltplan) war committet (`a54e006`), aber **nicht** im Worklog dokumentiert — siehe Nachtrag unten (Session 10). Kein Code-Verlust, nur Protokoll nachgezogen.

**Umgesetzt (`hardware/hyperrf/fpga-selection/` angelegt):** das **Entscheidungs-Gerüst für G04** — bewusst kein MPN geraten (Forbidden-Claim „Zynq UltraScale+ unless explicitly frozen"; Spec `hyperrf.fpga` = HOLD).
- `README.md` — Zweck von G04, warum Scored-Matrix (nicht „aus altem Bild wählen"), Ablauf Knockout-Filter → gewichtete Bewertung → Freeze, Bezug zu Host-Limit (PCIe 2.1 x1) + RF-Kill-unabhängigkeit.
- `REQUIREMENTS.md` — aus Master-Spec **abgeleitete** Hard-/Soft-Anforderungen: PCIe-2.1-x1-Endpoint (Hard-IP bevorzugt), digitale IQ-Anbindung 2× LMS7002M (LML-LVDS, Lane-Zahl = TBD je Modus), DSP/BRAM für 4-Kanal-Dezimation/Channelization, Timestamping (10 MHz + PPS), **Power-Deckel** (Handheld/Dual-Blower), Package/Thermik, Verfügbarkeit/Lifecycle, Toolchain-Offenheit (Open-Source-Projekt).
- `SCORING_MODEL.md` — Knockout-Kriterien (K1–K5, sofortiges Aus) + 8 gewichtete Score-Achsen mit Rubrik 0–5 und **begründeter Default-Gewichtung** (Power/Thermik & Verfügbarkeit hoch für ein Batterie-Handheld; explizit als Owner-Entscheidungspunkt markiert, überschreibbar).
- `CANDIDATE_MATRIX.csv` — Matrix-Skelett: Kriterien × Kandidaten-**Familien** (Artix-/ECP5-/PolarFire-/Agilex-Klasse als Platzhalter-Spalten), **alle** herstellerspezifischen Zellen `TBD` — zu füllen aus Datenblatt/Verfügbarkeit, nicht geraten.
- `score.py` — liest die CSV, rechnet gewichtete Summe **nur** wenn Zellen belegt sind; bei `TBD` → Ausgabe „INSUFFICIENT DATA — HOLD" statt Scheinergebnis. Knockout-Spalten disqualifizieren hart.

**Statusdisziplin:** `hyperrf.fpga` bleibt **HOLD**; kein Gate geschlossen. Das Framework produziert die Entscheidung erst, wenn reale Werte eingetragen sind (Vendor-Docs / Verfügbarkeit / Power-Messung). Validator Exit 0.

**Owner-Entscheidung getroffen (2026-09-01):** Gewichtungs-Haltung **„Maximal hackbar"** gewählt → **S4 Toolchain-Offenheit dominant = 30** (Rest: S2=14, S8=12, S5=10, S3=10, S1=8, S6=8, S7=8; Summe 100). In `CANDIDATE_MATRIX.csv` + `SCORING_MODEL.md` eingetragen. Bewusst dokumentiertes Spannungsfeld: offenste Toolflows (Yosys/nextpnr) decken v. a. kleinere Familien ab, die bei K1 (PCIe-Hard-IP)/K3 (DSP/BRAM) eng werden können — die Knockout-Filter haben Vorrang vor dem S4-Gewicht.

**Nächster Schritt (Session 12+):** (a) Owner-Gewichtung bestätigen/anpassen → Kandidaten-Zellen mit Datenblattwerten füllen (sobald Vendor-Verfügbarkeit bekannt), (b) restliche Board-Schaltpläne als Design-Spec: UI-Carrier / M.2-Bridge / Antenna-Rail (nicht HOLD-blockiert), (c) KiCad-Zeichnung aus Mainboard-/RF-Core-Specs beginnen (Gate G07).

---

## 2026-08-28 — Session 10 (RF-Core-Schaltplan — 7 Sheets, Sicherheit zuerst) [Nachtrag]

> Nachträglich protokolliert in Session 11 — der Code war bereits committet (`a54e006`), der Worklog-Eintrag fehlte.

**Umgesetzt (`hardware/rf-core/schematic/` angelegt):** kompletter RF-Core-Schaltplan-Design-Spec-Satz (Board 92×66 mm), gleiche Methodik wie Mainboard.
- `README.md` — Sheet-Index (7), Host-Anbindung über `J_RFCORE`, Netz-Konventionen, **Sicherheits-Grundsatz: Sheet 01 zuerst** (RF-Kill gatet alle PA/TX-Enables).
- `sheet_01_supervisor_rfkill.md` — **sicherheitskritisch**: hardware-erzwungener TX-Disable-Pfad, Default nach Reset = Kill aktiv, softwareunabhängig (fail-safe), Autorität = RP2350; jedes Radio muss seinen PA/TX-Enable explizit über `PA_EN_<radio>` führen (ERC-Review-Punkt).
- `sheet_02_subghz.md` (CC1101 U500 + SX1262 U501) · `sheet_03_24ghz_zwave.md` (CC2652P7 U502 + EFR32ZG23 U503) · `sheet_04_nfc_lfrfid.md` (PN7160 U504 + LF-AFE U505) · `sheet_05_uhf_rain.md` (Impinj E710 U506) · `sheet_06_ir_1wire.md` (IR-TX/RX + 1-Wire) · `sheet_07_power_host_antennas.md` (Rails, SPI/UART, Antennen-Feeds, Testpoints).

**Statusdisziplin:** Kern-Radios FIXED; Z-Wave/LF-AFE/UHF/IR TARGET, regionale RF-Matching-Werte auf realer HW (G09), nie nur Simulation. Validator Exit 0.

---

## 2026-08-28 — Session 9 (Mainboard-Schaltplan — alle 18 Sheets als Design-Spec)

**Umgesetzt:** Der komplette Schaltplan-Design-Spec-Satz für das Mainboard (`hardware/mainboard/schematic/`) — 16 Entwurfs-Sheets + 2 ehrliche Platzhalter:
- **Fundament:** 01 Power-Tree · 02 RK806S-PMIC · 03 RK3576-Core.
- **Speicher (blockiert):** 04 LPDDR5 (G02) · 05 UFS (G03) — Platzhalter mit Anforderungen + „was zum Schließen gebraucht wird", nicht geroutet.
- **Boot/Debug:** 06 Recovery/SPI-NOR · 16 Debug/Recovery (RK3576-Maskrom + RP2350-BOOTSEL getrennt).
- **I/O:** 07 USB-C-PD/USB3/DP · 08 USB-Host · 09 HDMI/DP-Out · 10 Ethernet×2 · 11 Wi-Fi 6E/BT · 12 M.2/HyperRF (PCIe 2.1×1+USB3) · 13 RP2350-Link.
- **Peripherie:** 14 Audio · 15 Sensoren.
- **Integration:** 17 Connectors (Inter-Board) · 18 Testpoints (gestaffelter Bring-up).

**Disziplin durchgehend:** Struktur/Netze/ERC-Absicht vollständig; jeder Herstellerwert (Ball-/Rail-Map, DSI-/RGMII-Timings, Boot-Straps, Wi-Fi-Bus) bleibt sichtbar `TBD 📄`/HOLD statt geraten. Forbidden-Claims respektiert (kein Gen3×4, kein 6-Layer, UFS/LPDDR5 nicht produktionsbestätigt).

**Ergebnis:** Schaltplan-Design-Spec strukturell **vollständig** → bereit für KiCad-Zeichnung + Minewing-ERC-Review (Gate G07). Vor „ERC clean": bestätigte 📄/HOLD-Werte einsetzen, 04/05 nach G02/G03 vervollständigen.

**Nächster Schritt (Session 10+):** je nach Owner-Wunsch — (a) KiCad-Zeichnung aus den Design-Specs beginnen, (b) RF-Core-/HyperRF-Schaltpläne analog aufbauen, (c) G04 FPGA-Scored-Candidate-Matrix, (d) auf Vendor-Rückmeldungen (PCBWay/Minewing) warten und HOLDs schließen.

---

## 2026-08-28 — Session 8 (Phase 5 Kickoff — Mainboard-Schaltplan)

**Umgesetzt (`hardware/mainboard/schematic/` angelegt):**
- `README.md` — Schaltplan-Methodik (reviewbare Design-Spec je Sheet statt sofort KiCad → SoT-Disziplin bleibt), **18-Sheet-Index** mit Status, **Netz-/Power-Namenskonvention** (aus POWER_TREE.csv), Impedanz-/SI-Ziele (50 Ω SE / 90 Ω / 100 Ω diff), ERC-Absicht (G07). Sheets 04 (LPDDR5) + 05 (UFS) bewusst **⛔ blockiert** bis G02/G03.
- `sheet_01_power_tree.md` — erstes fundamentales Sheet: Blockfluss (USB-C-PD → Charger → VSYS → Rails), Netz-Tabelle, Kern-Bauteile (TPS25751A/BQ25792/BQ28Z620/RK806S), kritische Notizen (Sequencing, +3V3_AON-immer-an für RP2350, IR-Drop 10 A, RF-Kill-Bezug), ERC-Absicht, HOLD (RK806S-Rail-Map).

**Methodik-Entscheidung:** Schaltplan als versionierbare Design-Spezifikation (diff-bar, HOLD sichtbar); KiCad-Zeichnung wird daraus deterministisch. Basis für Minewing-ERC-Review (G07).

**Nächster Schritt (Session 9+):** restliche Sheets sheet-für-sheet — als Nächstes Sheet 03 (RK3576-Core) + Sheet 02 (RK806S-PMIC, Rail-Map-Anforderungen), dann RP2350-Link/USB-C-PD/Ethernet/M.2 usw. Sheets 04/05 bleiben Platzhalter bis G02/G03.

---

## 2026-08-28 — Session 7 (Fertigungs-Handoff-Paket — `manufacturing/`)

**Owner-Direktive:** Produkt fertigungsbereit machen, um es an die **zwei Firmen** (PCBWay + Minewing) weiterzugeben. Rückfrage geklärt: **„Paket + Schaltplan selbst bauen"**, **EVT 1–3 Einheiten**, Ownership Hybrid (Annahme).

**Ehrliche Einordnung (dem Owner offengelegt):** Finale Gerber/CPL sind **nicht** seriös erzeugbar — G02(LPDDR5)/G03(UFS)/G04(FPGA)/G06(Stackup) sind HOLD und werden **genau von den zwei Firmen** geschlossen. Der korrekte Übergabestand ist ein **DFM-/RFQ- + Engineering-Handoff-Paket**, nicht geratene Gerber.

**Umgesetzt (`manufacturing/` angelegt, vorher leer):**
- `README.md` — Handoff-Hub + EVT-Umfang (1–3) + Ownership + „was NICHT hier ist".
- `MANUFACTURING_READINESS_REVIEW.md` — Gate-für-Gate-Reifegrad-Scorecard (🟢/🟡/🔴), wer schließt was, Forbidden-Claims-Guard.
- `BOARD_SET.md` — 6-Board-Set (Mainboard 210×92/12L-HDI, HyperRF 136×72, RF-Core 92×66, UI-Carrier 218×100, M.2-Bridge 30×52, Antenna-Rail 150×18), Verbindungen, kritische Layout-Themen.
- `DFM_RFQ_PCBWAY.md` — sende-fertige PCB-/DFM-RFQ mit **präzisen Stackup-/Impedanz-/Microvia-Fragen** (G06).
- `ENGINEERING_HANDOFF_MINEWING.md` — JDM-Scope + **Sourcing-Aufträge für die HOLD-Teile** (G02/G03/G04/G05/G11) + Review-Umfang.
- `BOM_EVT.csv` — vollständige Fertigungs-BOM (45 Positionen) mit Status + **Sourcing_Owner + Gate** je Position.

**Validator:** Exit 0.

**Nächster Schritt (Session 8):** Phase 5 starten — Produktions-Schaltplan (`hardware/schematic/`): Sheet-Plan (18 Sheets) + Netz-/Power-Definitionen, sheet-für-sheet als reviewbare Design-Spezifikation (Basis für KiCad-Zeichnung + Minewing-ERC-Review, Gate G07).

---

## 2026-08-28 — Session 6 (Software-/UI-Ebene — ONE-X-Launcher-Konzept)

**Umgesetzt (`linux/ui/` angelegt) — schließt die 4. Design-Ebene:**
- `linux/ui/mockup_home.svg` — Launcher-Home-Mockup in nativer Landscape-Auflösung (1280×720). Vier farbkodierte Funkdomänen (identische Farben wie `architecture.svg`), RF-Kill-Status prominent in der Statusleiste (rot = aktiv, aus RP2350-Heartbeat), HOLD/TARGET-Reife als Micro-Badge (FPGA G04, 5G/NTN, Kern FIXED, RP2350-Telemetrie), 5 Softkeys + Touch-Ring/D-Pad-Hinweise. Via Edge-Headless gerendert/verifiziert.
- `linux/ui/README.md` — Leitidee (UI spiegelt Hardware-Realität + Reife), Eingabemodell (Touch / Touch-Ring / D-Pad / 5 Softkeys, blindbedienbar), Informationsarchitektur, **Firmware-Anbindung** (UI = Consumer der RP2350-Telemetrie über ONE-X-Link; RF-Kill-Freigabe = Policy-Anfrage, kein Toggle), Umsetzungs-Skizze (Wayland+SW-Rotation, App-Framework TARGET).

**Statusdisziplin:** Explizit „Konzept, keine Implementierung bis G01 real läuft". App-Framework = TARGET (Auswahl nach Perf-Messung).

**Damit alle 4 Owner-Design-Ebenen adressiert:** Visual/Marke ✅ · Industrie-Design ✅ · Engineering-Architektur (Diagramm+G01+Phase2) ✅ · Software/UI ✅.

**Nächster Schritt (Session 7):** Engineering-Tiefe — Phase 3 Vendor-Docs/Core-BOM-Freeze vorbereiten (G02 LPDDR5-Topologie / G03 UFS-MPN: Anforderungs-/Recherche-Templates, ohne zu raten), oder G04 FPGA-Scored-Candidate-Matrix-Gerüst.

---

## 2026-08-28 — Session 5 (Industrie-Design — CadQuery-Gehäuse spec-getrieben)

**Befund:** `mechanical/generate_enclosure.py` war bereits im **korrekten Querformat** und maßlich spec-konform (230×110×64, Fenster 112,5×64,5, Ring Ø40, Boards 210×92/136×72/92×66, Rail 150×18, Akku 2S2P/4×21700) — anders als das alte Front-SVG. Fehlend war **Spec-Rückverfolgbarkeit + HOLD-Disziplin**, plus ein Export-Bug.

**Umgesetzt (Geometrie unangetastet, nur nachvollziehbar/ehrlich gemacht):**
- Modul-Docstring mit Provenienz (Master-Spec = SoT), Querformat-Formsprache, Status-Legende.
- Jeder Maß-Parameter mit Spec-Key + Status getaggt (FIXED/TARGET/HOLD inline).
- **HOLD-Banner** an Thermik (Spreader/Fans → Gate G10) und Akku-Pack-Compliance (→ Gate G11): explizit „Kollisions-/Bauraum-Referenz, nicht validiert".
- **Bugfix:** `fan2` wurde erzeugt + in Assembly genutzt, aber nie als Teil exportiert → jetzt beide Blower exportiert (`fan_30x30x5_dummy_1/_2`).
- Bounding-Box-Plausibilitätsprüfung + HOLD-Erinnerung am Skriptende (Warnung bei Envelope-Überschreitung).
- `mechanical/README.md` neu (Erzeugen, Formsprache, Status-Tabelle).

**Validierung:** `python -m py_compile` OK (CadQuery hier nicht installiert; Laufzeit-Erzeugung nicht getestet — Geometrie-Logik unverändert). Spec-Validator Exit 0.

**Nächster Schritt (Session 6):** Software-/UI-Ebene — ONE-X-Launcher-/UI-Konzept für 5″-Touch (Landscape); danach ggf. Phase 3 Vendor-Docs/Core-BOM-Freeze (G02/G03) vorbereiten.

---

## 2026-08-28 — Session 4 (Phase 2 — RP2350B System-Manager-Architektur)

**Umgesetzt (`firmware/rp2350/` angelegt, vorher leer):**
- `README.md` — Rolle (FIXED: Always-On, power/wake/buttons/sensors/haptik/fans/status/debug, **kein** Linux-Framebuffer), Nicht-Ziele, Statusdisziplin (alle Pins HOLD → pin-unabhängige Verträge).
- `ARCHITECTURE.md` — kooperatives tickbasiertes Ausführungsmodell (Core0-Superloop, Core1 für Echtzeit/RF-Kill-Latch), 12-Modul-Landkarte nach Sicherheitspriorität, System-Zustandsmaschine (OFF/BOOT/RUN/SUSPEND/SHUTDOWN/FAULT), Watchdog-Politik, **RF-Kill-Grundsatz** (HW-erzwungen, Default nach Boot/Reset/Fault = Kill aktiv).
- `PROTOCOL.md` — ONE-X-Link v1: Framing (SOF `0xA5 0x5A`, VER/TYPE/SEQ/LEN/CRC-16-CCITT), Zuverlässigkeit (ACK/NACK+SEQ), vollständiges Nachrichten-Set (Host→Mgr Kommandos, Mgr→Host Events), sicherheitskritische RF-Kill-Semantik (Manager = Autorität, Freigabe nur mit Regulierungsprofil+Token).
- `include/onex_proto.h` + `include/onex_modules.h` — kompilierbare C-Verträge (Frame/Enums/CRC-Proto; Modul-Interface init/tick/event). **gcc-Syntaxcheck OK** (`-std=c11 -Wall -Wextra`).

**Bewusst pin-unabhängig:** keine GPIO-/Bus-Zuordnungen erfunden (HOLD bis Mainboard-Schaltplan, Gate G07); HAL-Schicht folgt in Phase 5.

**Validator:** Exit 0 (nur Dateien hinzugefügt).

**Nächster Schritt (Session 5):** Industrie-Design vertiefen (`mechanical/generate_enclosure.py` an neue Front-Geometrie/Formsprache angleichen) **oder** Software-/UI-Ebene (ONE-X-Launcher-Konzept für 5″-Touch, Landscape).

---

## 2026-08-28 — Session 3 (Phase 1 / G01 — Linux-Display-Bringup-Skelett)

**Umgesetzt (`linux/` angelegt, vorher leer):**
- `linux/README.md` — Linux-Plattform-Strategie + G01-Scope; klare FIXED/TARGET/HOLD-Tabellen (Display-Fähigkeit FIXED, Treiber/Bringup HOLD via `display.driver_gate`).
- `linux/BRINGUP_CHECKLIST_G01.md` — 8-stufige Bringup-Checkliste (Panel-Power → DSI/PHY → DT-Overlay → DRM/KMS-Modeset → SW-Rotation Landscape → Touch-I²C → Suspend/Resume → Abschluss). Jede Stufe mit ✅-Kriterium; G01 gilt erst bei HW-Nachweis geschlossen.
- `linux/device-tree/rk3576-one-x-panel5.dtso` — Device-Tree-Overlay-**Skelett** (Panel ILI9881C-Klasse + Touch GT911-Klasse). Alle unsicheren Stellen als `VERIFY` (Node-Labels vs. RK3576-BSP) bzw. `HOLD 📄` (Pins, DSI-Timings, Init-Sequenz aus Datenblatt) markiert. FIXED-Werte (720×1280, 4 Lanes, Touch-I²C) gesetzt.
- `linux/device-tree/Makefile` — cpp+dtc-Build (KDIR auf RK3576-Kernelbaum anpassen).
- `linux/panel/PANEL_CANDIDATE.md` — Panel-/Touch-Datenpunkte; benötigte Datenblatt-Werte als TBD/HOLD gelistet (nicht geraten).

**Bewusst NICHT getan:** Gate-Status **nicht** geändert — G01 bleibt „offen", `display.driver_gate` bleibt HOLD (kein HW-Nachweis vorhanden). Keine DSI-Timings/Node-Labels erfunden.

**Validator:** Exit 0 (nur Dateien hinzugefügt, keine Spec-Änderung).

**Nächster Schritt (Session 4):** Wahlweise (a) Phase 2 `firmware/rp2350/`-Modularchitektur (power/wake/buttons/touch_ring/haptik/sensors/fan/battery/watchdog/rk3576_link/recovery/rf_kill/protocol), oder (b) Industrie-Design vertiefen: `mechanical/generate_enclosure.py` (CadQuery-Gehäuse) an neue Formsprache/Front-Geometrie angleichen, oder (c) Software-/UI-Ebene: ONE-X-Launcher-Konzept.

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

- **`presentation/index.html` synchronisiert** — drei veraltete Inline-SVGs (u.a. das falsche Hochformat-Frontlayout + alte RF-Grafik) durch externe `<img>`-Referenzen auf die neuen `docs/graphics/*.svg` ersetzt → eine Quelle pro Grafik, Präsentation bleibt automatisch synchron. `.fig img`-CSS ergänzt, `.tall` beim jetzt querformatigen Frontlayout entfernt. Ganze Seite via Edge-Headless gerendert/verifiziert (alle 3 Diagramme laden, Layout konsistent, Partner-Abschnitt de-claimed).
  - Hinweis: Bei späterer Artifact-Veröffentlichung (strikte CSP, keine externen Refs) müssten die SVGs wieder inline oder als data:-URI eingebettet werden. Für lokal/Repo/Pages ist die `<img>`-Referenz korrekt.

**Nächster Schritt (Session 3):** Phase 1/G01 `linux/`-Display-Bringup-Skelett beginnen (Device-Tree-Overlay-Struktur + DSI-Panel-Bringup-Checkliste RK3576 + 5″ 720×1280, Touch-I²C, Suspend/Resume); danach `firmware/rp2350/`-Modularchitektur (Phase 2).

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
