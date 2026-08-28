# RF-Core Sheet 04 — NFC/HF (PN7160) + 125 kHz LF-RFID

NFC/HF-Frontend (U504, NXP PN7160, 13,56 MHz, **FIXED**) + 125-kHz-LF-RFID-AFE (U505, **TARGET**).

## Bauteile

| Ref | Bauteil | Bus | Rolle |
|---|---|---|---|
| U504 | NXP PN7160 | I²C + IRQ | NFC/HF Reader/Card/P2P, 13,56 MHz |
| U505 | LF-RFID-AFE | SPI/analog | 125 kHz Read (+ opt. Emulation) |

## Netze

| Netz | Funktion |
|---|---|
| `NFC_I2C_*`, `NFC_IRQ`, `NFC_VEN` | PN7160-Host |
| `NFC_TX1/TX2`, `NFC_RX` | HF-Antennen-Treiber/Empfang (13,56 MHz) |
| `LF_COIL_P/N`, `LF_DATA`, `LF_CLK` | 125-kHz-Spule + AFE |
| `PA_EN_NFC` (Feld), `PA_EN_LF` (Feld) | **über RF-Kill-Gate (Sheet 01)** |

## Kritische Design-Notizen
- **NFC-Antenne** = abgestimmter 13,56-MHz-Kreis; **Matching im Gehäuse** (Metall-/Akku-Nähe verstimmt) → Tuning in finaler Mechanik (G09) 📄.
- **LF-Spule** (125 kHz): Induktivität/Q, Leseabstand; Platzierung fern von Störern.
- **Feld = TX:** NFC-/LF-Feldaktivierung zählt als Sendefunktion → über RF-Kill/Regulierungsprofil gaten.
- EMV: 13,56-MHz-Oberwellen filtern.
- Testpunkte: `NFC_I2C`, `LF_DATA`.

## ERC-Absicht
NFC-I²C mit Pulls; Antennentreiber-Netze definiert; LF-Spule als differenzielles Netz; Feld-Enables an Gate.

## HOLD / TBD
- NFC-Antennen-Matching (Gehäuse) 📄; exakte LF-AFE-MPN + Spule (TARGET, G09).
