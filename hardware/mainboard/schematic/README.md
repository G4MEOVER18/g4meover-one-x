# ONE-X Mainboard — Schaltplan (Phase 5 → Gate G07)

Produktions-Schaltplan des Mainboards (210 × 92 mm, 12-Layer-HDI) als **reviewbare Design-Spezifikation**, Sheet für Sheet. Ziel: ERC-cleaner Schaltplan (**Gate G07**) als Basis für KiCad-Zeichnung + Minewing-Design-Review.

> **Methodik (warum Design-Spec statt sofort KiCad):** Jedes Sheet wird zuerst als präzise Spezifikation (Bauteile, Netze, Rails, kritische Notizen, ERC-Absicht) festgelegt — überprüfbar, diff-bar, ohne CAD-Tool. Der KiCad-Schaltplan wird daraus deterministisch gezeichnet. So bleibt die Single-Source-of-Truth-Disziplin erhalten und HOLD-Themen bleiben sichtbar, statt in einer Binärdatei zu verschwinden.

## Sheet-Index (18 Sheets)

| # | Sheet | Kern | Abh. Gate | Status |
|---|---|---|---|---|
| 01 | Power-Tree / Entry | USB-C-PD-Eingang, VSYS, Rails-Übersicht | — | 🟡 Entwurf |
| 02 | RK806S PMIC | RK3576-Rail-Map, Sequencing | G07 (Rail-Map HOLD) | 🟡 Entwurf |
| 03 | RK3576 Core | SoC, Entkopplung, Straps, Clocks | — | 🟡 Entwurf |
| 04 | LPDDR5 | 16 GB, Topologie | **G02 (HOLD)** | ⛔ blockiert |
| 05 | UFS | 256 GB, M-PHY | **G03 (HOLD)** | ⛔ blockiert |
| 06 | Recovery/Boot | 32 MB SPI-NOR, BootSel | — | ⬜ |
| 07 | USB-C PD/USB3/DP | TPS25751A, Mux | — | ⬜ |
| 08 | USB-Host | USB-A, Hub | — | ⬜ |
| 09 | HDMI/DP-Out | Display-Out | — | ⬜ |
| 10 | Ethernet ×2 | 2× RTL8211F, RGMII, Magnetics | — | ⬜ |
| 11 | Wi-Fi 6E/BT | MT7921-Klasse, Antenne | — | ⬜ |
| 12 | M.2 / HyperRF-Link | PCIe 2.1 ×1 + USB3 | — | ⬜ |
| 13 | RP2350-Link | SPI/I²C/UART zum System-Manager | — | ⬜ |
| 14 | Audio | Codec, Amp, Mic | — | ⬜ |
| 15 | Sensoren | IMU/Mag/Baro/Temp/ALS (I²C) | — | ⬜ |
| 16 | Debug/Recovery | JTAG/SWD, UART-Konsole, Testmodi | — | ⬜ |
| 17 | Connectors | FPC/Board-to-Board, Power | — | ⬜ |
| 18 | Testpoints | Bring-up-/Mess-Punkte, Coupons | — | ⬜ |

Legende: 🟡 Entwurf · ⬜ offen · ⛔ blockiert (HOLD, nicht routen/finalisieren bis Gate schließt).

> **Sheets 04 (LPDDR5) und 05 (UFS) werden bewusst nicht finalisiert**, bis G02/G03 mit Herstellerdaten geschlossen sind (siehe [`../../../manufacturing/`](../../../manufacturing/)). Bis dahin nur Platzhalter-Sheets mit Anforderungen.

## Netz-Namenskonvention

- **Power-Rails (GROSS):** aus [`../../../spec/POWER_TREE.csv`](../../../spec/POWER_TREE.csv) —
  `VBUS_C`, `VSYS`, `+5V_SYS`, `+3V3_SYS`, `+3V3_AON`, `BAT_2S2P`, plus RK806S-Rails (`VDD_*`, HOLD-Rail-Map).
- **Differentielle Paare:** Suffix `_P`/`_N` (z.B. `PCIE_TX_P/N`, `USB3_RX_P/N`, `DSI_D0_P/N`, `RGMII0_TXD…`).
- **Busse:** `I2C<n>_SCL/SDA`, `SPI<n>_{SCK,MOSI,MISO,CSn}`, `UART<n>_{TX,RX}`.
- **Steuer-/Kill:** `RF_KILL` (HW-erzwungen), `PWR_EN_*`, `PG_*` (Power-Good), `RESET_*n`.
- **Masse:** `GND` (digital/analog Split nur wo begründet, dann `AGND`/`RGND` mit definiertem Stitch).

## Impedanz-/SI-Ziele (Referenz für G08-Layout)

| Netzklasse | Ziel |
|---|---|
| Single-Ended allgemein | 50 Ω |
| USB2 / GbE-Paare | 90 Ω diff |
| PCIe 2.1 / USB3 / MIPI-DSI | 100 Ω diff |
| LPDDR5 | nach bestätigter Topologie (G02) |

## ERC-Absicht (G07)
Jedes Sheet definiert Pin-Typen/Power-Flags so, dass ERC ohne Warnungen durchläuft (Power-In/Out, No-Connect explizit, Bus-Aliase konsistent). Sheets werden erst als „ERC-ready" markiert, wenn ihre Netze vollständig und widerspruchsfrei sind.

## Bezug
Alle Bauteile/Referenzen: [`../../../manufacturing/BOM_EVT.csv`](../../../manufacturing/BOM_EVT.csv) + [`../../../spec/`](../../../spec/) (INTERFACE_MATRIX, POWER_TREE). Nichts hier darf der Master-Spec widersprechen.
