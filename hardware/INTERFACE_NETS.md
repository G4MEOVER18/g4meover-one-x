# ONE-X — Inter-Board-Netz-Dictionary (kanonisch)

**Single Source of Truth für die Board-zu-Board-Signalnamen.** Mainboard-Sheet 17 fordert „exakt gespiegelte Netznamen zum Ziel-Board" — dieses Dokument legt fest, wie diese Netze **kanonisch** heißen, damit beide Enden jedes Verbinders identisch benannt sind (Voraussetzung für saubere KiCad-ERC, Gate G07).

> Geprüft von `tools/schematic_netcheck.py`. Wer ein Sheet ändert, hält sich an diese Namen; der Checker meldet Abweichungen.

## Konnektoren

| Connector | A-Seite | B-Seite | Inhalt |
|---|---|---|---|
| `J_DSI` | Mainboard | Display-FPC / UI-Carrier | MIPI-DSI + Backlight + Touch |
| `J_UI` | Mainboard | UI-Carrier | Bedienung/Haptik/LED + DSI-Durchführung |
| `J_RFCORE` | Mainboard | RF-Core | Radio-Bus + RF-Kill + Antennen-Feeds |
| `J_M2` | Mainboard | M.2-Bridge → HyperRF | PCIe 2.1 ×1 + USB3 + Sideband + Power |
| `J_ANT` | Mainboard | Antenna-Rail | 4× SMA-Feeds |
| `J_BAT` | Mainboard | Akku-Pack | Batterie + NTC + Balancing |
| `J_PWR` | Mainboard | USB-C-Board | VBUS/CC/USB3/DP |

## Kanonische Netznamen

### PCIe 2.1 ×1 (`J_M2` — Mainboard ↔ M.2-Bridge ↔ HyperRF-FPGA)
| Kanonisch | Rolle |
|---|---|
| `PCIE_TX_P` / `PCIE_TX_N` | Host→EP (AC-gekoppelt) |
| `PCIE_RX_P` / `PCIE_RX_N` | EP→Host |
| `PCIE_REFCLK_P` / `PCIE_REFCLK_N` | 100 MHz Referenz |
| `PCIE_PERST_n` | PCIe-Reset (Host→EP) |
| `PCIE_CLKREQ_n` | Clock-Request |
| `PCIE_WAKE_n` | Wake (EP→Host) |

*Ersetzt:* `PETx0*`/`PERx0*`/`PE_REFCLK*`/`PERST` (alte, uneinheitliche Schreibweisen).

### USB3 über M.2 (`J_M2`)
| Kanonisch | Rolle |
|---|---|
| `USB3_M2_TX_P` / `USB3_M2_TX_N` | SuperSpeed TX |
| `USB3_M2_RX_P` / `USB3_M2_RX_N` | SuperSpeed RX |
| `USB2_M2_D_P` / `USB2_M2_D_N` | USB2-Fallback |

*Ersetzt:* `USB3_SSTX*`/`USB3_SSRX*`. Der `_M2_`-Zusatz grenzt gegen den USB-C-USB3 (`J_PWR`) ab.

### MIPI-DSI (`J_DSI` / `J_UI`)
| Kanonisch | Rolle |
|---|---|
| `DSI0_CLK_P` / `DSI0_CLK_N` | DSI-Takt |
| `DSI0_D0_P` / `DSI0_D0_N` | Datenlane 0 |
| `DSI0_D1_P` / `DSI0_D1_N` | Datenlane 1 |
| `DSI0_D2_P` / `DSI0_D2_N` | Datenlane 2 |
| `DSI0_D3_P` / `DSI0_D3_N` | Datenlane 3 |
| `LCD_RST_n`, `BL_EN`, `BL_PWM`, `VLCD_3V3` | Reset / Backlight / Panel-Rail |
| `TP_SCL`, `TP_SDA`, `TP_INT`, `TP_RST`, `VDD_TP_3V3` | kap. Touch |

