# Sheet 03 — RK3576 Core

Der Applikations-SoC (U100, Rockchip RK3576) mit Versorgung, Entkopplung, Takt, Reset, Boot-Straps und Debug. **FIXED** ist der SoC; die **exakte Ball-/Pin-Zuordnung ist aus dem RK3576-Datenblatt zu setzen** (BOM: „production reference package still required") — hier als `TBD 📄` markiert, nicht geraten.

## Versorgungsdomänen (vom RK806S, Sheet 02)

| Domäne (Beispielname) | Zweck | Quelle | Status |
|---|---|---|---|
| `VDD_CPU_B` | A72-Cluster (big) | RK806S Buck | HOLD (Rail-Map) 📄 |
| `VDD_CPU_L` | A53-Cluster (little) | RK806S Buck | HOLD 📄 |
| `VDD_GPU` | GPU | RK806S Buck | HOLD 📄 |
| `VDD_NPU` | NPU | RK806S Buck | HOLD 📄 |
| `VDD_LOGIC` | Logic/Core | RK806S Buck | HOLD 📄 |
| `VDD_DDR` | LPDDR5-PHY | RK806S Buck | HOLD 📄 (→ Sheet 04, G02) |
| `VCC_1V8` / `VCC_3V3` | I/O-Bänke | RK806S LDO/Buck | HOLD 📄 |
| `VCCIO_*` | pro I/O-Bank | RK806S | HOLD 📄 |

> Genaue Rail-Namen, Spannungen und **Sequenz** folgen der RK3576-Referenz (Sheet 02). Bis dahin HOLD.

## Takt & Reset

| Netz | Funktion | Bauteil | Status |
|---|---|---|---|
| `XIN_24M` / `XOUT_24M` | Haupt-Oszillator 24 MHz | Quarz + 2× Load-Cap | TARGET (Wert 📄) |
| `RTC_32K_IN/OUT` | RTC 32,768 kHz | Quarz | TARGET |
| `NPOR` / `RESET_n` | Power-On-Reset | von PMIC `PG`/Reset (Sheet 02) | FIXED-Absicht |
| `PMIC_INT`, `PMIC_SLEEP` | PMIC-Kommunikation | zu RK806S | HOLD 📄 |

## Boot-Straps

- Boot-Quellen-Auswahl (UFS/eMMC/SD/SPI-NOR) über Strap-Pins — **Werte aus RK3576-TRM** 📄.
- **Recovery/Maskrom** erreichbar halten (→ Sheet 06 SPI-NOR, Sheet 16 Debug).
- Straps mit definierten Pull-Up/Down; Testpunkte vorsehen (Sheet 18).

## Interface-Fan-out (Verweise auf andere Sheets)

| Schnittstelle | Ziel-Sheet | Bus | Status (Interface-Matrix) |
|---|---|---|---|
| MIPI-DSI 4-lane | (UI-Carrier) | `DSI_D0..3_P/N`, `DSI_CLK_P/N` | FIXED |
| LPDDR5 | Sheet 04 | dual-channel | **HOLD (G02)** |
| UFS | Sheet 05 | M-PHY | **HOLD (G03)** |
| PCIe 2.1 ×1 | Sheet 12 | `PCIE_*_P/N` | FIXED |
| USB3 (M.2/5G) | Sheet 12 | `USB3_*_P/N` | FIXED |
| USB-C (USB3+DP-Alt) | Sheet 07 | — | FIXED |
| RGMII0/1 | Sheet 10 | `RGMII*` | FIXED |
| SDIO (Wi-Fi) | Sheet 11 | `SDIO_*` | FIXED |
| Control SPI/I²C/UART | Sheet 13 | zu RP2350 | FIXED |
| Audio SAI/I²S | Sheet 14 | `I2S_*` | TARGET |
| Sensor-I²C | Sheet 15 | `I2C<n>` | TARGET |
| JTAG/SWD, UART-Konsole | Sheet 16 | — | — |

## Kritische Design-Notizen
- **Entkopplung:** pro Power-Ball nach Rockchip-Referenz (Bulk + HF-Kondensatoren nah am Ball); genaue Stückzahl/Werte 📄. Für BGA-Escape HDI nötig (Gate G06).
- **VDD_DDR** eng mit LPDDR5-Topologie gekoppelt → **nicht finalisieren bis G02**.
- **Power-Sequencing** strikt nach RK806S-Referenz (Sheet 02); `RESET_n` erst nach allen `PG`.
- **EMI:** 24-MHz-Oszillator + Hochgeschwindigkeitsleitungen von RF-Fenstern/Antennen entkoppeln (Layout G08).
- **Recovery-Fähigkeit:** Maskrom-Boot immer erreichbar (Anti-Brick), Testpunkte an Straps/UART.

## ERC-Absicht
Alle Power-Domänen als Power-Input; keine unversorgte Domäne. Straps mit explizitem Pull + No-Connect wo unbenutzt. Bus-Aliase konsistent zu Ziel-Sheets.

## HOLD / TBD (nicht raten)
- Exakte **Ball-Map** + Power-Ball-Gruppen (RK3576-Datenblatt/Referenz-Package). 📄
- **Rail-Map + Sequenz** (Sheet 02, RK3576-Referenz). 📄
- Quarz-Lastkapazitäten, Strap-Pull-Werte. 📄
