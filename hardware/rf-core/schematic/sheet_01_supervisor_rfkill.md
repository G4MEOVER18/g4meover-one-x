# RF-Core Sheet 01 — Supervisor / RF-Kill (sicherheitskritisch)

Der **hardware-erzwungene TX-Disable-Pfad**. Master-Spec (Interface-Matrix): „software cannot override emergency TX disable". Dieses Sheet hat Vorrang vor allen Radio-Sheets.

## Prinzip

```
RF_KILL (vom RP2350, HW) ──▶ Supervisor-Gate ──┬─▶ CC1101   PA_EN / TXEN
                                                ├─▶ SX1262   PA-Ctrl / TXEN
   physischer Schalter/    ──▶  (UND-Logik,     ├─▶ CC2652P7 TX/PA
   Notfall-Kill ──────────▶      fail-safe)     ├─▶ EFR32ZG23 (Z-Wave)
                                                ├─▶ E710     (UHF PA)
   Default nach Reset =                         ├─▶ LF-RFID  (TX-Feld)
   KILL AKTIV (TX gesperrt)                     └─▶ IR-TX
```

## Regeln (nicht verhandelbar)
1. **Default nach Boot/Reset/Fault = Kill aktiv** (TX gesperrt), bis bewusst freigegeben.
2. **Softwareunabhängig:** Der Gate sitzt in Hardware zwischen jeder PA/TX-Enable und dem Radio. Linux/RK3576 kann ihn **nicht** umgehen; auch ein hängender RP2350 lässt den Pfad im sicheren Zustand (fail-safe = Kill).
3. **Autorität = RP2350-Manager** (+ optional physischer Notfallschalter). Freigabe nur mit Regulierungsprofil + Token ([ONE-X-Link](../../../firmware/rp2350/PROTOCOL.md) `CMD_RFKILL_SET`).
4. **Alle Sender** dahinter — kein Radio darf einen TX-Pfad haben, der den Gate umgeht.

## Netze

| Netz | Rolle |
|---|---|
| `RF_KILL` | Master-Kill vom RP2350 (aktiv = TX aus) |
| `RF_KILL_SW_n` | optionaler physischer Notfall-Kill (in Reihe/UND) |
| `PA_EN_<radio>` | pro Radio, **nur** über den Gate |
| `TX_GATE_OK` | Status: TX physisch freigegeben (an RP2350 zurück) |

## Umsetzung (Design)
- **Fail-safe-Logik:** Pull in Richtung „Kill" an jedem Enable; aktive Freigabe nötig. Diskrete Logik/Load-Switches statt reiner MCU-GPIOs.
- **Latch/Überwachung:** RP2350-Core1 überwacht den gelatchten Kill-Zustand (Firmware ARCHITECTURE.md).
- **Rückmeldung:** `TX_GATE_OK` → `EVT_RFKILL`/`EVT_HEARTBEAT.flags` (UI zeigt „RF-KILL AN", vgl. [`../../../linux/ui/`](../../../linux/ui/)).

## Kritische Design-Notizen
- **Kein verdeckter TX-Pfad:** Jedes Radio-Sheet muss seinen PA/TX-Enable explizit über `PA_EN_<radio>` (dieses Sheet) führen — Review-Punkt für ERC/Design-Review.
- **Sequencing:** Kill greift, bevor Radios Power/Clock bekommen.
- **Testpunkte:** `RF_KILL`, `TX_GATE_OK`, jeder `PA_EN_*` (Sheet 07) — vor jedem TX-Test messen.

## ERC-Absicht
`RF_KILL`/`PA_EN_*` eindeutig (ein Treiber), Default-Pulls Richtung Kill. Kein PA/TX-Enable ohne Gate-Netz.
