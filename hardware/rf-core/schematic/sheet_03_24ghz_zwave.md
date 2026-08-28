# RF-Core Sheet 03 — 2,4 GHz (CC2652P7) + Z-Wave (EFR32ZG23)

Multiprotokoll-2,4-GHz (U502, CC2652P7 — Zigbee/Thread/BLE, **FIXED**) + Z-Wave/LR (U503, EFR32ZG23-Klasse, **TARGET**).

## Bauteile / Busse

| Ref | Bauteil | Host-Bus | Rolle |
|---|---|---|---|
| U502 | TI CC2652P7 (+PA) | UART/SPI | Zigbee/Thread/BLE, 2,4 GHz |
| U503 | SiLabs EFR32ZG23-Klasse | UART/SPI | Z-Wave / Z-Wave LR (Sub-GHz, regionale Freq.) |

## Netze

| Netz | Funktion |
|---|---|
| `CC2652_UART_*` / `CC2652_SPI_*`, `RESETn`, `BOOT` | Host-Anbindung + Programmierung |
| `ZWAVE_UART_*`, `ZWAVE_RESETn` | Z-Wave-Modul/IC |
| `PA_EN_CC2652`, `PA_EN_ZWAVE` | **über RF-Kill-Gate (Sheet 01)** |
| `ANT_2G4`, `ANT_ZWAVE` | Antennenpfade (getrennt: 2,4 GHz vs. Z-Wave-Sub-GHz) |

## Kritische Design-Notizen
- **CC2652P7** hat integrierten PA (+20 dBm) → RF-Matching/Harmonic-Filter nach TI-Referenz; **Kill** greift am PA-Enable.
- **Z-Wave** ist **regional frequenzgebunden** (EU 868,4 / US 908,4 …) → **exakte IC/Modul + Region-Freeze** (TARGET, G09) 📄. Getrennte Antenne von 2,4 GHz.
- **Koexistenz** 2,4 GHz mit Wi-Fi/BT (Mainboard) + BLE — Isolation/Platzierung.
- Programmier-/Debug-Zugang (cJTAG/SWD) für beide vorsehen.
- Testpunkte: Host-Busse, `PA_EN_*`.

## ERC-Absicht
Getrennte Host-Busse/CS; Reset/Boot als Signale; PA-Enables an Gate; zwei getrennte Antennenpfade.

## HOLD / TBD
- **Z-Wave** exaktes IC/Modul + Region 📄 (TARGET-Freeze, G09).
- 2,4-GHz-Matching/Filter-Werte (EVT).
