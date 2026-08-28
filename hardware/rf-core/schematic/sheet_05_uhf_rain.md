# RF-Core Sheet 05 — UHF RAIN RFID (E710)

UHF-RAIN-RFID-Reader (U506, Impinj E710-Klasse, 860–960 MHz, **TARGET**). Region-/PA-/Antennen-Pfad ist EU-kritisch.

## Bauteile / Netze

| Netz | Funktion |
|---|---|
| `E710_HOST_*` (SPI/parallel je Referenz) | Host-Anbindung |
| `E710_TX`, `E710_RX_I/Q` | Reader-TX + Empfang |
| `UHF_PA_EN` | **über RF-Kill-Gate (Sheet 01)** |
| `ANT_UHF` | UHF-Antennenpfad (SAW/PA/Matching) |

## Kritische Design-Notizen
- **Region:** EU 865–868 MHz vs. US 902–928 MHz → **SAW-Filter/PA/Antenne regionsspezifisch** validieren (BOM: „EU regional SAW/PA/antenna path validation") 📄, Freeze auf EVT (G09).
- **PA-Leistung** + Oberwellen/Spurious streng nach Regulierung; Kill greift am `UHF_PA_EN`.
- **Antenne:** UHF benötigt Fläche/Abstand — Antennen-Rail/Fenster (Mechanik).
- **Wärme:** Dauer-Reader-Betrieb → Verlustleistung in Thermik (G10).
- Testpunkte: `UHF_PA_EN`, Host-Bus.

## ERC-Absicht
Host-Bus konsistent; TX/RX-Pfade definiert; PA-Enable an Gate; Antennenpfad eindeutig.

## HOLD / TBD
- **Region-/SAW-/PA-Auswahl** (EU zuerst) 📄; exakte E710-Referenz/-Anbindung (TARGET, G09).