> **Warum einzeln statt „`DSI0_D0..D3_P/N`" (2026-09-08):** Die Kurzschreibweise
> ist für Menschen lesbar, für ein Werkzeug aber unvollständig — `D1`, `D2` und
> sämtliche `_N`-Varianten kamen darin nie wörtlich vor und galten deshalb als
> unbekannt. Eine Single Source of Truth muss vollständig sein, nicht abgekürzt.

*Ersetzt:* `DSI_*` (ohne `0`).

### RF-Core-Bus (`J_RFCORE` — Mainboard ↔ RF-Core)
| Kanonisch | Rolle |
|---|---|
| `RFC_SPI_*` (SCK/MOSI/MISO/CSn…) | SPI zu den Radios |
| `RFC_UART_*` (TX/RX) | UART zu den Radios |
| `RFC_I2C_*` (SCL/SDA) | I²C (NFC/…) |
| `RFC_IRQ_*` | Interrupts der Radios |
| `RF_KILL` | HW-Master-Kill (aktiv = TX aus) |
| `RF_KILL_SW_n` | optionaler physischer Notfall-Kill |
| `TX_GATE_OK` | Status: TX physisch freigegeben (→ RP2350/LED) |

Die RF-Core-internen PA-Enables (`PA_EN_<radio>`) bleiben **board-lokal** (queren `J_RFCORE` nicht).

### Antennen-Feeds (`J_ANT` — Mainboard ↔ Antenna-Rail)
Über den Verbinder queren die 4 kanonischen Feeds `ANT_1`…`ANT_4` (50 Ω). Welcher Radio-Feed auf welchem SMA landet, ist **TBD 📄** (→ G09) — hier als Zuordnungs-Tabelle geführt, damit die Namen trotzdem eindeutig brücken:

| SMA / kanonisch | vorgesehener Quell-Feed (Design-Platzhalter, TBD) | Quell-Board |
|---|---|---|
| `ANT_1` | Sub-GHz (`ANT_SUBGHZ`, CC1101/SX1262) | RF-Core |
| `ANT_2` | 2,4 GHz (`ANT_2G4`, CC2652P7) | RF-Core |
| `ANT_3` | HyperRF-SDR-Feed (`LMSx_ANT_*`) | HyperRF |
| `ANT_4` | UHF-RAIN (`ANT_UHF`) / Ersatz | RF-Core |

> Die Quell-Feed-Netze (`ANT_SUBGHZ` etc.) sind **board-lokal**; am `J_ANT`-Übergang heißen sie kanonisch `ANT_1..4`. Die endgültige Zuordnung wird mit dem Antennenkonzept eingefroren (G09).

### Power / Sonstiges (board-übergreifend)
| Kanonisch | Rolle |
|---|---|
| `HYPERRF_AUX_5V` | HyperRF-Einspeisung bis 5 A (`J_M2`) |
| `+3V3_SYS` | System-Logik-Rail (`J_M2`, `J_UI`, `J_RFCORE`) — speist Logik, Radios, M.2 |
| `BAT_2S2P` | Akku (`J_BAT`, G11) |
| `GND` / `AGND` | Masse / Analog-Masse |

> **Namens-Präzisierung (2026-09-08):** Die M.2-Bridge führte diese Rail als „`+3V3`", der [Power-Tree](mainboard/schematic/sheet_01_power_tree.md) als `+3V3_SYS`. Es ist **dieselbe** Rail; kanonisch ist `+3V3_SYS`. Zwei Namen für eine Rail fallen erst beim Zusammenführen der Boards auf — dann aber teuer.

## Board-lokal (queren KEINE Board-Grenze — nicht im Mirror-Check)
`PA_EN_*`, `HRF_*`, `LMSx_LML_*`, `HB_*`, `RADAR_*`, `UWB_*`, `KEY_*`, `RING_*`, `HAPTIC_*`, `LED_*`, `PMIC_*` — bleiben auf ihrem Board.
