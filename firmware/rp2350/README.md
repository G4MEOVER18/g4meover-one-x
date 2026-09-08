# ONE-X — RP2350B System-Manager-Firmware (`firmware/rp2350/`)

Always-On-System-Manager auf **RP2350B + 16 MB QSPI** (beides **FIXED**, Master-Spec `compute.control_mcu`). Deckt **Phase 2** der [Roadmap](../../docs/ROADMAP.md) ab: die **Modul- und Protokoll-Architektur**.

## Rolle (FIXED — Master-Spec `compute.control_role`)

> „power/wake/buttons/sensors/haptics/fans/status/debug; **NOT main Linux framebuffer**"

Der RP2350B ist ein **zweiter, von Linux unabhängiger Rechner**. Er läuft weiter, wenn der RK3576/Linux hängt, und ist die **einzige** Instanz, die den physischen **RF-Kill** und das Power-Sequencing erzwingt.

```
        ┌────────────────────────── RP2350B (Always-On) ─────────────────────────┐
Tasten ▶│ buttons  touch_ring  haptic   sensors  battery  fan   power   watchdog │
IRQ    ▶│                                                                         │
        │   rf_kill (HW-erzwungen) ──▶ physischer TX-Disable-Pfad zum RF-Core     │
        │   rk3576_link (Protokoll) ◀──UART/SPI──▶  RK3576 · Linux                │
        │   recovery (DFU/BOOTSEL)                                                │
        └─────────────────────────────────────────────────────────────────────────┘
```

## Nicht-Ziele (bewusst)
- **Kein** Linux-Framebuffer/Display-Treiber (das macht der RK3576 direkt über MIPI-DSI, siehe [`../../linux/`](../../linux/)).
- **Keine** High-Level-RF-Protokolle (die laufen als Linux-SW auf dem RK3576 bzw. auf FPGA/RF-ICs).
- **Kein** Netzwerk/Storage.

## Statusdisziplin
- **FIXED:** MCU (RP2350B), QSPI (16 MB), Rolle, RF-Kill = physisch/softwareunabhängig, Modul-Set.
- **HOLD:** **alle** GPIO-/Pin-/Bus-Zuordnungen (hängen vom Mainboard-Schaltplan ab → Gate G07). Deshalb definiert diese Phase **pin-unabhängige** Verträge, keine Pinmaps.
- **TARGET:** konkrete Sensor-/Haptik-/Fan-Bauteile.

## Inhalt

