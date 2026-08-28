# ONE-X — Software-/UI-Konzept

Bedien- und Oberflächenkonzept für den **5″-Touch (Landscape 1280×720)**. Läuft als Linux-Applikationsschicht auf dem RK3576 (Wayland/Compositor). Konzept-Stand — **kein** implementiertes UI.

> Mockup: [`mockup_home.svg`](mockup_home.svg) (Launcher-Home, native Auflösung).

## 1. Leitidee

Die UI spiegelt die **Hardware-Realität** statt eine generische App-Wand zu sein:
- **Vier Funkdomänen** als farbkodierte Bereiche — identische Farben wie [`../../docs/graphics/architecture.svg`](../../docs/graphics/architecture.svg): Compute/System (teal), Control, HyperRF/SDR (violett), RF-Core (amber), Konnektivität (blau).
- **Reife sichtbar:** HOLD/TARGET-Bauteile tragen ein Micro-Badge (z.B. „FPGA · HOLD (G04)", „5G/NTN · TARGET"). Die Spec-Disziplin reicht bis in die Oberfläche — die UI verspricht nie mehr, als die Hardware belegt.
- **Sicherheit zuerst:** Der **RF-Kill-Zustand** ist dauerhaft in der Statusleiste (rot = aktiv) und kommt direkt aus der RP2350-Telemetrie.

## 2. Eingabemodell (an die Hardware gebunden)

Vier Eingabewege, jeder mit klarer Rolle (Master-Spec-FIXED-Controls):

| Eingabe | Primäre Rolle | Beispiele |
|---|---|---|
| **Touch (5″ kapazitiv)** | direkte Auswahl, Karten, Tastatur | Kachel öffnen, Wert setzen |
| **Touch-Ring Ø40 (links)** | kontinuierliches Tuning / Scrollen | Frequenz, Verstärkung, Listen |
| **D-Pad (rechts)** | diskrete Navigation, blind bedienbar | Fokus bewegen, bestätigen |
| **5 Softkeys (unten)** | kontextsensitive Aktionen | Menü · Zurück · Scan · Favorit · Power |

- Softkey-Beschriftung ist **immer** am unteren Rand über den 5 physischen Tasten sichtbar und **kontextabhängig**.
- **Blindbedienbarkeit:** Jede Kernaktion ist ohne Touch (nur D-Pad + Softkeys) erreichbar — wichtig im Feldeinsatz.
- Touch-Datenpfad läuft über den RK3576; der RP2350 liefert nur Wake-IRQ (Spec-FIXED).

## 3. Informationsarchitektur

```
Home (Launcher)
├── HyperRF · SDR      Spektrum · Wasserfall · Signal-ID · Rec/Replay   [FPGA HOLD]
├── RF-Core            Sub-GHz · NFC/RFID · Zigbee/BLE · Infrarot        [Kern FIXED]
├── Konnektivität      WLAN 6E · Ethernet ×2 · 5G/NTN · GNSS            [5G/NTN TARGET]
└── System             Dateien · Terminal · Einstellungen · RF-Kill      [RP2350-Telemetrie]
```

Jede App ist eine fokussierte „Werkstatt"; die Statusleiste (Uhr, RF-Kill, Akku, Netz) bleibt global.

## 4. Anbindung an die Firmware (RP2350B-Link)

Die UI ist ein **Consumer der RP2350-Telemetrie** über das [ONE-X-Link-Protokoll](../../firmware/rp2350/PROTOCOL.md):

| UI-Element | Quelle |
|---|---|
| RF-Kill-Indikator | `EVT_HEARTBEAT.flags bit0` / `EVT_RFKILL` |
| Akku-Anzeige 82 % | `EVT_BATTERY` |
| Lüfter/Watchdog-Status | `EVT_HEARTBEAT.state` |
| „RF-Kill · Freigabe"-Kachel | `CMD_RFKILL_SET engage=0` (nur mit Regulierungsprofil+Token → sonst `NACK(policy)`) |
| Softkeys/Touch-Ring-Events | `EVT_BUTTON` / `EVT_TOUCHRING` |
| Haptik-Feedback | `CMD_HAPTIC` |

> **RF-Kill-Freigabe ist bewusst kein einfacher Toggle:** Die UI stellt eine Anfrage; der Always-On-RP2350B entscheidet nach Policy. So kann die Oberfläche einen Sender nie allein freischalten.

## 5. Umsetzungs-Skizze (später, nach G01)
- Compositor: Wayland (Weston/labwc-Klasse) mit `transform` für Landscape (SW-Rotation, siehe [`../BRINGUP_CHECKLIST_G01.md`](../BRINGUP_CHECKLIST_G01.md) Abschnitt 5).
- App-Framework: offen (TARGET) — Kandidaten GTK4/Qt/immediate-mode; Auswahl erst nach G01/Perf-Messung.
- Status: **Konzept.** Keine Implementierung, bis das Display real läuft (G01).
