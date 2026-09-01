# KiCad-Bauplan — mainboard

> **Generiert** von `tools/gen_kicad_project.py` aus den Design-Spec-Sheets.
> Deterministisch (uuid5). Manifest: `hierarchy.json`. Diese Datei ist der
> menschliche Bau-Leitfaden für die KiCad-Zeichnung (Symbole/Wiring = KiCad-Schritt).

## Hierarchie
- Root-Sheet `mainboard.kicad_sch` instanziiert **18** Sub-Sheets.
- Root-UUID (fix): `674468c4-de73-5c94-b1cc-3b16121ca2e4`

## Sub-Sheets (Reihenfolge + Global-Labels)

| # | Sheet-Datei (KiCad) | Titel | Inter-Board-Labels | Status |
|---|---|---|---|---|
| 01 | `sheet_01_power_tree.kicad_sch` | Sheet 01 — Power-Tree / Entry | `BAT_2S2P`, `HYPERRF_AUX_5V`, `RF_KILL` | zeichnen |
| 02 | `sheet_02_rk806s_pmic.kicad_sch` | Sheet 02 — RK806S PMIC | — | zeichnen |
| 03 | `sheet_03_rk3576_core.kicad_sch` | Sheet 03 — RK3576 Core | `DSI0_CLK_P`, `DSI0_D0..3_P` | zeichnen |
| 04 | `sheet_04_lpddr5.kicad_sch` | Sheet 04 — LPDDR5 ⛔ BLOCKIERT (Gate G02) | — | ⛔ HOLD-Stub |
| 05 | `sheet_05_ufs.kicad_sch` | Sheet 05 — UFS ⛔ BLOCKIERT (Gate G03) | — | ⛔ HOLD-Stub |
| 06 | `sheet_06_recovery_boot.kicad_sch` | Sheet 06 — Recovery / Boot (SPI-NOR) | — | zeichnen |
| 07 | `sheet_07_usbc_pd.kicad_sch` | Sheet 07 — USB-C (PD / USB3 / DP-Alt) | — | zeichnen |
| 08 | `sheet_08_usb_host.kicad_sch` | Sheet 08 — USB-Host (USB-A) | — | zeichnen |
| 09 | `sheet_09_hdmi_dp_out.kicad_sch` | Sheet 09 — HDMI / DP-Out | — | zeichnen |
| 10 | `sheet_10_ethernet.kicad_sch` | Sheet 10 — Ethernet ×2 | — | zeichnen |
| 11 | `sheet_11_wifi_bt.kicad_sch` | Sheet 11 — Wi-Fi 6E / Bluetooth | — | zeichnen |
| 12 | `sheet_12_m2_hyperrf_link.kicad_sch` | Sheet 12 — M.2 / HyperRF-Link | `HYPERRF_AUX_5V`, `PCIE_CLKREQ_n`, `PCIE_PERST_n`, `PCIE_REFCLK`, `PCIE_REFCLK_P`, `PCIE_RX_P`, `PCIE_TX_P`, `PCIE_WAKE_n`, `USB2_M2_D_P`, `USB3_M2_RX_P`, `USB3_M2_TX_P` | zeichnen |
| 13 | `sheet_13_rp2350_link.kicad_sch` | Sheet 13 — RP2350-Link (System-Manager-Anbindung) | `RF_KILL` | zeichnen |
| 14 | `sheet_14_audio.kicad_sch` | Sheet 14 — Audio | — | zeichnen |
| 15 | `sheet_15_sensors.kicad_sch` | Sheet 15 — Sensoren | — | zeichnen |
| 16 | `sheet_16_debug_recovery.kicad_sch` | Sheet 16 — Debug / Recovery | — | zeichnen |
| 17 | `sheet_17_connectors.kicad_sch` | Sheet 17 — Connectors (Inter-Board) | `ANT_1`, `ANT_2`, `ANT_3`, `ANT_4`, `BAT_2S2P`, `BL_EN`, `BL_PWM`, `DSI0_CLK_P`, `DSI0_D0..D3_P`, `HYPERRF_AUX_5V`, `LCD_RST_n`, `RFC_I2C`, `RFC_IRQ`, `RFC_SPI`, `RFC_UART`, `RF_KILL`, `RF_KILL_SW_n`, `TP_INT`, `TP_RST`, `TP_SCL`, `TP_SDA`, `TX_GATE_OK` | zeichnen |
| 18 | `sheet_18_testpoints.kicad_sch` | Sheet 18 — Testpoints / Bring-up | `BAT_2S2P`, `HYPERRF_AUX_5V`, `RF_KILL` | zeichnen |

## Regeln
- **Inter-Board-Labels** = Global-Labels mit exakt dem kanonischen Namen aus
  [`../../INTERFACE_NETS.md`](../../INTERFACE_NETS.md) (von `schematic_netcheck.py` geprüft).
- **HOLD-Stub-Sheets** bleiben leer bis zum jeweiligen Gate (kein geratenes Bauteil/Pinout).
- **Symbole/Pinouts** kommen aus Vendor-Symbol-Libs im KiCad-Schritt — hier nicht geraten.
- Alle sheet-lokalen Netze siehe `hierarchy.json` → `sheets[].nets`.