| Datei | Inhalt |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Ausführungsmodell (kooperativ, Always-On), Zustandsmaschine, Modul-Landkarte |
| [`PROTOCOL.md`](PROTOCOL.md) | RK3576 ↔ RP2350-Link: Framing, CRC, Nachrichten-Set, RF-Kill-Semantik |
| [`include/onex_proto.h`](include/onex_proto.h) | C-Header: Frame-/Nachrichtendefinition (pin-unabhängig, implementierbar) |
| [`include/onex_modules.h`](include/onex_modules.h) | C-Header: Modul-Vertrag (`init`/`tick`/`event`) + Modul-Enum |
| [`include/onex_rfkill.h`](include/onex_rfkill.h) | C-Header: RF-Kill-Zustandsautomat (Zustände, Gründe, Freigabe-Policy) |
| [`include/onex_link.h`](include/onex_link.h) | C-Header: Protokoll-Endpunkt `rk3576_link` |
| [`include/onex_power.h`](include/onex_power.h) | C-Header: Rail-Sequencing + System-Zustandsmaschine |
| [`include/onex_watchdog.h`](include/onex_watchdog.h) | C-Header: Gesundheitswächter (Kick-Erlaubnis, Eskalation) |
| [`include/onex_sched.h`](include/onex_sched.h) | C-Header: Superloop-Scheduler (Modul-Tabelle, Events, Budget) |
| [`src/onex_proto.c`](src/onex_proto.c) | **Implementierung** des Frame-Codecs (CRC-16, Encode, Decode, Resync) |
| [`src/onex_rfkill.c`](src/onex_rfkill.c) | **Implementierung** des RF-Kill-Automaten (safety-critical, Priorität 0) |
| [`src/onex_link.c`](src/onex_link.c) | **Implementierung** des Endpunkts: RX/Dispatch/ACK-NACK, Heartbeat, Events |
| [`src/onex_power.c`](src/onex_power.c) | **Implementierung** von Rail-Sequencing + Zustandsmaschine (safety-critical) |
| [`src/onex_watchdog.c`](src/onex_watchdog.c) | **Implementierung** des Wächters (safety-critical) |
| [`src/onex_sched.c`](src/onex_sched.c) | **Implementierung** des Superloops — fährt die Modul-Tabelle |
| [`test/test_onex_proto.c`](test/test_onex_proto.c) | Host-Unit-Tests — frieren das Wire-Format als Regressionsschranke ein |
| [`test/test_onex_rfkill.c`](test/test_onex_rfkill.c) | Host-Unit-Tests — überwiegend **negativ**: was *nicht* freigeben darf |
| [`test/test_onex_link.c`](test/test_onex_link.c) | **Integrationstests** — echte Abläufe über die Drahtdarstellung |
| [`test/test_onex_power.c`](test/test_onex_power.c) | Host-Unit-Tests für `power` + `watchdog` + Kopplung an den RF-Kill |
| [`test/test_onex_sched.c`](test/test_onex_sched.c) | Host-Unit-Tests für den Superloop (Reihenfolge, Events, Budget) |

## Was hier schon *verifiziert* ist

Die hardware-unabhängige Schicht wird **auf dem Host kompiliert und getestet** — lange bevor es EVT-Hardware gibt:

```
python tools/fw_test.py        # bauen + ausführen (Teil von tools/check_all.py)
```

Das geht, weil der Codec bewusst **frei von Pin-/HAL-Annahmen** ist (alle GPIO-Zuordnungen sind HOLD bis Gate G07). Übersetzt wird mit `-Wall -Wextra -Werror -Wconversion -Wshadow` — Warnungen sind Fehler, denn was auf dem Host warnt, warnt auf dem Cortex-M33 auch, nur bemerkt es dort niemand.

Abgedeckt: CCITT-FALSE-Normvektor, Wire-Layout byteweise, Roundtrip über **alle** Payload-Längen 0…255 (beide Grenzen), unvollständige Frames, CRC-Fehler, unbekannte Version, führender Leitungsmüll, Resync-Fortschrittsgarantie und ein Empfangsstrom, der sich nach einem zerstörten Frame nachweislich wieder fängt.

Vor dem Build läuft eine **statische Vorprüfung** auf fehlende `<stddef.h>`-Includes. Grund: Manche libc-Implementierungen (MinGW) ziehen `NULL`/`size_t` beiläufig über `<stdint.h>` mit herein, glibc nicht — solcher Code kompiliert lokal anstandslos und fällt erst in der CI um. Die Prüfung löst den Include-Graph über die eigenen Header auf und braucht keinen Compiler.

Zwei Eigenschaften sind **sicherheitsrelevant** und deshalb je durch einen eigenen Test festgenagelt:
1. **CRC wird vor der Version geprüft.** Nur so ist die SEQ, die ein `NACK(version)` zurückspiegelt, durch die Prüfsumme gedeckt ([`PROTOCOL.md` §5](PROTOCOL.md)).
2. **Resync springt hinter den defekten Anker**, nicht auf Byte 1 — sonst fände der Parser bei führendem Müll denselben kaputten Frame erneut und träte auf der Stelle.

## RF-Kill — Freigabe-Policy (Owner-Entscheidung 2026-09-07)

