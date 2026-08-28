# RF-Core Sheet 02 — Sub-GHz (CC1101 + SX1262)

Zwei Sub-GHz-Radios: CC1101 (U500, Protokoll/Raw) + SX1262 (U501, LoRa/FSK). **FIXED**; regionale Matching-Werte werden auf EVT getunt (G09).

## Bauteile / Busse

| Ref | Bauteil | Host-Bus | Rolle |
|---|---|---|---|
| U500 | TI CC1101 | SPI + GDO-IRQs | Sub-GHz Protokoll/Raw |
| U501 | Semtech SX1262 | SPI + DIO/BUSY | LoRa/FSK Sub-GHz |

## Netze

| Netz | Funktion |
|---|---|
| `RFC_SPI_SCK/MOSI/MISO`, `CC1101_CSn`, `SX1262_CSn` | gemeinsamer SPI, getrennte CS |
| `CC1101_GDO0/2`, `SX1262_DIO1/BUSY`, `SX1262_RESET` | IRQ/Status/Reset |
| `PA_EN_CC1101`, `PA_EN_SX1262` | **über RF-Kill-Gate (Sheet 01)** |
| `ANT_SUBGHZ` | Antennenpfad (ggf. Switch gemeinsam) |

## Kritische Design-Notizen
- **Matching/Balun** je Region (EU 868 / US 915 …) — Werte-Platzhalter, Freeze auf EVT (G09) 📄.
- **TX/RX-Switch** falls gemeinsame Antenne; SX1262-PA-Pfad (High-Power-Option) beachten.
- **Entkopplung/Xtal** nach Datenblatt-Referenz; TCXO für SX1262 falls LoRa-Genauigkeit nötig 📄.
- **Kill:** beide PA/TX-Enables ausschließlich über Sheet 01.
- Testpunkte: `RFC_SPI_*`, `PA_EN_*` (Sheet 07).

## ERC-Absicht
Gemeinsamer SPI mit getrennten CS; IRQ/BUSY als Signale; PA-Enables an Gate-Netze; Antennenpfad definiert.

## HOLD / TBD
- Regionale Matching-/Balun-Werte, TCXO ja/nein 📄 (EVT, G09).
