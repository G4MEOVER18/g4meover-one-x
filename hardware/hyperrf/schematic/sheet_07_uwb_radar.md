# HyperRF Sheet 07 — UWB / 60-GHz-Radar

Zwei Spezial-RF-Funktionen: **UWB** (Qorvo DW3000-Serie, Suffix **HOLD → G05**) und eine **60-GHz-Radar-Kachel** (TI IWRL6432W-Klasse, TARGET) mit **eigenem RF-Fenster**.

## UWB (DW3000-Serie — Suffix HOLD)

| Netz | Rolle | Status |
|---|---|---|
| `UWB_SPI_*` | Konfig/Daten | HOLD |
| `UWB_IRQ` / `UWB_RST_n` | Interrupt / Reset | HOLD |
| `UWB_ANT` | UWB-Antenne | HOLD |

> **`hyperrf.uwb` = HOLD:** DW3000-**Suffix nicht eingefroren** (→ G05). Forbidden-Claim: **kein** „UWB SR150", solange Design nicht geändert/verifiziert. Bus-Struktur design-bar, exaktes Bauteil + Antenne bleiben HOLD.

## 60-GHz-Radar-Kachel (IWRL6432W-Klasse, TARGET)

| Netz | Rolle | Status |
|---|---|---|
| `RADAR_HOST_*` | Host-Interface (SPI/…); Daten zum FPGA/Host | TARGET |
| `RADAR_ANT_*` | integrierte 57–64-GHz-Antennen (on-package/on-tile) | TARGET |
| `RADAR_EN` | Enable | TARGET |

- **Separates RF-Fenster / eigene Kachel** (Spec `hyperrf.radar` „separate RF window/tile"; Thermik-Constraint „RF windows kept metal-free").
- **Kein allgemeiner 60-GHz-SDR** — das ist eine **Radar**-Funktion mit festem IC, kein Wideband-SDR (`hyperrf.not_claimed`, FIXED). Wichtiger Review-Guard.

## Kritische Design-Notizen
- **60 GHz extrem verlust-/toleranzempfindlich:** Antennen-/Substrat-/Fenster-Design kritisch → HDI + metallfreies Fenster; Detailkonzept TBD 📄 (Mechanik-Abstimmung).
- **Isolation** UWB ↔ Radar ↔ SDR-Kette.
- **UWB-Suffix (G05)** bestimmt Pinout/Antenne → erst danach Bauteil setzen.

## ERC-Absicht
UWB-/Radar-Busse eindeutig; Antennenpfade als kontrollierte RF-Netze; Enables sauber; UWB-Bauteil als Platzhalter-Footprint bis G05.

## HOLD / TBD
**UWB-DW3000-Suffix HOLD → G05** · Radar-Kachel-Antennen-/Fenster-Konzept 📄 · Isolationskonzept 📄 · Radar-MPN (TARGET-Freeze EVT).