Der Zustandsautomat setzt [`PROTOCOL.md` §4](PROTOCOL.md) und [RF-Core Sheet 01](../../hardware/rf-core/schematic/sheet_01_supervisor_rfkill.md) um. Vier Zustände: **ENGAGED** (Kill, Default) · **ARMED** (Freigabefenster offen — TX weiterhin gesperrt) · **RELEASED** (TX frei) · **FAULT** (gelatcht).

**Kill ist billig, Freigabe ist teuer** — die Asymmetrie ist Absicht:

- `engage=1` wirkt **immer und sofort**: ohne Token, ohne Regulierungsprofil, in jedem Zustand. Sicherheit darf nie an einer Prüfung scheitern.
- `engage=0` ist eine Anfrage und braucht **alles**: physische Geste am Gerät, offenes Zeitfenster, gültiges Regulierungsprofil, korrektes Token, kein Fault, kein Notfallschalter.

| Entscheidung | Festlegung |
|---|---|
| **Token-Semantik** | Nonce, das der RP2350 **nur nach einer physischen Taste/Ring-Geste** ausgibt. Software allein — auch kompromittiertes Linux — kann damit nie senden. **One-Shot:** nach jeder Anfrage verbraucht, auch bei Ablehnung (sonst im offenen Fenster erratbar). Ohne Entropiequelle wird gar kein Token ausgegeben und jede Freigabe scheitert. |
| **Link-Verlust** | Karenzzeit (`ONEX_RFKILL_LINK_GRACE_MS`, TARGET 3 s), dann Kill mit Grund `LINK_LOSS`. Kurze Aussetzer würgen keine laufende autorisierte Messung ab, ein echter Absturz führt aber zuverlässig zum funkstillen Zustand. |
| **Freigabefenster** | `ONEX_RFKILL_ARM_TTL_MS` (TARGET 10 s) nach der Geste, danach neue Geste nötig. |
| **Gate-Abgleich** | `TX_GATE_OK` ist die **Wahrheit**, nicht der Befehl. „Wir killen, aber TX ist physisch frei" heißt: der Kill-Pfad wirkt nicht → **FAULT, gelatcht**, nur per bewusstem `clear_fault()` (und der führt nach ENGAGED, nie direkt nach RELEASED). Die Gegenrichtung (freigegeben, Gate noch nicht ok) ist Einschwingzeit und **kein** Fault. |

Beide Zeitkonstanten sind **TARGET**, nicht FIXED — im Feld abstimmbar über `onex_rfkill_configure()`.

Die Testsuite ist bewusst überwiegend **negativ**: jede einzelne Bedingung der Freigabekette hat einen eigenen Test, in dem genau sie — und nur sie — verletzt ist. Dazu Millisekunden-Zähler-Überlauf (~49,7 Tage Always-On, im Feld erreichbar), Profilverlust im laufenden Betrieb und `NULL`-Eingänge (→ killen, nicht raten).

## `rk3576_link` — der Protokoll-Endpunkt

Führt Codec und RF-Kill zu einem bedienbaren Link zusammen: Bytestrom → Frames → Kommando → `ACK`/`NACK`, dazu Heartbeat (~1 Hz) und Events. Der Transport (UART primär, SPI optional — Busauswahl HOLD bis G07) hängt an einem Schreib-Callback, deshalb ist auch der Endpunkt vollständig host-testbar.

Drei Entscheidungen prägen sein Verhalten:

