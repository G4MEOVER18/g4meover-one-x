# Sheet 14 — Audio

Audio-Subsystem: Codec, Lautsprecher-Verstärker, MEMS-Mikrofon. Status: TARGET (Bauteil-Suffixe/Akustik nach Mechanik).

## Bauteile (aus BOM_EVT.csv)

| Ref | Bauteil | Rolle |
|---|---|---|
| U220 | Nuvoton NAU8822-Klasse | Audio-Codec (I²S + analog) |
| U221 | MAX98357A-Klasse | Klasse-D-Lautsprecher-Amp (I²S-Eingang) |
| MIC1 | Knowles/TDK PDM-MEMS | Mikrofon |
| SPK1 | 8 Ω Kompakt-Lautsprecher | Ausgabe |

## Netze

| Netz | Funktion | Status |
|---|---|---|
| `I2S_BCLK/LRCLK/SDOUT/SDIN` (SAI) | Audio-Bus RK3576↔Codec/Amp | TARGET |
| `AUDIO_I2C_*` | Codec-Konfiguration | TARGET |
| `PDM_CLK/DATA` | Mikrofon | TARGET |
| `SPK_P/N` | Lautsprecher-Ausgang (Amp) | TARGET |
| `HP_L/R`, `HP_DET` | Kopfhörer (falls Buchse) | TARGET |

## Kritische Design-Notizen
- **Amp-Speisung** aus `+5V_SYS`; Klasse-D-EMI (Ferrit/Filter am Ausgang, kurze Speaker-Leitungen).
- **MEMS-Port** akustisch an Gehäuse-Öffnung (Mechanik); von Lüftern/Haptik entkoppeln.
- **Masse-Führung:** Analog-Audio-Masse sauber, Trennung von digitalen/Power-Störern.
- **I²S-Master/Slave-Rolle** + Clocking festlegen (Codec vs. SoC) 📄.
- **Testpunkte:** `I2S_*`, `SPK_P/N` (→ Sheet 18).

## ERC-Absicht
I²S als Bus; Codec/Amp-Rails Power-Input; Speaker-Ausgang als differenzielles Netz; Config-I²C mit Pulls.

## HOLD / TBD
- Kopfhörerbuchse ja/nein (Bauraum) 📄.
- Exakte Codec-/Amp-/Mic-Suffixe + Lautsprecherlast (Akustikkammer) 📄.
