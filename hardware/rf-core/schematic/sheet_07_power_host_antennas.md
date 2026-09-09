# RF-Core Sheet 07 — Power / Host-Link / Antennen / Testpoints

Versorgung, Mainboard-Anbindung, Antennen-Aggregation und Bring-up des RF-Core-Boards.

## Power
- Eingang über `J_RFCORE` (Mainboard Sheet 17): `+3V3_SYS` (+ ggf. lokale LDOs für rauschempfindliche Radios).
- Getrennte, gefilterte Analog-/RF-Rails wo nötig (Ferrit/π-Filter je Radio).

| Netz | Rolle | Status |
|---|---|---|
| `+3V3_SYS` | Eingangsrail über `J_RFCORE` | FIXED (Name kanonisch) |
| `V3V3_RF` | gefilterte RF-Rail hinter dem π-Filter, **board-lokal** | TARGET |

**Gezeichnet ist der eine Eingangspfad** (`+3V3_SYS` → Ferrit → `V3V3_RF`, π-Filter
gegen `GND`). Wie viele solcher Rails es am Ende gibt, entscheidet sich mit den
Radio-Blättern 02–06 — den Rail-Zuschnitt hier vorwegzunehmen hieße, ihn zu
erfinden. Ferrit-Impedanz und Kondensatorwerte sind TBD 📄 (→ G09, mit dem Layout).

## Host-Link (zum Mainboard)
| Netz | Funktion |
|---|---|
| `RFC_SPI_*`, `RFC_UART_*` | gemeinsame Radio-Busse (getrennte CS/Selektoren) |
| `RFC_I2C_*` | NFC (PN7160) |
| `RF_KILL`, `TX_GATE_OK` | Sicherheitspfad (Sheet 01) |
| `RFC_IRQ_*` | Sammel-IRQs der Radios |

## Antennen-Aggregation
| Feed | Radio |
|---|---|
| `ANT_SUBGHZ` | CC1101/SX1262 (Sheet 02) |
| `ANT_2G4` / `ANT_ZWAVE` | CC2652P7 / EFR32ZG23 (Sheet 03) |
| HF-Loop | PN7160 (Sheet 04) |
| LF-Coil | LF-RFID (Sheet 04) |
| `ANT_UHF` | E710 (Sheet 05) |
| IR-Fenster | IR (Sheet 06) |
→ Verteilung auf Antennen-Rail (4× SMA) + interne Antennen; Isolation zwischen Bändern.

### Warum hier keine `ANT_1..ANT_4` stehen

Die Feeds tragen auf diesem Blatt ihren **physikalischen** Namen (`ANT_SUBGHZ`,
`ANT_2G4`, `ANT_ZWAVE`, `ANT_UHF`), nicht den kanonischen. Welcher Feed auf
welchem SMA landet, ist TBD 📄 (→ G09); ein Netz hat genau **einen** Namen, also
lässt sich der kanonische erst nach dem Antennen-Freeze vergeben.

Jede Kette läuft `Quelle (Sheet 02/03/05) → Matching-Platz → Übergabe-Pad`. Zwei
Details sind Absicht:

* **Der Abschnitt hinter dem Matching-Platz bleibt unbenannt.** Ein Matching-Platz
  ist ein Serienelement — links und rechts liegen zwei verschiedene Netze. Beiden
  denselben Namen zu geben hätte die Anpassung in der Netzliste stillschweigend
  überbrückt (derselbe Fehler wie bei den PCIe-Serien-Cs, Session 30).
* **Es wird kein Übergabe-Stecker gezeichnet.** Ob die Feeds über den
  Mainboard-Verbinder laufen oder per Koax direkt zur Antenna-Rail, ist genau die
  offene Frage — ein gezeichneter Stecker wäre die Antwort darauf, die es noch
  nicht gibt. Siehe die Notiz im [Netz-Wörterbuch](../../INTERFACE_NETS.md).

HF-Loop (PN7160), LF-Coil und IR-Fenster gehen **nicht** auf SMA — eigene
Strahler, deshalb hier nicht aggregiert.

## Testpoints (gestaffelter Bring-up)
- **Zuerst:** `RF_KILL` + jeder `PA_EN_*` (physische Kill-Wirksamkeit vor jedem TX-Test).
- Power-Rails, Host-Busse (`RFC_SPI/UART/I2C`), Radio-Resets.
- Pro-Radio-RSSI/TX-Check über Host-SW (RK3576).

## Nicht auf diesem Blatt

- **Der Host-Bus** (`RFC_SPI_*`, `RFC_UART_*`, `RFC_I2C_*`, `RFC_IRQ_*`). Das
  Wörterbuch führt ihn nur als **Muster** — wie viele Chip-Selects und
  IRQ-Leitungen es gibt, hängt an den Radio-Blättern. Folgt mit dem Bus-Freeze (G07).
- **Der Supervisor-Teil von `J_RFCORE`.** Der steht auf [Sheet 01](sheet_01_supervisor_rfkill.md)
  und gehört zu demselben physischen Stecker; ihn hier ein zweites Mal zu zeichnen
  hätte zwei Stecker für ein Signal bedeutet. Pin-Budget und Steckertyp: TBD 📄.

## Kritische Design-Notizen
- **RF-Kill zuerst verifizieren** (Sheet 01) — kein TX-Test ohne bestätigten Gate.
- Rail-Filterung gegen gegenseitige Radio-Störung; Masse-/Schirmkonzept.
- Antennen-/Band-Isolation (besonders 2,4 GHz vs. Wi-Fi/BT auf Mainboard, UHF vs. Sub-GHz).

## ERC-Absicht
Rails Power-Input; Host-Busse konsistent zum Mainboard-Connector; Antennen-Feeds eindeutig; Sicherheitsnetze (`RF_KILL`/`PA_EN_*`) mit Sheet 01 abgeglichen.
