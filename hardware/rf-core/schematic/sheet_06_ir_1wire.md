# RF-Core Sheet 06 — IR / 1-Wire

Infrarot-TX/RX (D500/Q500) + geschützter 1-Wire/AUX-Anschluss. **TARGET** (optisches Fenster). IR ist optisch, nicht auf der HF-Frequenzachse — der TX unterliegt aber trotzdem dem Kill-/Aktions-Modell.

## Netze

| Netz | Funktion |
|---|---|
| `IR_TX` (via Treiber-Q500), `IR_RX` (Demodulator) | Infrarot Senden/Empfangen |
| `PA_EN_IR` (IR-TX-Freigabe) | über Gate (Sheet 01) — TX nur bei Freigabe |
| `OW_DATA`, `OW_PWR` | 1-Wire/AUX (geschützt: Serien-R, ESD, Strombegrenzung) |

## Kritische Design-Notizen
- **IR-TX-Treiber:** ausreichend Strom für Reichweite; IR-LED über Transistor, nicht direkt am GPIO.
- **IR-RX:** Demodulator (38 kHz o.ä.) + Umgebungslicht-Filter; optisches Fenster (Mechanik).
- **1-Wire/AUX schützen:** ESD/TVS, Serienwiderstand, Verpolungs-/Überspannungsschutz — externer Port.
- **AUX** kann Testklemme/externer Sensor sein — klare Strom-/Spannungsgrenzen.
- Testpunkte: `IR_TX`, `OW_DATA`.

## ERC-Absicht
IR-TX-Treiberpfad definiert; 1-Wire mit Schutz-Bauteilen; AUX-Grenzen dokumentiert.

## HOLD / TBD
- IR-LED/Empfänger-Wahl + optisches Fenster (Mechanik) 📄.
- AUX-Belegung/Grenzwerte final 📄.