- **Wiederholungen wirken genau einmal.** Der Host kann ein verlorenes Kommando nicht von einer verlorenen Antwort unterscheiden und wiederholt bei Timeout. Ein Duplikat-Cache (gleiche SEQ **und** gleicher Typ) sendet dann die *gespeicherte* Antwort erneut, statt das Kommando ein zweites Mal auszuführen — sonst würde ein wiederholtes `CMD_POWER reboot` doppelt wirken. Beim RF-Kill greift zusätzlich die Idempotenz des Automaten selbst.
- **Auf CRC-Fehler folgt keine Antwort.** Ist die Prüfsumme falsch, ist auch die SEQ unglaubwürdig; ein `NACK` mit geratener SEQ könnte beim Host ein ganz anderes, noch offenes Kommando als abgelehnt markieren. Bei **Versionsfehlern** wird dagegen geantwortet — dort deckt die Prüfsumme die SEQ ab. Genau dafür prüft der Codec CRC vor Version.
- **Fehlende Module sagen `BUSY`, nicht `ACK`.** Für `POWER`/`FAN`/`HAPTIC`/`LED`/`RECOVERY`/`TIME_SYNC` gibt es in Phase 2 noch keine Implementierung. Ohne registrierten Delegaten antwortet der Link mit `NACK(BUSY)` — ein `ACK` würde eine Wirkung behaupten, die es nicht gibt. Ebenso meldet der Heartbeat ohne RF-Kill-Modul **Kill aktiv**: ein fehlendes Sicherheitsmodul darf nie als „TX frei" erscheinen.

Der Puffer erholt sich nachweislich aus einer Müllflut (Resync statt Blockade — ein stehender Link wäre schlimmer als Datenverlust), und jeder gültige Frame speist die RF-Kill-Karenz.

## `power` — Rail-Sequencing und Systemzustand

Setzt die Zustandsmaschine aus [`ARCHITECTURE.md` §3](ARCHITECTURE.md) und den [Power-Tree](../../hardware/mainboard/schematic/sheet_01_power_tree.md) um. Einschaltreihenfolge `VSYS → +5V_SYS → +3V3_SYS → PMIC`, Abschalten exakt umgekehrt — beides durch Tests festgenagelt.

Zwei Randbedingungen kommen direkt aus der Hardware:

