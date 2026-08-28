# Sheet 13 — RP2350-Link (System-Manager-Anbindung)

Verbindung RK3576 ↔ **RP2350B** (U200, Always-On-System-Manager). Elektrische Basis für das [ONE-X-Link-Protokoll](../../../firmware/rp2350/PROTOCOL.md). Alle drei Busse sind **FIXED** (Interface-Matrix: Control SPI/I²C/UART).

## Busse

| Bus | Netze | Richtung | Rolle | Status |
|---|---|---|---|---|
| Control SPI | `RP_SPI_SCK/MOSI/MISO/CSn` | RK3576 (Master) ↔ RP2350 | Kommandos/Status, opt. low-BW-Grafik | FIXED |
| Control I²C | `RP_I2C_SCL/SDA` | RK3576 ↔ RP2350 | Power/Status/Buttons/Sensoren | FIXED |
| Control UART | `RP_UART_TX/RX` | RK3576 ↔ RP2350 | Debug/Recovery/Steuerung | FIXED |
| Wake/IRQ | `RP_IRQ_n` (RP2350→RK3576), `TOUCH_WAKE` | — | Wecken, Touch-Wake-IRQ | FIXED |

> Der **primäre Link** trägt das ONE-X-Link-Framing (SOF `0xA5 0x5A`, VER/TYPE/SEQ/LEN/CRC-16) — Transport UART primär oder SPI (PROTOCOL.md §1). Bus-Auswahl wird hier elektrisch für **beide** vorgesehen; die Firmware wählt den aktiven.

## Versorgung / Always-On

- RP2350B + 16 MB QSPI (U201) laufen an **`+3V3_AON`** (Sheet 01) — **unabhängig** von VSYS/RK806S. Der Manager bleibt an, wenn Linux/PMIC aus ist.
- Eigener Reset/BootSel (→ Sheet 16 Debug/Recovery): `RP_RUN_n`, `RP_BOOTSEL`.

## Sicherheits-/Steuersignale (RP2350-seitig, Detail auf RF-Core/Sheet 01)

| Netz | Rolle |
|---|---|
| `RF_KILL` | HW-erzwungener TX-Disable-Pfad (Manager = Autorität; Default nach Reset = aktiv) |
| `PWR_BTN_n` | Power-Taste → RP2350 (Zustandsmaschine OFF/BOOT/RUN…) |
| `SYS_PWR_EN` | RP2350 gibt System-Rails frei (Sheet 01/02) |
| `FAN_PWM/TACH` | Lüftersteuerung (dual blowers) |
| `HAPTIC_*`, `SOFTKEY_*`, `TOUCHRING_*` | UI-Peripherie (physisch auf UI-Carrier, hier nur Link) |

## Level-/Signal-Integrität
- Beide MCUs auf 3,3-V-I/O → i.d.R. kein Level-Shift nötig; **verifizieren** gegen RK3576-Bank-IO-Spannung 📄.
- I²C mit definierten Pull-Ups (Wert nach Buslast) an `+3V3_AON`.
- SPI-Leitungslänge/Terminierung für die vorgesehene Taktrate im Layout prüfen (G08).

## Kritische Design-Notizen
- **Domänen-Kreuzung AON↔SYS:** Signale zwischen `+3V3_AON`-RP2350 und ggf. abgeschaltetem RK3576 dürfen keinen Backfeed erzeugen (Serienwiderstände/definierte Pegel bei RK3576-Off).
- **Recovery-Pfad wahren:** RP2350 kann RK3576-Recovery anstoßen (`CMD_RECOVERY`) — Reset-/BootSel-Verdrahtung dazu vorsehen.
- **Testpunkte** an SPI/I²C/UART + `RF_KILL` (→ Sheet 18).

## ERC-Absicht
Drei Busse als reguläre Signale mit konsistenten Netznamen zu beiden ICs; Pull-Ups deklariert; `+3V3_AON` als Power-Input an RP2350/QSPI. Wake-/Kill-Netze eindeutig (ein Treiber).

## HOLD / TBD
- RK3576-Bank-IO-Spannung der Control-Pins (Level-Shift ja/nein) 📄.
- Aktiver primärer Transport (UART vs. SPI) — Firmware-seitig konfigurierbar, elektrisch beide vorgesehen.
