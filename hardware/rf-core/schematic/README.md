# ONE-X RF-Core — Schaltplan (Low-Power-Funk)

RF-Core-Board (92 × 66 mm) mit den Low-Power-Radios + dem **hardware-erzwungenen RF-Kill**. Gleiche Design-Spec-Methodik wie das [Mainboard](../../mainboard/schematic/README.md): reviewbare Sheets, HOLD sichtbar, ERC-Absicht.

> **Sicherheits-Grundsatz zuerst:** Sheet 01 (Supervisor/RF-Kill) hat Priorität. Der Kill gatet **alle** PA-/TX-Enables physisch (softwareunabhängig), Default nach Reset = **aktiv**. Bezug: [`../../../firmware/rp2350/`](../../../firmware/rp2350/) (`RF_KILL`).

## Sheet-Index

| # | Sheet | Kern | Status (BOM) |
|---|---|---|---|
| 01 | Supervisor / RF-Kill | HW-Gate über alle TX/PA-Enables, Default-aktiv | FIXED |
| 02 | Sub-GHz | CC1101 (U500) + SX1262 (U501), regionale Matching-Werte | FIXED (Matching EVT) |
| 03 | 2,4 GHz + Z-Wave | CC2652P7 (U502) Zigbee/Thread/BLE + EFR32ZG23 (U503) Z-Wave/LR | FIXED / TARGET |
| 04 | NFC + LF-RFID | PN7160 (U504) 13,56 MHz + 125 kHz LF-AFE (U505) | FIXED / TARGET |
| 05 | UHF RAIN | Impinj E710 (U506) 860–960 MHz, EU-Region SAW/PA | TARGET |
| 06 | IR / 1-Wire | IR-TX/RX (D500/Q500) + geschütztes 1-Wire/AUX | TARGET |
| 07 | Power / Host-Link / Antennen | Rails, SPI/UART zum Mainboard, Antennen-Feeds, Testpoints | — |

## Host-Anbindung
Über Connector `J_RFCORE` (Mainboard Sheet 17): `SPI`/`UART` zu den Radios, `RF_KILL`, Antennen-Feeds, Power. Steuer-SW läuft als Linux-High-Level-RF auf dem RK3576.

## Netz-Konventionen
Wie Mainboard. Zusätzlich: `<RADIO>_TXEN`/`<RADIO>_RXEN`/`<RADIO>_CE`, `PA_EN_*` — **alle** über den RF-Kill-Gate (Sheet 01). Antennen-Feeds `ANT_<band>`.

## Statusdisziplin
Kern-Radios (CC1101/SX1262/CC2652P7/PN7160) FIXED; Z-Wave/LF-AFE/UHF/IR TARGET (Suffix/Matching-Freeze auf EVT, Gate G09). Regionale RF-Matching-Werte werden **auf realer Hardware** getunt (G09) — nie nur aus Simulation.
