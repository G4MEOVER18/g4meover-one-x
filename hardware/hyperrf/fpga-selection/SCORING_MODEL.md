# HyperRF-FPGA — Scoring-Modell

Zwei Stufen: **Knockout** (hart, bestanden/durchgefallen) → **gewichteter Score** (0–5 je Achse × Gewicht).

## Stufe 1 — Knockout-Kriterien (K1–K5)

Reißt ein Kandidat **eine** Hard-Anforderung, ist er raus — unabhängig vom Score. Bewertung: `PASS` / `FAIL` / `TBD`.

| ID | Kriterium | FAIL-Bedingung |
|---|---|---|
| K1 | PCIe-2.1-x1-Endpoint | kein PCIe-EP / nur Gen3-x4-Host-Rolle / EP nicht realisierbar im Budget |
| K2 | 2× LMS7002M LVDS-Interface | zu wenig LVDS-fähige I/O oder Taktressourcen |
| K3 | DSP+BRAM für 4-Kanal-Channelization | DSP/BRAM unter dem dimensionierten Bedarf |
| K4 | Power im Handheld-Budget | Gesamtleistung über der Thermik-/Akku-Obergrenze (G10) |
| K5 | Verfügbarkeit/Lifecycle | NRND/EOL / keine reale Distributor-Verfügbarkeit |

> Solange eine K-Zelle `TBD` ist, gilt der Kandidat als **nicht qualifiziert** (kein PASS) — `score.py` wertet ihn als „unvollständig", nicht als Sieger.

## Stufe 2 — Gewichtete Achsen (S1–S8)

Jede Achse 0–5 nach Rubrik, dann × Gewicht. Achsen entsprechen den Soft-Anforderungen aus `REQUIREMENTS.md`.

### Rubrik (0–5, einheitlich)
| Punkte | Bedeutung |
|---|---|
| 5 | deutlich über Anforderung, mit Reserve + belegt |
| 4 | erfüllt komfortabel |
| 3 | erfüllt knapp / mit Auflagen |
| 2 | grenzwertig, Risiko |
| 1 | kaum, nur mit Workaround |
| 0 | nicht gegeben |
| `TBD` | Datenlage fehlt → zählt in `score.py` als „unvollständig" |

### Default-Gewichtung (⚠️ Owner-Entscheidungspunkt)

> Diese Gewichte drücken eine **Produkt-/Design-Haltung** aus, keine technische Naturkonstante. Sie sind bewusst überschreibbar. Der hier gesetzte Default priorisiert das, was ein **Open-Source-Funk-Handheld** braucht: freie/reproduzierbare Toolchain, kohärente SDR-Fähigkeit und ein reifes Ökosystem (geringes Bring-up-Risiko). Power/Thermik ist bereits als **Knockout (K4)** hart abgesichert und taucht deshalb im Score nur indirekt (S3) auf.

| Achse | Bedeutung | Gewicht | Begründung |
|---|---|---:|---|
| S4 | Toolchain-Offenheit | **18** | Open-Source-Gerät: freier/reproduzierbarer Build wiegt schwer (Hackbarkeit, keine Lizenz-Falle) |
| S2 | Kohärenz-Support (2× LMS7002M) | **15** | Kern-Alleinstellungsmerkmal des HyperRF (kohärentes 4RX/4TX) |
| S8 | Ökosystem / Referenzdesigns | **13** | LimeSDR-nahe Gateware + reife PCIe-EP-IP senken das Bring-up-Risiko am stärksten |
| S3 | Package / Thermik / HDI | **12** | muss auf 12-Layer-HDI + Wärmeableitung realisierbar sein |
| S5 | DSP-Headroom | **12** | Reserve für 5G/NTN/Radar-Vorverarbeitung (TARGET-Roadmap) |
| S1 | Timing / PLL-Ressourcen | **10** | Timestamping (10 MHz + PPS) wichtig, aber breit verfügbar |
| S6 | I/O-Headroom | **10** | Reserve für Filterbank/Converters/Clock — meist ausreichend |
| S7 | Kosten (EVT-/Kleinserie) | **10** | relevant fürs Vermarkten, aber nachrangig zur Fähigkeit in EVT |
| | **Summe** | **100** | |

**Alternative Haltungen (falls Owner anders gewichtet):**
- *„Rohleistung zuerst"* → S5 (DSP) + S6 (I/O) hoch, S4/S7 runter.
- *„Kostendisziplin fürs Vermarkten"* → S7 hoch, S5 runter.
- *„Maximal offen/hackbar"* → S4 dominant (z. B. 30), Rest verteilt.

Zum Ändern: die `weight`-Spalte in `CANDIDATE_MATRIX.csv` anpassen (Summe muss 100 bleiben — `score.py` prüft das).

## Endwert

```
score(Kandidat) = Σ_i ( rubrik_i × gewicht_i ) / 100        # 0..5-Skala
nur gültig, wenn alle K = PASS und keine S-Zelle TBD
```

`score.py` gibt bei jeder offenen Zelle **„INSUFFICIENT DATA — HOLD"** aus statt einer Zahl — das Gate bleibt bewusst zu, bis die Datenlage steht.
