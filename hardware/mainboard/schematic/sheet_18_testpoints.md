# Sheet 18 — Testpoints / Bring-up

Mess-, Bring-up- und Fertigungs-Testpunkte. Sammelt die in den anderen Sheets geforderten TPs. Ziel: **gestaffelter Power-Up-Bring-up** der 1–3 EVT-Einheiten ohne Löten.

## Power-Rails (Sheet 01/02)
`BAT_2S2P` · `VSYS` · `+5V_SYS` · `+3V3_SYS` · `+3V3_AON` · `HYPERRF_AUX_5V` · alle RK806S-Rails (nach Rail-Map, G02/G07).
> Reihenfolge-Prüfung: `+3V3_AON` zuerst (RP2350), dann System-Rails, dann Core.

## Reset/Sequencing
`RK_RESET_n` · `RP_RUN_n` · `PG_*` · `PWR_EN_*` · `MASKROM_n` · `RP_BOOTSEL`

## Kommunikation/Bring-up
`DBG_UART_TX/RX` (RK3576-Konsole) · `RP_UART/SPI/I2C` (Sheet 13) · `SENS_I2C` · `AUDIO_I2C` · `PD_I2C`

## Sicherheit
`RF_KILL` (muss in jedem Zustand messbar den TX-Pfad gaten) · PA-Enables (RF-Core).

## Hochgeschwindigkeit (Referenz/Coupons, nicht sondieren im Betrieb)
- Impedanz-**Coupons** (PCBWay-DFM, G06): SE 50 Ω, diff 90/100 Ω.
- PCIe/USB3: `PCIE_RST_n`, `REFCLK`, Link-LEDs (Sheet 12) — Zustands-TPs, keine SI-Sonde auf den Paaren.

## Fertigungstest (später, DVT)
- Testpad-Raster für ICT/Flying-Probe (Minewing/EVT-Build).
- Boundary-/Boot-Test-Hooks über UART/SWD.

## Kritische Design-Notizen
- **Gestaffelter Bring-up:** erst Power/Sequencing (TPs Rails+PG), dann RK3576-Konsole (UART), dann Display (G01), dann RF-Kette — jede Stufe an eigenen TPs verifizierbar.
- **RF-Kill zuerst prüfen:** vor jedem TX-Test `RF_KILL`-Wirksamkeit an den PA-Enables messen.
- TPs erreichbar bei (teil-)montiertem Gehäuse (Bauraum/Mechanik).

## ERC-Absicht
Testpunkte als 1-Pin-Netz-Taps ohne Doppeltreiber; nur Referenz auf bestehende Netze (keine neuen Netznamen).