- **`+3V3_AON` ist Voraussetzung, kein Sequenzschritt.** Die Rail speist den RP2350B selbst („immer zuerst / immer an"). Ein Controller kann seine eigene Versorgung nicht sequenzieren — fällt sie weg, ist nichts mehr verlässlich (`FAULT_AON_LOST`).
- **Die RK806S-Rail-Map ist HOLD.** Welche RK3576-Rails in welcher Reihenfolge kommen, braucht die Rockchip-Referenz. Der PMIC wird deshalb als Black-Box mit *einem* Enable und *einem* Power-Good behandelt — **die HOLD-Grenze ist die Modulgrenze**, nichts wird geraten.

**Nie endlos warten:** Jeder Sequenzschritt hat eine Frist; bleibt Power-Good aus, geht es nach `FAULT` statt in eine stille Endlosschleife. Ebenso, wenn der RK3576 nach der PMIC-Freigabe nicht lebendig wird. `FAULT` ist gelatchter, sicherer Ruhezustand (Rails aus, Ursache meldbar); der Ausgang führt über einen bewussten `clear_fault()` **nach OFF**, nie direkt zurück nach RUN. Der **erste** Fehlercode bleibt stehen — Folgefehler sind Symptome, die Erstursache ist die Diagnose.

## `watchdog` — Wirkung durch Unterlassen

Das Modul kann nichts abschalten. Seine einzige Macht ist, den Hardware-Watchdog **nicht mehr zu füttern**; der löst dann den Reset aus, und danach startet die Firmware im sicheren Default (RF-Kill an, Rails aus). Der gefährliche Fehler ist deshalb nicht „kickt zu selten", sondern **„kickt weiter, obwohl etwas kaputt ist"** — und genau darauf zielen die Tests.

- Gekickt wird nur, wenn **alle** safety-critical Module (`rf_kill`, `power`, `watchdog`) OK gemeldet haben.
- **Schweigen zählt wie ein Fault.** Das fängt den Fall, den ein reiner Fehlerzähler nicht sieht: ein Modul, das hängt und deshalb gar nichts mehr meldet — auch keinen Fehler.
- **`DEGRADED` löst keinen Reset aus** (so definiert in `onex_modules.h`), ein defektes *unkritisches* Modul ebenfalls nicht.
- **Startkarenz, aber kein Freibrief:** Direkt nach dem Reset hat noch niemand gemeldet — ohne Karenz entstünde eine Reset-Schleife. Sie endet, sobald alle kritischen Module einmal gemeldet haben, spätestens nach `ONEX_WD_STARTUP_GRACE_MS`. Meldet ein Modul in dieser Zeit bereits `FAULT`, wird trotzdem nicht gekickt: die Karenz deckt Unwissenheit ab, nicht Defekte.
- Einmal entzogen, bleibt der Kick entzogen (**gelatcht**) — ein Wächter, der sich selbst wieder beruhigt, verschleiert genau die Sprunghaftigkeit, die er melden soll.

Die Kette `watchdog → power → rf_kill` aus `ARCHITECTURE.md` §4 ist durchgehend getestet: eine Eskalation bringt `power` nach `FAULT`, und der daraus abgeleitete `system_fault` sperrt den TX-Pfad.

## Build-Ziel (später)
Pico-SDK (RP2350, Cortex-M33). Die pin-abhängige HAL-Schicht kommt erst nach dem Mainboard-Schaltplan (Phase 5 / Gate G07). Alles hier ist so geschnitten, dass es **ohne** Pinmap kompiliert — Logik oben, Hardwarezugriff unten.

## Superloop-Scheduler

Fährt die Modul-Tabelle aus [`onex_modules.h`](include/onex_modules.h) so, wie [`ARCHITECTURE.md` §1](ARCHITECTURE.md) es vorgibt: Module in Tabellenreihenfolge ticken, Gesundheit an den Watchdog melden, am Ende die Kick-Erlaubnis holen.

**Die Reihenfolge ist Sicherheitsauslegung, keine Optimierung** — `rf_kill`, `power`, `watchdog` laufen vor allem anderen. Ein später laufendes Modul darf nie zwischen einen Sicherheitszustand und seine Wirkung geraten. Ein eigener Test hält die Reihenfolge fest.

**Was der Scheduler nicht kann — bewusst benannt:** Er ist kooperativ. Ein Modul, das in `tick()` blockiert, kann von ihm *nicht* unterbrochen werden; er kann die Budgetüberschreitung (200 µs, `onex_modules.h`) nur **erkennen und melden**. Die tatsächliche Rettung bei echtem Stillstand ist der Hardware-Watchdog: bleibt der Superloop stehen, wird nicht mehr gekickt, der Chip resettet, und die Firmware startet im sicheren Default. Wer von einem kooperativen Scheduler mehr verspricht, verkauft eine Sicherheit, die es nicht gibt. Fehlt die Zeitquelle, wird die Budgeteinhaltung deshalb auch **nicht behauptet**, statt „alles in Ordnung" zu melden.

**Zwei Stufen für fehlende Sicherheitsmodule**, weil der Scheduler unterschiedlich viel weiß:

| Fall | Erkennung | Wirkung |
|---|---|---|
| `init()` liefert `false` | Modul bekannt → **aktive** `FAULT`-Meldung | Kick fällt **sofort** weg |
| `NULL`-Platzhalter in der Tabelle | Modul-ID unbekannt (sie steht ja *im* Modul) | **passiv** über `reported[]` — Kick fällt nach der Startkarenz weg |

Die Tabellenposition als Modul-ID zu deuten wäre die naheliegende Abkürzung, aber eine stille Annahme, die die Tabelle nicht garantiert — daher bewusst nicht.

**Events werden aus einem Schnappschuss zugestellt.** Die Warteschlange wird *vor* der Zustellung geleert, damit ein Handler, der selbst postet, keine unbegrenzte Rekursion auslöst — sein Event läuft im nächsten Durchlauf. Läuft die Queue über, wird das **neueste** Event verworfen und gezählt: bereits angenommene Events werden garantiert zugestellt, die Reihenfolge bleibt erhalten, und der Verlust ist sichtbar statt still.
