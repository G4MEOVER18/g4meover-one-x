# HyperRF FPGA-Auswahl — Gate G04

Entscheidungs-Gerüst für den **FPGA-MPN-Freeze** des HyperRF-Subsystems. Solange G04 offen ist, bleibt `hyperrf.fpga` in der Master-Spec **HOLD** — hier wird **kein** Bauteil geraten.

> **Roadmap-Vorgabe:** „Scored Candidate Matrix, **nicht aus altem Bild wählen**." Das EVT6-Referenzmaterial nennt Familien nur illustrativ; die Auswahl entsteht aus dieser Matrix, nicht aus einem alten Render.
>
> **Forbidden-Claim (Master-Spec):** *„Zynq UltraScale+ unless FPGA is explicitly frozen later."* Bis dieses Gate mit realen Werten geschlossen ist, darf **kein** konkreter MPN als gesetzt dargestellt werden.

## Warum ein FPGA überhaupt (FIXED aus Spec)

| Grund | Spec-Bezug |
|---|---|
| **PCIe-Endpoint** zum RK3576-Host | `hyperrf.fpga`, `hyperrf.host_limit` |
| **DSP / Channelization / Dezimation** | Host-Link ist nur **PCIe 2.1 x1** — die rohe 4-Kanal-RFIC-Bandbreite kann **nicht** kontinuierlich gestreamt werden; der FPGA muss vor dem Host dezimieren/kanalisieren | `hyperrf.host_limit` (FIXED) |
| **Digitale IQ-Anbindung** an 2× LMS7002M | `hyperrf.sdr` (2× LMS7002M, 4RX/4TX kohärent) |
| **Timestamping** | 10 MHz Referenz + GNSS-PPS + FPGA-Timestamping | `hyperrf.timing` |

## Ablauf (Gate-Prozess)

```
1. REQUIREMENTS.md   → Hard-/Soft-Anforderungen aus Master-Spec ableiten
2. Knockout-Filter   → Kandidaten, die eine Hard-Anforderung reißen, fallen raus (K1–K5)
3. CANDIDATE_MATRIX  → Datenblatt-/Verfügbarkeitswerte je Kandidat eintragen (TBD bis belegt)
4. score.py          → gewichtete Summe NUR über belegte Zellen; TBD ⇒ „INSUFFICIENT DATA — HOLD"
5. Freeze            → Gewinner + Begründung dokumentieren → hyperrf.fpga: HOLD → FIXED (G04 zu)
```

Ein Ergebnis entsteht **erst**, wenn reale Werte vorliegen (Vendor-Docs, Distributor-Verfügbarkeit, Power-Messung/Schätzung mit Quelle). Vorher meldet `score.py` bewusst „unzureichende Daten" statt einer Scheinzahl.

## Dateien

| Datei | Inhalt |
|---|---|
| `REQUIREMENTS.md` | abgeleitete Hard-/Soft-Anforderungen + Herkunft je Zeile |
| `SCORING_MODEL.md` | Knockout-Kriterien + 8 gewichtete Achsen + Rubrik + Default-Gewichtung (Owner-Entscheidung) |
| `CANDIDATE_MATRIX.csv` | Matrix-Skelett; herstellerspezifische Zellen = `TBD` |
| `score.py` | Auswertung der CSV (Knockout + gewichtete Summe, TBD-sicher) |

## Bezug zu Sicherheit

Der FPGA steuert HyperRF-TX-Pfade **nicht** am RF-Kill vorbei. Der hardware-erzwungene Kill (siehe RF-Core `sheet_01_supervisor_rfkill.md` + `firmware/rp2350/` `RF_KILL`) gilt subsystemübergreifend — auch für die HyperRF-PAs. Dieses Gate wählt Rechenleistung, nicht Sende-Autorität.
