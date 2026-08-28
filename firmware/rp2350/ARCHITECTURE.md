# RP2350B System-Manager — Architektur

## 1. Ausführungsmodell

**Kooperativ, tickbasiert, Always-On.** Ein deterministischer Superloop auf **Core 0** treibt alle Module über einen einheitlichen Vertrag (`init` → `tick` → `event`). **Core 1** ist reserviert für zeitkritische/latenzsensible Aufgaben (Haptik-Wellenform, RF-Kill-Latch-Überwachung), damit ein hängendes Modul den Sicherheitspfad nicht blockiert.

```
Core 0 (Superloop, ~1 kHz Basistakt):
  for each module in ORDER:
      module.tick(now_us)
  service rk3576_link (RX/TX)
  kick hardware watchdog        // nur wenn alle Pflichtmodule OK

Core 1 (Echtzeit):
  haptic waveform DMA/PWM
  rf_kill latch monitor         // liest den physischen Kill-Zustand direkt
```

**Warum kooperativ statt RTOS:** vorhersagbare Worst-Case-Latenz, kleiner Footprint, kein Scheduler-Risiko im Sicherheitspfad. Ein Modul darf pro `tick` nicht blockieren (Budget: **< 200 µs**), lange Arbeit wird in Zustandsschritte zerlegt.

## 2. Modul-Landkarte

Reihenfolge im Superloop = Sicherheitspriorität (oben zuerst).

| # | Modul | Verantwortung | Kritikalität |
|---|---|---|---|
| 1 | `rf_kill` | Physischen TX-Disable-Pfad zum RF-Core **erzwingen**; Zustand latchen | **safety-critical** |
| 2 | `power` | Rail-Sequencing, Ein/Aus, Brown-out, Ladefreigabe | **safety-critical** |
| 3 | `watchdog` | HW-Watchdog nur bei gesundem System kicken; Fault-Eskalation | **safety-critical** |
| 4 | `battery` | 2S2P-4×21700-Gauge, SoC/SoH, Temperatur, Schutzgrenzen | hoch |
| 5 | `fan` | Dual-Blower-Regelung nach Sensor-/RF-Last (P/Q-Kurven → Gate G10) | hoch |
| 6 | `sensors` | IMU/Temp/ALS o.ä. einlesen, filtern, bereitstellen | mittel |
| 7 | `buttons` | Power/Softkeys entprellen, Kurz/Lang/Combo, Recovery-Combo | mittel |
| 8 | `touch_ring` | Ø40-Ring auswerten (Position/Geste), an RK3576 melden | mittel |
| 9 | `haptic` | Haptik-Wellenformen (Core 1), Event-getrieben | niedrig |
| 10 | `rk3576_link` | Protokoll-Endpunkt zu Linux (siehe PROTOCOL.md) | hoch |
| 11 | `recovery` | DFU/BOOTSEL, Failsafe, Firmware-Update-Handshake | mittel |
| 12 | `protocol` | Frame-Codec (Encode/Decode/CRC) — von `rk3576_link` genutzt | hoch |

Jedes Modul erfüllt den Vertrag in [`include/onex_modules.h`](include/onex_modules.h). Der Vertrag ist **pin-unabhängig**; die Hardwarezugriffe kapselt später eine HAL-Schicht (nach Mainboard-Schaltplan, HOLD).

## 3. System-Zustandsmaschine

```
        ┌────────┐  power-btn long / RK3576 boot-req   ┌────────┐
        │  OFF   │ ─────────────────────────────────▶  │  BOOT  │
        └────────┘                                      └────────┘
             ▲                                               │ rails OK + RK3576 „alive"
   rails down│                                               ▼
        ┌────────┐   idle timeout / RK3576 suspend     ┌────────┐
        │SHUTDOWN│ ◀───────────────────────────────    │  RUN   │
        └────────┘                                      └────────┘
             ▲                                          │      ▲
             │ fault (batt/therm/wd)                    │ mem  │ resume (Touch/Power-IRQ)
             │                                          ▼      │
        ┌────────┐                                   ┌────────┐
        │ FAULT  │ ◀──────────────────────────────── │SUSPEND │
        └────────┘   (RF-Kill bleibt in JEDEM Zustand wirksam)
```

- **RF-Kill ist zustandsunabhängig:** In OFF/BOOT/RUN/SUSPEND/SHUTDOWN/FAULT bleibt ein aktivierter Kill physisch wirksam. Er kann nur durch **explizite, bewusste** Nutzeraktion + Regulierungsprofil-Freigabe aufgehoben werden — nie allein durch Linux-Software.
- **FAULT** ist ein sicherer Ruhezustand: RF-Kill an, Rails minimal, Ursache über `rk3576_link` gemeldet, Recovery möglich.

## 4. Fehler-/Watchdog-Politik
- `watchdog.tick` kickt den HW-Watchdog **nur**, wenn alle `safety-critical`-Module im letzten Zyklus `OK` meldeten.
- Modul-Fault → eskaliert an `power`/`rf_kill` → System nach **FAULT**.
- Doppelte Absicherung: HW-Watchdog resettet den RP2350 bei Superloop-Stillstand; nach Reset startet Firmware in **sicherem Default** (RF-Kill **an**, Rails aus).

## 5. Sicherheits-Grundsatz (RF-Kill)
Der TX-Disable-Pfad ist **hardware-erzwungen und softwareunabhängig** (Master-Spec: RF-Core hat „physical TX/RF-kill"). Firmware-Rolle: Kill **setzen/latchen/überwachen**, nie ein reiner Software-Flag. Default nach Boot/Reset/Fault = **Kill aktiv**. Deckt sich mit dem rechtlichen Rahmen (Sendefunktionen nur mit Regulierungsprofil + bewusster Freigabe).
