# G4MEOVER ONE-X — Autonomes Arbeitsprotokoll

> Dieses Projekt hat **absolute Priorität** und wird autonom kontinuierlich vorangetrieben.
> Jede Session trägt hier ihren Fortschritt ein (neueste oben). Regeln in `CLAUDE.md`.

## Arbeitszyklus (jede Session)
1. `docs/ROADMAP.md` öffnen → höchste unerledigte Phase / nächstes Gate.
2. Master-Spec lesen, betroffene FIXED/TARGET/HOLD prüfen (nichts raten).
3. **Einen** kohärenten Engineering-Schritt umsetzen.
4. `python tools/spec_validator.py` (muss Exit 0 liefern).
5. Diesen Worklog + Roadmap-Status fortschreiben, committen, pushen.

---

## 2026-09-08 — Session 24 (Superloop-Scheduler — Phase 2 im Kern abgeschlossen)

**Umgesetzt:** `include/onex_sched.h` + `src/onex_sched.c` + `test/test_onex_sched.c` (**46 Prüfungen**). Der Scheduler fährt die Modul-Tabelle aus `onex_modules.h` so, wie `ARCHITECTURE.md` §1 es vorgibt: Module in Tabellenreihenfolge ticken, Gesundheit an den Watchdog melden, Kick-Erlaubnis holen. Gesamt **294 Prüfungen** in 5 Suiten; check_all 4/4.

Damit ist **Phase 2 im Kern abgeschlossen**: Codec, RF-Kill, Link-Endpunkt, Power, Watchdog und Superloop sind implementiert und host-getestet. Was bleibt, braucht Externa (HAL/Pinmap nach G07, Vendor-Daten für die HOLDs).

**Entwurfsentscheidungen:**
- **Reihenfolge = Sicherheitsauslegung, keine Optimierung.** `rf_kill`, `power`, `watchdog` laufen vor allem anderen; ein später laufendes Modul darf nie zwischen einen Sicherheitszustand und seine Wirkung geraten. Eigener Test hält das fest.
- **Zeitbasis µs.** Der Vertrag gibt `tick(uint64_t now_us)` vor — richtig so, denn das 200-µs-Budget ist in ms nicht messbar. `uint64` µs läuft praktisch nie über; die Adapter rechnen für die Module auf `uint32` ms um, wo der bekannte 49,7-Tage-Wrap greift, den sie bereits behandeln.
- **Ehrlichkeitsgrenze benannt:** Ein kooperativer Scheduler kann ein blockierendes `tick()` **nicht unterbrechen** — nur erkennen und melden. Die Rettung bei echtem Stillstand ist der HW-Watchdog. Fehlt die Zeitquelle, wird Budgeteinhaltung deshalb auch **nicht behauptet** (`budget_exceeded` bleibt false), statt „alles in Ordnung" zu melden.
- **Events aus einem Schnappschuss.** Die Queue wird *vor* der Zustellung geleert → ein Handler, der selbst postet, kann keine unbegrenzte Rekursion auslösen; sein Event läuft im nächsten Durchlauf. Bei Überlauf wird das **neueste** Event verworfen und gezählt: angenommene Events werden garantiert und in Reihenfolge zugestellt, der Verlust bleibt sichtbar.

**Zwei Stufen für fehlende Sicherheitsmodule** (der Scheduler weiß unterschiedlich viel):
| Fall | Erkennung | Wirkung |
|---|---|---|
| `init()` == false | Modul bekannt → **aktive** FAULT-Meldung | Kick fällt **sofort** weg |
| `NULL`-Platzhalter | Modul-ID unbekannt (steht *im* Modul) | **passiv** über `reported[]` → Kick fällt nach der Startkarenz weg |

Die Tabellenposition als Modul-ID zu deuten wäre die naheliegende Abkürzung — aber eine stille Annahme, die die Tabelle nicht garantiert. Bewusst nicht gemacht; der Test prüft stattdessen beide Zeitpunkte (während der Karenz läuft das System an, danach nicht mehr).

**Drei Funde:**
1. **Testfehler bei mir:** `test_missing_critical_module_blocks_kick` prüfte bei 1 ms — mitten in der 2-s-Startkarenz — und schlug zu Recht fehl. Die Ursachenanalyse ergab den obigen Zwei-Stufen-Unterschied; Test auf beide Zeitpunkte erweitert statt die Erwartung abzuschwächen.
2. **Redundanter Code durch Mutation aufgedeckt (S5):** `onex_sched_init` meldete deaktivierte Sicherheitsmodule an den Watchdog — die Schleife in `run_once()` tut das ohnehin in jedem Durchlauf, und der Watchdog wird ausschließlich dort ausgewertet. Die init-Meldung war strikt überflüssig. **Dasselbe Muster wie der `tx_allowed`-Fund in Session 21**: zwei Kopien einer Regel driften auseinander. Entfernt statt dokumentiert.
3. **Folgefehler daraus:** Nach dem Entfernen war der Parameter `now_us` in `onex_sched_init` tot — `-Werror=unused-parameter` fing es sofort. Statt mit `(void)` zu kaschieren aus der Signatur entfernt (Header ist neu, keine Bruchgefahr).

**Mutationslauf 7/7 gefangen** (nach der Bereinigung): Reihenfolge umgedreht → 4 · Queue erst nach Zustellung geleert → 1 · Gesundheit nicht gemeldet → 3 · `init()==false` deaktiviert nicht → 5 · verbliebene FAULT-Meldestelle → 1 · Budgetüberschreitung ignoriert → 3 · ohne Watchdog trotzdem kicken → 1.

**Keine Spec-Änderung, keine HOLDs berührt.**

**Nächster Schritt (Session 25+):** (a) echte KiCad-Zeichnung → G07 (braucht KiCad + Vendor-Libs); (b) HOLDs mit Vendor-Rückmeldungen schließen (G02/G03/G04/G05/G06); (c) optional die verbleibenden unkritischen Module (`buttons`, `touch_ring`, `haptic`, `battery`, `fan`, `sensors`, `recovery`) — deren Logik ist aber weitgehend HAL-nah und damit erst nach G07 sinnvoll testbar.

---

## 2026-09-08 — Session 23 (`power` + `watchdog` — Sicherheitskette vollständig)

**Umgesetzt:** Die beiden verbleibenden safety-critical Module. Damit ist die Kette `watchdog → power → rf_kill` aus `ARCHITECTURE.md` §4 **durchgehend implementiert und getestet**. Neu: `include/onex_power.h` + `src/onex_power.c`, `include/onex_watchdog.h` + `src/onex_watchdog.c`, `test/test_onex_power.c` (**80 Prüfungen** für beide Module plus ihre Kopplung). Gesamt **248 Prüfungen** in 4 Suiten; check_all bleibt 4/4.

**`power` — Rail-Sequencing + Zustandsmaschine.** Einschaltreihenfolge `VSYS → +5V_SYS → +3V3_SYS → PMIC` aus `sheet_01_power_tree.md`, Abschalten exakt umgekehrt (beides per Test festgenagelt). Zwei Randbedingungen kommen direkt aus der Hardware:
- **`+3V3_AON` ist Voraussetzung, kein Sequenzschritt** — die Rail speist den RP2350B selbst („immer zuerst / immer an"); ein Controller kann seine eigene Versorgung nicht sequenzieren.
- **RK806S-Rail-Map ist HOLD** → der PMIC wird als Black-Box mit einem Enable und einem Power-Good behandelt. **Die HOLD-Grenze wurde zur Modulgrenze gemacht**, statt die RK3576-interne Sequenz zu raten.

Weitere Eigenschaften: nie endlos warten (jeder Schritt hat eine Frist → sonst `FAULT`, keine stille Endlosschleife), Host-Boot-Timeout, Power-Good-Verlust im RUN = Fehler (kein geordnetes Abschalten), Brown-out/Akku/Thermik als harte Stopps, `FAULT` gelatcht mit Ausgang **nach OFF** (nie direkt nach RUN), **erster** Fehlercode bleibt stehen (Folgefehler sind Symptome). Niedriges VSYS im Zustand OFF ist ausdrücklich **kein** Fehler — sonst wäre das Gerät nach dem Einschalten sofort im FAULT.

**`watchdog` — Wirkung durch Unterlassen.** Das Modul kann nichts abschalten; seine einzige Macht ist, den HW-Watchdog nicht mehr zu füttern. Der gefährliche Fehler ist deshalb nicht „kickt zu selten", sondern **„kickt weiter, obwohl etwas kaputt ist"**. Gekickt wird nur bei durchgehend OK gemeldeten kritischen Modulen; **Schweigen zählt wie ein Fault** (fängt das hängende Modul, das nicht einmal mehr einen Fehler meldet); `DEGRADED` und defekte *unkritische* Module lösen keinen Reset aus; Entzug ist gelatcht. Die **Startkarenz** verhindert die Reset-Schleife nach dem Boot, ist aber kein Freibrief: ein explizit gemeldeter `FAULT` schlägt sie.

**Zwei Funde durch Mutationstest:**
- **Echte Testlücke (P3):** „Folgefehler überschreibt Erstursache" blieb grün. Grund: der `tick`-Pfad wertet im FAULT-Zustand gar keine Ursachen mehr aus — überschreiben kann sich nur über `onex_power_notify_fault()`, und genau diesen Pfad testete nichts. Test `test_notify_fault_keeps_first_cause` ergänzt; die Mutation fällt jetzt auf.
- **Äquivalente Mutation (W4):** Der Startwert `ONEX_HEALTH_FAULT` in `onex_watchdog_init` ist im heutigen Ablauf **nicht wirksam** — die Absicherung gegen „nie gemeldet" ist das `reported[]`-Flag, die Schleife liest `health[]` vorher gar nicht. Der Kommentar behauptete das Gegenteil und war irreführend; korrigiert auf „redundante Verteidigung, nicht durch Test abgedeckt". Kein Codefehler, aber eine falsche Begründung weniger.

**Mutationslauf (8 Mutationen):** Watchdog kickt trotz Fault → 5 · Schweigen nicht als Fault → 3 · Startkarenz deckt echte Faults → 4 · Rail-Timeout entfernt → 3 · Power-Good-Verlust ignoriert → 2 · Folgefehler überschreibt Erstursache → 1 (nach Testergänzung) · `clear_fault` führt nach RUN → 2. Eine Mutation (Startwert OK statt FAULT) ist nachweislich **äquivalent** und daher zu Recht nicht gefangen — dokumentiert statt kaschiert.

**Keine Spec-Änderung, keine HOLDs berührt.** check_all 4/4 grün.

**Nachtrag — die CI fing einen echten Portabilitätsfehler (Commit 2f50daa → Fix):** Lokal 4/4 grün, in der CI rot. Ursache: `onex_watchdog.c` nutzt `NULL`, erreichte aber nie `<stddef.h>`. **MinGW zieht `NULL` beiläufig über `<stdint.h>` mit herein, glibc nicht** — der Fehler ist auf dem Entwicklungsrechner strukturell unsichtbar. Die übrigen Module entkamen nur zufällig (`onex_power.h` erreicht `<stddef.h>` über `onex_proto.h`, `onex_rfkill.h` inkludiert es selbst); ausgerechnet `onex_watchdog.h` inkludiert `<stdint.h>` + `<stdbool.h>` + `onex_modules.h` — keiner davon liefert `NULL`.

Das ist bereits der **zweite CI-Fund dieser Art** nach dem CRLF-Determinismusfehler in Session 18. Muster: Die zweite Plattform findet, was auf der ersten unsichtbar ist. Deshalb blieb es nicht beim Ein-Zeilen-Fix — `tools/fw_test.py` hat jetzt eine **statische Vorprüfung**, die den transitiven Include-Graph über die eigenen Header auflöst und meldet, wenn eine Datei `NULL`/`size_t`/`ptrdiff_t`/`offsetof` nutzt, ohne einen `<stddef.h>`-Lieferanten zu erreichen. Gegenprobe: mit zurückgenommenem Fix meldet sie den Fehler **lokal auf MinGW**, wo der Compiler schweigt. Die Prüfung braucht keinen Compiler und läuft vor jedem Build.

**Nächster Schritt (Session 24+):** (a) Superloop-Scheduler, der die Modul-Tabelle aus `onex_modules.h` tatsächlich fährt und die Module in Prioritätsreihenfolge tickt — damit wäre Phase 2 im Kern abgeschlossen; (b) echte KiCad-Zeichnung → G07; (c) HOLDs mit Vendor-Rückmeldungen schließen.

---

## 2026-09-07 — Session 22 (`rk3576_link`: Protokoll-Endpunkt — Codec + RF-Kill zusammengeführt)

**Umgesetzt:** Der Link RK3576 ↔ RP2350B ist erstmals **als Ganzes bedienbar und getestet**. `include/onex_link.h` + `src/onex_link.c` + `test/test_onex_link.c` (**64 Prüfungen**, Integrationstests über die echte Drahtdarstellung). Gesamt jetzt **168 Prüfungen** in 3 Suiten; check_all bleibt 4/4.

Aufgaben des Moduls: Bytestrom → Frames → Kommando ausführen → `ACK`/`NACK` mit gespiegelter SEQ; Heartbeat (~1 Hz) mit `state`/`flags`/`uptime_s`; Events mit eigener, fortlaufender SEQ. Transport (UART primär, SPI optional — Busauswahl HOLD bis G07) hängt an einem Schreib-Callback → weiterhin voll host-testbar.

**Drei prägende Entscheidungen:**
1. **Wiederholungen wirken genau einmal.** `PROTOCOL.md` §2 lässt den Host bei Timeout 3×/20 ms wiederholen — er kann ein verlorenes Kommando nicht von einer verlorenen Antwort unterscheiden. Ein **Duplikat-Cache** (gleiche SEQ *und* gleicher Typ) sendet die gespeicherte Antwort erneut, statt das Kommando ein zweites Mal auszuführen. Ohne das würde ein wiederholtes `CMD_POWER reboot` doppelt wirken. Beim RF-Kill kommt die Idempotenz des Automaten als zweite Ebene dazu.
2. **Auf CRC-Fehler folgt keine Antwort.** Bei falscher Prüfsumme ist kein Header-Feld vertrauenswürdig — auch die SEQ nicht; ein `NACK` mit geratener SEQ könnte beim Host ein anderes, noch offenes Kommando als abgelehnt markieren. Der Manager schweigt und zählt nur. Bei **Versionsfehlern** wird geantwortet, weil die SEQ dort CRC-gedeckt ist — der Zweck der Prüfreihenfolge aus Session 20 zahlt sich hier konkret aus.
3. **Fehlende Module sagen `BUSY`, nicht `ACK`.** Für POWER/FAN/HAPTIC/LED/RECOVERY/TIME_SYNC gibt es noch keine Implementierung; ohne registrierten Delegaten antwortet der Link `NACK(BUSY)`. Ein ACK würde eine Wirkung behaupten, die es nicht gibt. Ebenso meldet der Heartbeat **ohne** RF-Kill-Modul „Kill aktiv" — ein fehlendes Sicherheitsmodul darf nie als „TX frei" erscheinen.

**Protokoll additiv erweitert** (v1 bleibt, keine Bruchänderung): `EVT_NONCE = 0x89` (`u8 valid, u8 nonce[8]`) als Antwort auf `CMD_GET`, plus die `CMD_GET.what`-Konstanten (STATUS/BATTERY/RFKILL/RFKILL_NONCE). Damit ist die Freigabe-Policy aus Session 21 **end-to-end über den Draht bedienbar**: Geste am Gerät → Host holt Nonce per `CMD_GET(0x04)` → spiegelt es in `CMD_RFKILL_SET engage=0`. `PROTOCOL.md` §2/§3 entsprechend nachgezogen.

**Zwei echte Funde durch Mutationstest:**
- **Testlücke:** Bei abgeschaltetem Duplikat-Cache blieb der Test „Retry erhält wieder ACK" grün — weil `onex_rfkill_request` im Zustand RELEASED bereits selbst idempotent antwortet. Der Test prüfte Zähler und ACK-Anzahl, aber **nie, ob der Delegat wirklich nur einmal gerufen wurde** — und das ist der eigentliche Schaden. Zählenden Delegaten ergänzt; L1 fängt jetzt „Kommando trotz Retry nur EINMAL ausgeführt: got 2, want 1" plus „neue SEQ führt erneut aus".
- **Ungenaue Begründung im Code:** Der Kommentar behauptete, ohne Cache käme beim RF-Kill `NACK(policy)` zurück. Tatsächlich fängt der Automat diesen Fall selbst ab. Korrigiert auf die zutreffende Darstellung (Cache = Schutz vor allem für **nicht-idempotente** Kommandos, RF-Kill doppelt abgesichert).

**Mutationslauf (5/5 gefangen, nach der Korrektur):** Duplikat-Cache abgeschaltet → 4 · Antwort auf CRC-Fehler → 1 · gültiger Frame speist Karenz nicht → 1 · fehlendes RF-Kill-Modul meldet nicht „Kill aktiv" → 1 · ACK/NACK vom Host werden beantwortet (Echo-Schleife) → 1.

**Weitere abgedeckte Fälle:** byteweise Einspeisung mit vorangehendem Leitungsmüll, RX-Puffer-Flut ohne verwertbaren Frame (Resync statt Blockade — ein stehender Link wäre schlimmer als Datenverlust), keine Echo-Schleife auf ACK/NACK des Hosts, Heartbeat-Takt und -Flags, Event-SEQ zählt hoch (Host kann Lücken erkennen), Freigabe ohne Token → `BADARG`, Kill ohne Token → `ACK`.

**Keine Spec-Änderung, keine HOLDs berührt.** check_all 4/4 grün.

**Nächster Schritt (Session 23+):** (a) `power` + `watchdog` — die letzten beiden safety-critical Module, danach ist die Sicherheitskette vollständig getestet; (b) Superloop-Scheduler, der die Modul-Tabelle aus `onex_modules.h` tatsächlich fährt; (c) echte KiCad-Zeichnung → G07; (d) HOLDs mit Vendor-Rückmeldungen schließen.

---

## 2026-09-07 — Session 21 (RF-Kill-Zustandsautomat — sicherheitskritischstes Modul, getestet)

**Umgesetzt:** `ONEX_MOD_RF_KILL` (Priorität 0 im Superloop) ist implementiert und verifiziert. Setzt `ARCHITECTURE.md` §5, `PROTOCOL.md` §4 und `hardware/rf-core/schematic/sheet_01_supervisor_rfkill.md` in ausführbare, getestete Logik um — weiterhin pin-/HAL-frei (Pinmap HOLD bis G07).

- **`include/onex_rfkill.h`** + **`src/onex_rfkill.c`** (neu) — vier Zustände: ENGAGED (Default) · ARMED (Freigabefenster, **TX weiterhin gesperrt**) · RELEASED · FAULT (gelatcht).
- **`test/test_onex_rfkill.c`** (neu) — 20 Testgruppen, **64 Prüfungen**, bewusst überwiegend **negativ**.
- `tools/fw_test.py` um die zweite Suite erweitert → **104 Prüfungen** insgesamt, check_all weiterhin 4/4.

**Owner-Entscheidungen (2026-09-07), jetzt verbindlich in Code + `PROTOCOL.md` §4:**
1. **Token = One-Shot-Nonce nach physischer Geste.** Der RP2350 erzeugt es erst, wenn am Gerät eine Taste/Ring-Geste erkannt wurde. Damit kann Software allein — auch kompromittiertes Linux — nie senden. Nach jeder Anfrage verbraucht, **auch bei Ablehnung** (sonst im offenen Fenster durch Wiederholung erratbar). Ohne Entropiequelle wird gar kein Token ausgegeben und jede Freigabe scheitert (fail-safe statt vorhersagbares Token).
2. **Link-Verlust → Karenzzeit, dann Kill.** `ONEX_RFKILL_LINK_GRACE_MS` = 3 s, `ONEX_RFKILL_ARM_TTL_MS` = 10 s — beide **TARGET**, nicht FIXED, zur Laufzeit über `onex_rfkill_configure()` abstimmbar.

**Leitprinzip: Kill ist billig, Freigabe ist teuer.** `engage=1` wirkt immer und sofort — ohne Token, ohne Profil, in jedem Zustand; Sicherheit darf nie an einer Prüfung scheitern. `engage=0` verlangt die volle Kette (Geste · Fenster · Profil · Token · kein Fault · kein Notfallschalter). Eine symmetrische Prüfung beider Richtungen wäre hier ein Designfehler.

**Gate-Abgleich als eigentlicher Zweck von `TX_GATE_OK`:** Der *gemessene* Zustand ist die Wahrheit, nicht der befohlene. „Wir killen, aber TX ist physisch frei" heißt, der Kill-Pfad wirkt nicht → **FAULT, gelatcht**, nur per bewusstem `clear_fault()` verlassbar (und der führt nach ENGAGED, nie direkt nach RELEASED). Die Gegenrichtung (freigegeben, Gate meldet noch nicht ok) ist Einschwingzeit und ausdrücklich **kein** Fault — sonst wäre jede Freigabe ein Fehlalarm.

**Echter Fund durch Mutationstest:** Die erste Fassung berechnete „TX frei" an **zwei** Stellen (Sollwert fürs Gate und Ausgabe `tx_enable`). Eine Mutation, die nur eine Kopie traf, blieb grün — genau der Bug-Typ, der in einem Sicherheitspfad tödlich ist: läuft eine Kopie weg, prüft der Diskrepanz-Abgleich gegen eine Erwartung, die nicht mehr dem Befehl entspricht. Zusammengeführt zu einer einzigen Definition (`tx_allowed()`); danach schlägt die Mutation an. **Nebenbefund über das Werkzeug selbst:** der Mutations-Grep filterte nur auf `FAIL` und verschluckte `[BUILD-FEHLER]` — ein fehlgeschlagener Build sah aus wie „Mutation nicht gefangen". Korrigiert; auch der Prüfaufbau braucht Skepsis.

**Mutationslauf nach der Korrektur (6/6 gefangen):** ARMED gibt TX frei → 1 · Token-Vergleich immer true → 3 · Gate-Mismatch-Erkennung entfernt → 5 · Link-Karenz nie ausgelöst → 5 · naive Wrap-Behandlung → 2 · Nonce nach Fehlversuch nicht verbrannt → 1. Danach Original wiederhergestellt, 104/104 grün.

**Weitere abgedeckte Fälle:** Millisekunden-Zähler-Überlauf (~49,7 Tage Always-On — im Feld erreichbar; naive Subtraktion würde die Karenz falsch bewerten), Wegfall des Regulierungsprofils im laufenden Betrieb, Notfallschalter mit Vorrang vor allem, `NULL`-Eingangsbild (→ killen, nicht raten), und kein `EVT_RFKILL`-Spam ohne Zustandswechsel.

**Keine Spec-Änderung, keine HOLDs berührt.** check_all 4/4 grün.

**Nächster Schritt (Session 22+):** (a) `rk3576_link` — Codec + RF-Kill zum Protokoll-Endpunkt zusammenführen (ACK/NACK-Politik, SEQ-Verwaltung, Heartbeat-Takt); (b) `power`/`watchdog` (die übrigen safety-critical Module); (c) echte KiCad-Zeichnung → G07; (d) HOLDs mit Vendor-Rückmeldungen schließen.

---

## 2026-09-07 — Session 20 (Firmware wird ausführbar: ONE-X-Link-Codec implementiert + getestet)

**Ausgangslage:** `include/onex_proto.h` deklarierte seit Phase 2 drei Funktionen (`onex_crc16`, `onex_frame_encode`, `onex_frame_decode`) — **ohne jede `.c`-Datei im Repo**. Protokoll-Spec und Header standen, die Implementierung fehlte. Damit war der Link RK3576 ↔ RP2350B bislang reine Papierform.

**Umgesetzt:** Der Codec ist implementiert und **maschinell verifiziert**. Erstmals wird in diesem Repo nicht nur *spezifiziert*, sondern Verhalten ausgeführt und geprüft.

- **`firmware/rp2350/src/onex_proto.c`** (neu) — CRC-16/CCITT-FALSE, Encoder, Decoder, Resync. Freistehend (kein malloc, keine libc-Strings), Zero-Copy beim Dekodieren, keine Endianness-Annahme (Mehrbyte-Felder explizit byteweise big-endian). Läuft unverändert auf Cortex-M33 und Host.
- **`firmware/rp2350/test/test_onex_proto.c`** (neu) — 11 Testgruppen, **40 Prüfungen**: CCITT-FALSE-Normvektor (`"123456789"` → `0x29B1`), Wire-Layout byteweise, Roundtrip über **alle** Payload-Längen 0…255 (beide Grenzen, inkl. Maximalframe 263 B), jedes unvollständige Präfix, CRC-Fehler, unbekannte Version, führender Leitungsmüll, Resync, und ein Empfangsstrom, der sich nach einem zerstörten Frame nachweislich wieder fängt.
- **`tools/fw_test.py`** (neu) — baut + startet die Tests mit dem System-Compiler. Bewusst **ohne** `arm-none-eabi`: geprüft wird nur die pin-/HAL-freie Logik (Pinmap bleibt HOLD bis G07). Flags `-Wall -Wextra -Werror -Wconversion -Wshadow -Wstrict-prototypes` — Warnungen sind Fehler.
- **`tools/check_all.py`** — vierter Check eingehängt, Lauf jetzt **4/4 grün**. Neu: ein Check darf **`SKIP`** melden, wenn eine externe Voraussetzung fehlt (Exit 2, z. B. kein Compiler). Das zählt nicht als FAIL, wird aber explizit ausgewiesen — ein übersprungener Check darf nie wie ein bestandener aussehen. SKIP-Pfad getestet.
- Header additiv erweitert: `ONEX_DEC_ERR_CRC` / `ONEX_DEC_ERR_VERSION` + `onex_frame_resync()`. **Keine bestehende Signatur geändert.**

**Zwei sicherheitsrelevante Entwurfsentscheidungen (je durch einen eigenen Test festgenagelt):**
1. **CRC wird vor der Version geprüft.** `PROTOCOL.md` §5 verlangt bei unbekannter `VER` ein `NACK(version)` mit *gespiegelter SEQ*. Nur bei dieser Reihenfolge ist die zurückgespiegelte SEQ überhaupt durch die Prüfsumme gedeckt — umgekehrt würde ein korrupter Frame eine erfundene SEQ zurücksenden.
2. **Resync springt hinter den defekten Anker**, nicht auf Byte 1, und springt **nicht** um `LEN` (das ist bei CRC-Fehler unglaubwürdig — ein gekipptes LEN-Byte dürfte keinen nachfolgenden echten Frame verschlucken). Ohne diese Fortschrittsgarantie stünde der Parser bei führendem Leitungsmüll endlos auf demselben kaputten Frame.

**Verifikation der Verifikation (Mutationstest):** Grüne Tests beweisen nichts, solange nicht gezeigt ist, dass sie anschlagen. Drei Regressionen wurden bewusst eingebaut und alle gefangen: Resync-Suche ab Index 1 → 2 Fehler · CRC-Init `0x0000` statt `0xFFFF` → 2 Fehler · Version-vor-CRC → 1 Fehler. Danach Original wiederhergestellt, wieder 0 Fehler.

**Wirkung:** Die Firmware-Tests laufen ab sofort bei **jedem Commit** (pre-commit-Hook → `check_all`) und in der **CI** (ubuntu-latest bringt gcc mit). Das Wire-Format zwischen RK3576 und RP2350B ist damit gegen stille Änderung gesichert, bevor die erste EVT-Platine existiert.

**Keine Spec-/Signal-Änderung, keine HOLDs berührt.** Alle GPIO-/Bus-Zuordnungen bleiben HOLD (G07). check_all 4/4 grün.

**Nächster Schritt (Session 21+):** (a) **RF-Kill-Zustandsautomat** (`ONEX_MOD_RF_KILL`) — sicherheitskritischstes Modul, ebenfalls pin-frei testbar; die Freigabe-Policy aus `PROTOCOL.md` §4 braucht eine Owner-Entscheidung (Token-Semantik, Verhalten bei Link-Verlust); (b) echte KiCad-Zeichnung (KiCad + Vendor-Libs) → G07; (c) HOLDs mit Vendor-Rückmeldungen schließen (G02/G03/G04/G05/G06).

---

## 2026-09-02 — Session 19 (README aktualisiert: CI-Badge + Verifikation + Struktur)

**Umgesetzt:** Flaggschiff-`README.md` auf den realen Reifegrad gebracht (war seit Session 1 nicht nachgezogen).
- **CI-Status-Badge** im Kopf (verlinkt auf den verify-Workflow).
- **Repository-Struktur** aktualisiert: `tools/` nennt jetzt alle Verifikations-Werkzeuge; `hardware/` erklärt `schematic/` (40 Sheets) + `kicad/` + `INTERFACE_NETS.md`; `.githooks/` + `.github/` ergänzt.
- **Neuer Abschnitt „Verifikation (grünes Tor)"** — `check_all.py`, Tabelle der drei Prüfungen, lokaler Hook + CI-Determinismus-Test. Macht die maschinell erzwungene HOLD-Disziplin öffentlich sichtbar.

Reine Doku, keine Spec-/Signal-Änderung. check_all 3/3 grün.

**Nächster Schritt (Session 20+):** (a) echte KiCad-Zeichnung (KiCad + Vendor-Libs) → G07; (b) HOLDs mit Vendor-Rückmeldungen schließen (G02/G03/G04/G05/G06); (c) weitere Inhalts-Vertiefung ohne Externa (z. B. Orphan-Netz-Audit).

---

## 2026-09-02 — Session 18 (CI-Spiegel: GitHub Actions verify-Workflow)

**Umgesetzt:** `.github/workflows/verify.yml` (neu) — serverseitiges grünes Tor, spiegelt den lokalen pre-commit-Hook, greift bei jedem Push/PR auf `main` (+ `workflow_dispatch`). Zwei Schritte:
1. `python tools/check_all.py` — aggregierter Verifikations-Lauf (read-only).
2. **Determinismus-Check** — regeneriert `spec_validator.py` + `gen_kicad_project.py` und schlägt bei einem `git diff` fehl → fängt **veraltete abgeleitete Dateien** (spec/DERIVED_*, hardware/*/kicad/* sind bewusst versioniert). Stärker als der lokale Hook (der nur read-only prüft).

**Warum wichtig:** Der lokale Hook ist opt-in pro Clone; CI greift **immer** — auch wenn jemand `install_hooks.py` nicht ausführte oder `--no-verify` nutzte. Keine externen Deps nötig (alle Tools nur Python-stdlib) → CI = nur `actions/setup-python`.

**Lokal simuliert:** beide Generatoren neu laufen lassen → kein Diff (committete derived-Dateien aktuell). `.githooks/README.md` um CI-Abschnitt ergänzt.

**CI-Fix (erster Lauf schlug fehl — genau wie beabsichtigt gefangen):** Der Determinismus-Check fand auf ubuntu einen Diff an `spec/MASTER_SPEC_FLAT.csv` (75/75 Zeilen = reine CRLF↔LF-Signatur). Ursache: Pythons `csv.writer` schreibt Default **CRLF**, das committete Blob ist LF → auf Windows lokal unsichtbar (autocrlf), auf CI sichtbar. Fix: `csv.writer(..., lineterminator="\n")` (LF, plattformunabhängig) + `.gitattributes` (generierte Dateien + tools/hooks `eol=lf`). Ein echter plattformabhängiger Bug, den nur die CI fing.

**Nächster Schritt (Session 19+):** (a) echte KiCad-Zeichnung (KiCad + Vendor-Libs) → G07; (b) HOLDs mit Vendor-Rückmeldungen schließen (G02/G03/G04/G05/G06); (c) CI-Status-Badge in Flaggschiff-README.

---

## 2026-09-01 — Session 17 (Pre-Commit-Hook + read-only-Modus der Checker)

**Umgesetzt:** `check_all.py` als **Git-Pre-Commit-Hook** verdrahtet — das grüne Tor greift jetzt automatisch bei jedem Commit.
- **Seiteneffektfreiheit zuerst:** `spec_validator.py` und `gen_kicad_project.py` um `--check` (read-only) erweitert — im Check-Modus werden **keine** abgeleiteten Dateien geschrieben (spec/DERIVED_*, kicad/*). `check_all.py` ruft nun beide mit `--check`; Lauf verändert den Arbeitsbaum nicht (per Git-Status verifiziert).
- **`.githooks/pre-commit`** (repo-verfolgt, POSIX-sh) + **`.githooks/README.md`** + **`tools/install_hooks.py`** (setzt `core.hooksPath` idempotent, markiert Hook ausführbar).
- **Live getestet:** Negativtest (verbotener Claim „6-layer mainboard" in Testdatei) → Hook **blockiert** Commit (2/3, spec_validator FAIL), kein Fehl-Commit entstanden; Testdatei entfernt. Positivtest = dieser Commit selbst (Hook 3/3 → durchgelassen).

**Nutzen:** Kein Stand mit verbotenem Claim, Netznamen-Mirror-Lücke oder kaputter KiCad-Ableitung kann mehr versehentlich committet werden. Umgehen nur bewusst via `git commit --no-verify`. Hooks sind lokal pro Clone → jeder (auch die 6h-Cloud-Routine) aktiviert einmalig `install_hooks.py`.

**Nächster Schritt (Session 18+):** (a) echte KiCad-Zeichnung (KiCad + Vendor-Libs) → G07; (b) HOLDs mit Vendor-Rückmeldungen schließen (G02/G03/G04/G05/G06); (c) Hook optional in GitHub-Actions-CI spiegeln (serverseitig, unabhängig von lokaler Aktivierung).

---

## 2026-09-01 — Session 16 (Aggregierter Verifikations-Lauf — ein grünes Tor vor G07)

**Umgesetzt:** `tools/check_all.py` (neu) — Umbrella-Runner, der die drei über die Sessions gebauten Checker nacheinander ausführt und ein kombiniertes PASS/FAIL liefert: (1) `spec_validator.py` (keine verbotenen Claims), (2) `schematic_netcheck.py` (Inter-Board-Netznamen beidseitig), (3) `gen_kicad_project.py` (KiCad-Ableitung reproduzierbar + selbstgeprüft). Exit 0 nur bei 3/3; CI-/Handoff-tauglich (konsolen-robust). **Lauf: 3/3 grün → Repo bereit für die KiCad-Phase (G07).**
- CLAUDE.md-Arbeitszyklus aktualisiert: Schritt 5/7 verweisen jetzt auf `check_all.py` (statt nur `spec_validator.py`), damit künftige autonome Sessions alle drei Checks fahren.
- Determinismus verifiziert: erneuter `gen_kicad_project.py`-Lauf erzeugt byte-identische Ausgaben (kein Git-Diff).

**Hinweis:** Versehentlich in die Konsole gepastete Package-Referenzbilder (PGA/LGA/BGA) auf Owner-Ansage ignoriert; kein daraus abgeleitetes Artefakt eingecheckt.

**Nächster Schritt (Session 17+):** (a) echte KiCad-Zeichnung starten (braucht KiCad + Vendor-Symbol-Libs) → G07 ERC; (b) `check_all.py` in eine CI/Pre-Commit-Hook hängen; (c) HOLDs mit Vendor-Rückmeldungen schließen (G02/G03/G04/G05/G06).

---

## 2026-09-01 — Session 15 (KiCad-Ableitung — deterministische Grundlage)

**Ehrliche Einordnung zuerst:** In dieser Umgebung ist **kein KiCad** installiert (`kicad-cli` fehlt) → hand-geschriebene `.kicad_sch`-S-Expressions wären nicht gegen das Binärformat verifizierbar; echte Symbole bräuchten Vendor-Pinouts (nicht raten). Deshalb liefert dieser Schritt die **verifizierbare, reproduzierbare Grundlage** der KiCad-Zeichnung, nicht fabrizierte Schaltplan-Dateien.

**Umgesetzt:**
- **`tools/gen_kicad_project.py`** (neu) — deterministischer Generator (uuid5): liest je Board `schematic/*.md`, erzeugt `hardware/<board>/kicad/`: `<board>.kicad_pro` (JSON), `hierarchy.json` (Manifest: Sheets, Netze, Inter-Board-Labels, Netz-Index), `KICAD_BUILD_PLAN.md` (Bauplan mit Global-Labels je Sheet). Selbstprüfung (JSON-Parse + Quell-Sheet-Existenz).
- **`hardware/kicad/README.md`** (neu) — erklärt Ableitung, Verifikations-Caveat, Zeichnungs-Ablauf, Regenerierung.
- Generiert für **alle 6 Boards**: mainboard(18)/rf-core(7)/ui-carrier(4)/m2-bridge(2)/antenna-rail(1)/hyperrf(8). Inter-Board-Labels aus INTERFACE_NETS abgeleitet; HOLD-Stubs korrekt erkannt (Mainboard 04/05, HyperRF 08).
- **Zwei Klassifizierungs-Bugs im Generator gefixt** (bevor committet): (1) Inter-Board-Fehltreffer `ANT_2G4`↔`ANT_2` (loses startswith → präzises `is_interboard()`), (2) Stub-Übererkennung (Prosa-„HOLD"/„Platzhalter" → nur noch Titel-Marker ⛔/Platzhalter/„bewusst NICHT ausgearbeitet").

**Ergebnis:** Selbstprüfung ✅ für alle 6 Boards; Spec-Validator + `schematic_netcheck.py` weiter grün (keine Regression). Der `.kicad_sch`-Zeichenschritt (Symbole/Vendor-Pinouts/wiring) ist explizit als nächster, KiCad-gebundener Schritt markiert.

**Nächster Schritt (Session 16+):** (a) KiCad-Zeichnung real starten (Mainboard/RF-Core, sobald KiCad/Vendor-Libs verfügbar) → G07 ERC, (b) `gen_kicad_project.py` optional um `.kicad_sch`-Netz-Scaffolds erweitern, **sobald** ein KiCad-Öffnen-Test möglich ist, (c) HOLDs mit Vendor-Daten schließen.

---

## 2026-09-01 — Session 14 (Cross-Sheet-Netznamen-Konsistenz + Checker-Tool)

**Motivation:** Mainboard-Sheet 17 fordert „exakt gespiegelte Netznamen zum Ziel-Board" — an mehreren Interfaces war das verletzt (uneinheitliche Schreibweisen würden KiCad-ERC bei G07 teuer machen). **22 Mirror-Lücken** gefunden und geschlossen.

**Umgesetzt:**
- **`hardware/INTERFACE_NETS.md`** (neu) — kanonisches Inter-Board-Netz-Dictionary (Single Source): PCIe/USB3/DSI/RF-Core-Bus/Antennen/Power je Connector mit **einem** kanonischen Namen; board-lokale Netze explizit ausgenommen.
- **`tools/schematic_netcheck.py`** (neu) — wiederverwendbarer Checker: prüft, ob jeder kanonische Netz-Stamm an **allen** beteiligten Boards vorkommt; Exit 1 bei Lücke (KiCad/CI-tauglich), konsolen-robust (UTF-8/ASCII).
- **Normalisierungen in den Sheets:** PCIe `PETx0/PERx0/PE_REFCLK/PERST/PCIE_RST_n/CLKREQ_n/WAKE_n` → `PCIE_TX/RX/REFCLK_P/N` + `PCIE_PERST_n/CLKREQ_n/WAKE_n` (Mainboard 12, M.2-Bridge, HyperRF 08); USB3 `USB3_SSTX/SSRX` → `USB3_M2_TX/RX` (M.2-Bridge); DSI `DSI_*` → `DSI0_*` (Mainboard README+03); Mainboard-Sheet 17 nennt jetzt die J_UI/J_DSI/J_RFCORE/J_ANT-Signale **beim kanonischen Namen** (`DSI0_*`, `TP_*`, `RFC_*`, `RF_KILL`/`TX_GATE_OK`, `ANT_1..4`).

**Ergebnis:** `schematic_netcheck.py` → **konsistent (25/25 Netz-Stämme über 6 Interfaces)**. Spec-Validator weiter Exit 0 (keine Regression). Keine Signal-Semantik geändert, nur Namen vereinheitlicht; alle HOLD/TBD/Forbidden-Disziplin unberührt.

**Nächster Schritt (Session 15+):** (a) KiCad-Zeichnung aus den nun namens-konsistenten Specs beginnen (Mainboard/RF-Core → G07 ERC), (b) `schematic_netcheck.py` bei Bedarf um weitere Interfaces (J_BAT/J_PWR-Detailnetze) erweitern, (c) HOLDs mit Vendor-Daten schließen.

---

## 2026-09-01 — Session 13 (HyperRF-Schaltplan — nach FPGA-Abhängigkeit partitioniert)

**Umgesetzt (`hardware/hyperrf/schematic/`):** README + 8 Sheets. Kern-Methode: das **HOLD-blockierte** Board (FPGA-MPN, G04) nach **Abhängigkeit partitioniert** — alles FPGA-Unabhängige ausgearbeitet, der FPGA selbst als ehrliches Platzhalter-Sheet (wie Mainboard 04/05).
- **Ausgearbeitet (nicht G04-abhängig):** 01 Power (`HYPERRF_AUX_5V` 5A → rauscharme Point-of-Load-Rails; FPGA-Rails HOLD) · 02 Takt/Referenz (10 MHz-Ref, **kohärente** LO/Sampling-Verteilung A↔B skew-gematcht, GNSS-PPS) · 03/04 LMS7002M A/B (4RX/4TX-Analog-Frontend, Balun/Matching→G09, LML-Digital-IF mit FPGA-Seite HOLD) · 05 High-Band-Conversion (3,8→6 GHz **TARGET** via Translation/Filter — kein 6-GHz-Nativ-Claim) · 06 Modul-Bays (5G RM530N-Klasse / NTN BG95-Klasse / LoRa-Sat LR1121-Klasse / GNSS NEO-F10N **L1/L5**) · 07 UWB (DW3000-Suffix **HOLD→G05**, kein SR150) + 60-GHz-Radar-Kachel (IWRL6432W-Klasse, separates metallfreies RF-Fenster, **kein** 60-GHz-SDR).
- **Platzhalter:** 08 FPGA — **⛔ HOLD→G04**, Rolle FIXED (PCIe-2.1-x1-EP + DSP/Channelization + LMS-LVDS + Timestamping), aber kein MPN/Pinout/Rails geraten; verlinkt auf `../fpga-selection/`.

**Damit Schaltplan-Design-Spec für ALLE 6 Boards angelegt** (Mainboard 18 · RF-Core 7 · UI-Carrier 4 · M.2-Bridge 2 · Antenna-Rail 1 · HyperRF 8). Forbidden-Claims durchgehend respektiert (kein 60-GHz-SDR, kein 6-GHz-nativ, kein Zynq-US+, kein SR150, GNSS nur L1/L5). Validator Exit 0.

**Nächster Schritt (Session 14+):** (a) KiCad-Zeichnung aus den fertigen Design-Specs beginnen (Mainboard/RF-Core zuerst → G07 ERC), (b) HOLDs mit Vendor-Daten schließen (G02/G03/G04/G05/G06), (c) Cross-Sheet-Konsistenz-Check (Netznamen board-übergreifend gespiegelt).

---

## 2026-09-01 — Session 12 (Board-Schaltpläne: UI-Carrier / M.2-Bridge / Antenna-Rail)

**Umgesetzt:** die drei **nicht-HOLD-blockierten** Board-Schaltpläne als Design-Spec (gleiche Methodik wie Mainboard/RF-Core) — damit ist der Schaltplan-Satz für **5 von 6 Boards** komplett (nur HyperRF bleibt FPGA-/HOLD-blockiert bis G04).
- **`hardware/ui-carrier/schematic/`** (218×100) — README + 4 Sheets. Kern-Designentscheidung: **Zwei-Domänen-Trennung** über einen `J_UI` — Anzeige/kap. Touch → RK3576 (DSI+I²C), physische Bedienung (Ring/D-Pad/5 Softkeys/Haptik/LEDs) → **RP2350** (funktioniert vor/ohne Linux, für Wake/Recovery/RF-Kill-Bestätigung). Sheet 01 DSI/Backlight · 02 Touch(GT911-Klasse, Adress-Strapping-Gotcha) · 03 Ring-AFE/D-Pad/Softkeys · 04 Haptik/Status-LED (`LED_RFKILL` aus RP2350, nicht Linux)/`J_UI`.
- **`hardware/m2-bridge/schematic/`** (30×52) — README + 2 Sheets. High-Speed-Brücke **PCIe 2.1 ×1 + USB3** (FIXED; **kein** Gen3 ×4). Sheet 01 PCIe/USB3-Diff-Paare + AC-Kopplung + RefClk · 02 Sideband(PERST/CLKREQ/WAKE) + Power inkl. `HYPERRF_AUX_5V`-Durchführung + TPs.
- **`hardware/antenna-rail/schematic/`** (150×18) — README + 1 Sheet. **Genau 4× SMA** (Forbidden „10+ SMA" respektiert), 50-Ω-Feeds, Pi/L-Matching- + SAW-Footprints (DNP bis G09), ESD je Port, Masse-Rückführung. Band-/Radio-Zuordnung je SMA = TBD 📄; Matching wird **auf realer HW getunt (G09)**, nie nur Simulation.

**Statusdisziplin durchgehend:** Busse/Signale FIXED aus Spec; alle Herstellerwerte (DSI-Timings, Touch-Register, Ring-AFE-MPN, AC-Cs, Steckertyp/-höhe, Matching-Werte) sichtbar `TBD 📄`/TARGET statt geraten. Kein Gate geschlossen. Validator Exit 0.

**Nächster Schritt (Session 13+):** (a) KiCad-Zeichnung aus den fertigen Mainboard-/RF-Core-Specs beginnen (Richtung G07 ERC), (b) HyperRF-Schaltplan-Sheets, soweit **nicht** FPGA-abhängig (LMS-Analog-Frontend, Power, Clock), vorbereiten, (c) auf Vendor-Rückmeldungen (PCBWay/Minewing) warten und HOLDs schließen.

---

## 2026-09-01 — Session 11 (Phase 8 / Gate G04 — HyperRF-FPGA Scored Candidate Matrix)

**Kontext-Fix zuerst:** Session 10 (RF-Core-Schaltplan) war committet (`a54e006`), aber **nicht** im Worklog dokumentiert — siehe Nachtrag unten (Session 10). Kein Code-Verlust, nur Protokoll nachgezogen.

**Umgesetzt (`hardware/hyperrf/fpga-selection/` angelegt):** das **Entscheidungs-Gerüst für G04** — bewusst kein MPN geraten (Forbidden-Claim „Zynq UltraScale+ unless explicitly frozen"; Spec `hyperrf.fpga` = HOLD).
- `README.md` — Zweck von G04, warum Scored-Matrix (nicht „aus altem Bild wählen"), Ablauf Knockout-Filter → gewichtete Bewertung → Freeze, Bezug zu Host-Limit (PCIe 2.1 x1) + RF-Kill-unabhängigkeit.
- `REQUIREMENTS.md` — aus Master-Spec **abgeleitete** Hard-/Soft-Anforderungen: PCIe-2.1-x1-Endpoint (Hard-IP bevorzugt), digitale IQ-Anbindung 2× LMS7002M (LML-LVDS, Lane-Zahl = TBD je Modus), DSP/BRAM für 4-Kanal-Dezimation/Channelization, Timestamping (10 MHz + PPS), **Power-Deckel** (Handheld/Dual-Blower), Package/Thermik, Verfügbarkeit/Lifecycle, Toolchain-Offenheit (Open-Source-Projekt).
- `SCORING_MODEL.md` — Knockout-Kriterien (K1–K5, sofortiges Aus) + 8 gewichtete Score-Achsen mit Rubrik 0–5 und **begründeter Default-Gewichtung** (Power/Thermik & Verfügbarkeit hoch für ein Batterie-Handheld; explizit als Owner-Entscheidungspunkt markiert, überschreibbar).
- `CANDIDATE_MATRIX.csv` — Matrix-Skelett: Kriterien × Kandidaten-**Familien** (Artix-/ECP5-/PolarFire-/Agilex-Klasse als Platzhalter-Spalten), **alle** herstellerspezifischen Zellen `TBD` — zu füllen aus Datenblatt/Verfügbarkeit, nicht geraten.
- `score.py` — liest die CSV, rechnet gewichtete Summe **nur** wenn Zellen belegt sind; bei `TBD` → Ausgabe „INSUFFICIENT DATA — HOLD" statt Scheinergebnis. Knockout-Spalten disqualifizieren hart.

**Statusdisziplin:** `hyperrf.fpga` bleibt **HOLD**; kein Gate geschlossen. Das Framework produziert die Entscheidung erst, wenn reale Werte eingetragen sind (Vendor-Docs / Verfügbarkeit / Power-Messung). Validator Exit 0.

**Owner-Entscheidung getroffen (2026-09-01):** Gewichtungs-Haltung **„Maximal hackbar"** gewählt → **S4 Toolchain-Offenheit dominant = 30** (Rest: S2=14, S8=12, S5=10, S3=10, S1=8, S6=8, S7=8; Summe 100). In `CANDIDATE_MATRIX.csv` + `SCORING_MODEL.md` eingetragen. Bewusst dokumentiertes Spannungsfeld: offenste Toolflows (Yosys/nextpnr) decken v. a. kleinere Familien ab, die bei K1 (PCIe-Hard-IP)/K3 (DSP/BRAM) eng werden können — die Knockout-Filter haben Vorrang vor dem S4-Gewicht.

**Nächster Schritt (Session 12+):** (a) Owner-Gewichtung bestätigen/anpassen → Kandidaten-Zellen mit Datenblattwerten füllen (sobald Vendor-Verfügbarkeit bekannt), (b) restliche Board-Schaltpläne als Design-Spec: UI-Carrier / M.2-Bridge / Antenna-Rail (nicht HOLD-blockiert), (c) KiCad-Zeichnung aus Mainboard-/RF-Core-Specs beginnen (Gate G07).

---

## 2026-08-28 — Session 10 (RF-Core-Schaltplan — 7 Sheets, Sicherheit zuerst) [Nachtrag]

> Nachträglich protokolliert in Session 11 — der Code war bereits committet (`a54e006`), der Worklog-Eintrag fehlte.

**Umgesetzt (`hardware/rf-core/schematic/` angelegt):** kompletter RF-Core-Schaltplan-Design-Spec-Satz (Board 92×66 mm), gleiche Methodik wie Mainboard.
- `README.md` — Sheet-Index (7), Host-Anbindung über `J_RFCORE`, Netz-Konventionen, **Sicherheits-Grundsatz: Sheet 01 zuerst** (RF-Kill gatet alle PA/TX-Enables).
- `sheet_01_supervisor_rfkill.md` — **sicherheitskritisch**: hardware-erzwungener TX-Disable-Pfad, Default nach Reset = Kill aktiv, softwareunabhängig (fail-safe), Autorität = RP2350; jedes Radio muss seinen PA/TX-Enable explizit über `PA_EN_<radio>` führen (ERC-Review-Punkt).
- `sheet_02_subghz.md` (CC1101 U500 + SX1262 U501) · `sheet_03_24ghz_zwave.md` (CC2652P7 U502 + EFR32ZG23 U503) · `sheet_04_nfc_lfrfid.md` (PN7160 U504 + LF-AFE U505) · `sheet_05_uhf_rain.md` (Impinj E710 U506) · `sheet_06_ir_1wire.md` (IR-TX/RX + 1-Wire) · `sheet_07_power_host_antennas.md` (Rails, SPI/UART, Antennen-Feeds, Testpoints).

**Statusdisziplin:** Kern-Radios FIXED; Z-Wave/LF-AFE/UHF/IR TARGET, regionale RF-Matching-Werte auf realer HW (G09), nie nur Simulation. Validator Exit 0.

---

## 2026-08-28 — Session 9 (Mainboard-Schaltplan — alle 18 Sheets als Design-Spec)

**Umgesetzt:** Der komplette Schaltplan-Design-Spec-Satz für das Mainboard (`hardware/mainboard/schematic/`) — 16 Entwurfs-Sheets + 2 ehrliche Platzhalter:
- **Fundament:** 01 Power-Tree · 02 RK806S-PMIC · 03 RK3576-Core.
- **Speicher (blockiert):** 04 LPDDR5 (G02) · 05 UFS (G03) — Platzhalter mit Anforderungen + „was zum Schließen gebraucht wird", nicht geroutet.
- **Boot/Debug:** 06 Recovery/SPI-NOR · 16 Debug/Recovery (RK3576-Maskrom + RP2350-BOOTSEL getrennt).
- **I/O:** 07 USB-C-PD/USB3/DP · 08 USB-Host · 09 HDMI/DP-Out · 10 Ethernet×2 · 11 Wi-Fi 6E/BT · 12 M.2/HyperRF (PCIe 2.1×1+USB3) · 13 RP2350-Link.
- **Peripherie:** 14 Audio · 15 Sensoren.
- **Integration:** 17 Connectors (Inter-Board) · 18 Testpoints (gestaffelter Bring-up).

**Disziplin durchgehend:** Struktur/Netze/ERC-Absicht vollständig; jeder Herstellerwert (Ball-/Rail-Map, DSI-/RGMII-Timings, Boot-Straps, Wi-Fi-Bus) bleibt sichtbar `TBD 📄`/HOLD statt geraten. Forbidden-Claims respektiert (kein Gen3×4, kein 6-Layer, UFS/LPDDR5 nicht produktionsbestätigt).

**Ergebnis:** Schaltplan-Design-Spec strukturell **vollständig** → bereit für KiCad-Zeichnung + Minewing-ERC-Review (Gate G07). Vor „ERC clean": bestätigte 📄/HOLD-Werte einsetzen, 04/05 nach G02/G03 vervollständigen.

**Nächster Schritt (Session 10+):** je nach Owner-Wunsch — (a) KiCad-Zeichnung aus den Design-Specs beginnen, (b) RF-Core-/HyperRF-Schaltpläne analog aufbauen, (c) G04 FPGA-Scored-Candidate-Matrix, (d) auf Vendor-Rückmeldungen (PCBWay/Minewing) warten und HOLDs schließen.

---

## 2026-08-28 — Session 8 (Phase 5 Kickoff — Mainboard-Schaltplan)

**Umgesetzt (`hardware/mainboard/schematic/` angelegt):**
- `README.md` — Schaltplan-Methodik (reviewbare Design-Spec je Sheet statt sofort KiCad → SoT-Disziplin bleibt), **18-Sheet-Index** mit Status, **Netz-/Power-Namenskonvention** (aus POWER_TREE.csv), Impedanz-/SI-Ziele (50 Ω SE / 90 Ω / 100 Ω diff), ERC-Absicht (G07). Sheets 04 (LPDDR5) + 05 (UFS) bewusst **⛔ blockiert** bis G02/G03.
- `sheet_01_power_tree.md` — erstes fundamentales Sheet: Blockfluss (USB-C-PD → Charger → VSYS → Rails), Netz-Tabelle, Kern-Bauteile (TPS25751A/BQ25792/BQ28Z620/RK806S), kritische Notizen (Sequencing, +3V3_AON-immer-an für RP2350, IR-Drop 10 A, RF-Kill-Bezug), ERC-Absicht, HOLD (RK806S-Rail-Map).

**Methodik-Entscheidung:** Schaltplan als versionierbare Design-Spezifikation (diff-bar, HOLD sichtbar); KiCad-Zeichnung wird daraus deterministisch. Basis für Minewing-ERC-Review (G07).

**Nächster Schritt (Session 9+):** restliche Sheets sheet-für-sheet — als Nächstes Sheet 03 (RK3576-Core) + Sheet 02 (RK806S-PMIC, Rail-Map-Anforderungen), dann RP2350-Link/USB-C-PD/Ethernet/M.2 usw. Sheets 04/05 bleiben Platzhalter bis G02/G03.

---

## 2026-08-28 — Session 7 (Fertigungs-Handoff-Paket — `manufacturing/`)

**Owner-Direktive:** Produkt fertigungsbereit machen, um es an die **zwei Firmen** (PCBWay + Minewing) weiterzugeben. Rückfrage geklärt: **„Paket + Schaltplan selbst bauen"**, **EVT 1–3 Einheiten**, Ownership Hybrid (Annahme).

**Ehrliche Einordnung (dem Owner offengelegt):** Finale Gerber/CPL sind **nicht** seriös erzeugbar — G02(LPDDR5)/G03(UFS)/G04(FPGA)/G06(Stackup) sind HOLD und werden **genau von den zwei Firmen** geschlossen. Der korrekte Übergabestand ist ein **DFM-/RFQ- + Engineering-Handoff-Paket**, nicht geratene Gerber.

**Umgesetzt (`manufacturing/` angelegt, vorher leer):**
- `README.md` — Handoff-Hub + EVT-Umfang (1–3) + Ownership + „was NICHT hier ist".
- `MANUFACTURING_READINESS_REVIEW.md` — Gate-für-Gate-Reifegrad-Scorecard (🟢/🟡/🔴), wer schließt was, Forbidden-Claims-Guard.
- `BOARD_SET.md` — 6-Board-Set (Mainboard 210×92/12L-HDI, HyperRF 136×72, RF-Core 92×66, UI-Carrier 218×100, M.2-Bridge 30×52, Antenna-Rail 150×18), Verbindungen, kritische Layout-Themen.
- `DFM_RFQ_PCBWAY.md` — sende-fertige PCB-/DFM-RFQ mit **präzisen Stackup-/Impedanz-/Microvia-Fragen** (G06).
- `ENGINEERING_HANDOFF_MINEWING.md` — JDM-Scope + **Sourcing-Aufträge für die HOLD-Teile** (G02/G03/G04/G05/G11) + Review-Umfang.
- `BOM_EVT.csv` — vollständige Fertigungs-BOM (45 Positionen) mit Status + **Sourcing_Owner + Gate** je Position.

**Validator:** Exit 0.

**Nächster Schritt (Session 8):** Phase 5 starten — Produktions-Schaltplan (`hardware/schematic/`): Sheet-Plan (18 Sheets) + Netz-/Power-Definitionen, sheet-für-sheet als reviewbare Design-Spezifikation (Basis für KiCad-Zeichnung + Minewing-ERC-Review, Gate G07).

---

## 2026-08-28 — Session 6 (Software-/UI-Ebene — ONE-X-Launcher-Konzept)

**Umgesetzt (`linux/ui/` angelegt) — schließt die 4. Design-Ebene:**
- `linux/ui/mockup_home.svg` — Launcher-Home-Mockup in nativer Landscape-Auflösung (1280×720). Vier farbkodierte Funkdomänen (identische Farben wie `architecture.svg`), RF-Kill-Status prominent in der Statusleiste (rot = aktiv, aus RP2350-Heartbeat), HOLD/TARGET-Reife als Micro-Badge (FPGA G04, 5G/NTN, Kern FIXED, RP2350-Telemetrie), 5 Softkeys + Touch-Ring/D-Pad-Hinweise. Via Edge-Headless gerendert/verifiziert.
- `linux/ui/README.md` — Leitidee (UI spiegelt Hardware-Realität + Reife), Eingabemodell (Touch / Touch-Ring / D-Pad / 5 Softkeys, blindbedienbar), Informationsarchitektur, **Firmware-Anbindung** (UI = Consumer der RP2350-Telemetrie über ONE-X-Link; RF-Kill-Freigabe = Policy-Anfrage, kein Toggle), Umsetzungs-Skizze (Wayland+SW-Rotation, App-Framework TARGET).

**Statusdisziplin:** Explizit „Konzept, keine Implementierung bis G01 real läuft". App-Framework = TARGET (Auswahl nach Perf-Messung).

**Damit alle 4 Owner-Design-Ebenen adressiert:** Visual/Marke ✅ · Industrie-Design ✅ · Engineering-Architektur (Diagramm+G01+Phase2) ✅ · Software/UI ✅.

**Nächster Schritt (Session 7):** Engineering-Tiefe — Phase 3 Vendor-Docs/Core-BOM-Freeze vorbereiten (G02 LPDDR5-Topologie / G03 UFS-MPN: Anforderungs-/Recherche-Templates, ohne zu raten), oder G04 FPGA-Scored-Candidate-Matrix-Gerüst.

---

## 2026-08-28 — Session 5 (Industrie-Design — CadQuery-Gehäuse spec-getrieben)

**Befund:** `mechanical/generate_enclosure.py` war bereits im **korrekten Querformat** und maßlich spec-konform (230×110×64, Fenster 112,5×64,5, Ring Ø40, Boards 210×92/136×72/92×66, Rail 150×18, Akku 2S2P/4×21700) — anders als das alte Front-SVG. Fehlend war **Spec-Rückverfolgbarkeit + HOLD-Disziplin**, plus ein Export-Bug.

**Umgesetzt (Geometrie unangetastet, nur nachvollziehbar/ehrlich gemacht):**
- Modul-Docstring mit Provenienz (Master-Spec = SoT), Querformat-Formsprache, Status-Legende.
- Jeder Maß-Parameter mit Spec-Key + Status getaggt (FIXED/TARGET/HOLD inline).
- **HOLD-Banner** an Thermik (Spreader/Fans → Gate G10) und Akku-Pack-Compliance (→ Gate G11): explizit „Kollisions-/Bauraum-Referenz, nicht validiert".
- **Bugfix:** `fan2` wurde erzeugt + in Assembly genutzt, aber nie als Teil exportiert → jetzt beide Blower exportiert (`fan_30x30x5_dummy_1/_2`).
- Bounding-Box-Plausibilitätsprüfung + HOLD-Erinnerung am Skriptende (Warnung bei Envelope-Überschreitung).
- `mechanical/README.md` neu (Erzeugen, Formsprache, Status-Tabelle).

**Validierung:** `python -m py_compile` OK (CadQuery hier nicht installiert; Laufzeit-Erzeugung nicht getestet — Geometrie-Logik unverändert). Spec-Validator Exit 0.

**Nächster Schritt (Session 6):** Software-/UI-Ebene — ONE-X-Launcher-/UI-Konzept für 5″-Touch (Landscape); danach ggf. Phase 3 Vendor-Docs/Core-BOM-Freeze (G02/G03) vorbereiten.

---

## 2026-08-28 — Session 4 (Phase 2 — RP2350B System-Manager-Architektur)

**Umgesetzt (`firmware/rp2350/` angelegt, vorher leer):**
- `README.md` — Rolle (FIXED: Always-On, power/wake/buttons/sensors/haptik/fans/status/debug, **kein** Linux-Framebuffer), Nicht-Ziele, Statusdisziplin (alle Pins HOLD → pin-unabhängige Verträge).
- `ARCHITECTURE.md` — kooperatives tickbasiertes Ausführungsmodell (Core0-Superloop, Core1 für Echtzeit/RF-Kill-Latch), 12-Modul-Landkarte nach Sicherheitspriorität, System-Zustandsmaschine (OFF/BOOT/RUN/SUSPEND/SHUTDOWN/FAULT), Watchdog-Politik, **RF-Kill-Grundsatz** (HW-erzwungen, Default nach Boot/Reset/Fault = Kill aktiv).
- `PROTOCOL.md` — ONE-X-Link v1: Framing (SOF `0xA5 0x5A`, VER/TYPE/SEQ/LEN/CRC-16-CCITT), Zuverlässigkeit (ACK/NACK+SEQ), vollständiges Nachrichten-Set (Host→Mgr Kommandos, Mgr→Host Events), sicherheitskritische RF-Kill-Semantik (Manager = Autorität, Freigabe nur mit Regulierungsprofil+Token).
- `include/onex_proto.h` + `include/onex_modules.h` — kompilierbare C-Verträge (Frame/Enums/CRC-Proto; Modul-Interface init/tick/event). **gcc-Syntaxcheck OK** (`-std=c11 -Wall -Wextra`).

**Bewusst pin-unabhängig:** keine GPIO-/Bus-Zuordnungen erfunden (HOLD bis Mainboard-Schaltplan, Gate G07); HAL-Schicht folgt in Phase 5.

**Validator:** Exit 0 (nur Dateien hinzugefügt).

**Nächster Schritt (Session 5):** Industrie-Design vertiefen (`mechanical/generate_enclosure.py` an neue Front-Geometrie/Formsprache angleichen) **oder** Software-/UI-Ebene (ONE-X-Launcher-Konzept für 5″-Touch, Landscape).

---

## 2026-08-28 — Session 3 (Phase 1 / G01 — Linux-Display-Bringup-Skelett)

**Umgesetzt (`linux/` angelegt, vorher leer):**
- `linux/README.md` — Linux-Plattform-Strategie + G01-Scope; klare FIXED/TARGET/HOLD-Tabellen (Display-Fähigkeit FIXED, Treiber/Bringup HOLD via `display.driver_gate`).
- `linux/BRINGUP_CHECKLIST_G01.md` — 8-stufige Bringup-Checkliste (Panel-Power → DSI/PHY → DT-Overlay → DRM/KMS-Modeset → SW-Rotation Landscape → Touch-I²C → Suspend/Resume → Abschluss). Jede Stufe mit ✅-Kriterium; G01 gilt erst bei HW-Nachweis geschlossen.
- `linux/device-tree/rk3576-one-x-panel5.dtso` — Device-Tree-Overlay-**Skelett** (Panel ILI9881C-Klasse + Touch GT911-Klasse). Alle unsicheren Stellen als `VERIFY` (Node-Labels vs. RK3576-BSP) bzw. `HOLD 📄` (Pins, DSI-Timings, Init-Sequenz aus Datenblatt) markiert. FIXED-Werte (720×1280, 4 Lanes, Touch-I²C) gesetzt.
- `linux/device-tree/Makefile` — cpp+dtc-Build (KDIR auf RK3576-Kernelbaum anpassen).
- `linux/panel/PANEL_CANDIDATE.md` — Panel-/Touch-Datenpunkte; benötigte Datenblatt-Werte als TBD/HOLD gelistet (nicht geraten).

**Bewusst NICHT getan:** Gate-Status **nicht** geändert — G01 bleibt „offen", `display.driver_gate` bleibt HOLD (kein HW-Nachweis vorhanden). Keine DSI-Timings/Node-Labels erfunden.

**Validator:** Exit 0 (nur Dateien hinzugefügt, keine Spec-Änderung).

**Nächster Schritt (Session 4):** Wahlweise (a) Phase 2 `firmware/rp2350/`-Modularchitektur (power/wake/buttons/touch_ring/haptik/sensors/fan/battery/watchdog/rk3576_link/recovery/rf_kill/protocol), oder (b) Industrie-Design vertiefen: `mechanical/generate_enclosure.py` (CadQuery-Gehäuse) an neue Formsprache/Front-Geometrie angleichen, oder (c) Software-/UI-Ebene: ONE-X-Launcher-Konzept.

---

## 2026-08-28 — Session 2 (Rework-Direktive + Design-Neuaufbau, Teil 1)

**Neue Owner-Direktive (2026-08-28):** Das Projekt wird **komplett neu umgesetzt** — „alles überarbeiten, auch designtechnisch". Vier Design-Ebenen betroffen (Industrie-/Produktdesign, Visual-/Marken-Auftritt, Engineering-Architektur, Software-/UI). Vorgehen: **sofort autonom bauen**. **Design-Orientierung: letzte ChatGPT-Vorlagen** (`ONE-X_EVT6_VERIFIED_GRAPHICS_PACKAGE`, `…MASTER_ALL_FILES…2026-08-27`). **Alle KiCad/PCB-Dateien = Vorerzeugnisse** (Drafts), nicht als final behandeln. HOLD-Disziplin bleibt ([[feedback-chatgpt-data-rework]], [[feedback-no-unconfirmed-partners]]).

**ChatGPT-Design-Vorlagen gesichtet (verbindliche Formsprache):** Querformat-Handheld, Touch-Ring Ø40 links · 5″-Display mittig (Bezel) · D-Pad rechts · 5 Softkeys unten · 4× SMA oben. Interface-Architektur = RK3576-Hub mit sichtbaren HOLD-Badges an LPDDR5/UFS.

**Umgesetzt:**
- **`docs/graphics/front_layout.svg` komplett neu** — vorher inkonsistentes **Hochformat**, jetzt maßstäbliches **Querformat** (1 mm = 8 px), exakt in ChatGPT-EVT6-Formsprache. Alle Maße FIXED aus Master-Spec (Envelope 230×110×64, Recess 138×81, Fenster 112,5×64,5, Ring Ø40, D-Pad 34×34, 5 Softkeys, 4× SMA). Titelblock + Bemaßung (230/110 mm) + Provenienz + FIXED/HOLD-Legende.
- **`docs/graphics/architecture.svg` komplett neu** — professionelles System-Diagramm, 4 farbkodierte Domänen (Compute/Control/HyperRF/RF-Core), HOLD an LPDDR5 (Gate G02) und UFS (Gate G03) sichtbar gebadged, HyperRF-FPGA→G04-HOLD markiert. Host-I/O-Subpanel, Bus-Labels, Legende, Provenienz.
- **`docs/graphics/rf_coverage.svg` komplett neu** — professionelles Spektrum (log-Achse 100 kHz–100 GHz), Bänder nach **Reifegrad-Status** gefärbt (FIXED/VALIDATED_ARCH/TARGET/HOLD) statt nach Optik, nach Domänen gruppiert (HyperRF/RF-Core/Spezial), inkl. **Forbidden-Claim-Guard-Box** (kein 60-GHz-SDR, UWB-Suffix HOLD/G05, GNSS nur L1/L5, FPGA HOLD/G04). Jedes Band mit MPN-„-Klasse"-Bezeichnung.
- Alle drei Grafiken via Edge-Headless gerendert und visuell verifiziert.

**Sponsor-Compliance (Owner-Freigabe „De-Claim + entfernen"):** `providers/` aus Public-Repo entfernt (Unterlagen privat unter `C:\Data\KI\_private_one-x\providers\`); „Sponsor aktiv"→„Outreach/keine Zusage" in README/Präsentation/CLAUDE/ROADMAP. Grund: Validator scannt NUR Spec-Claims, nicht den Doku-Fließtext.

**Validator:** `python tools/spec_validator.py` → Exit 0 (FIXED=47, HOLD=8, TARGET=17; keine verbotenen Claims).

- **`presentation/index.html` synchronisiert** — drei veraltete Inline-SVGs (u.a. das falsche Hochformat-Frontlayout + alte RF-Grafik) durch externe `<img>`-Referenzen auf die neuen `docs/graphics/*.svg` ersetzt → eine Quelle pro Grafik, Präsentation bleibt automatisch synchron. `.fig img`-CSS ergänzt, `.tall` beim jetzt querformatigen Frontlayout entfernt. Ganze Seite via Edge-Headless gerendert/verifiziert (alle 3 Diagramme laden, Layout konsistent, Partner-Abschnitt de-claimed).
  - Hinweis: Bei späterer Artifact-Veröffentlichung (strikte CSP, keine externen Refs) müssten die SVGs wieder inline oder als data:-URI eingebettet werden. Für lokal/Repo/Pages ist die `<img>`-Referenz korrekt.

**Nächster Schritt (Session 3):** Phase 1/G01 `linux/`-Display-Bringup-Skelett beginnen (Device-Tree-Overlay-Struktur + DSI-Panel-Bringup-Checkliste RK3576 + 5″ 720×1280, Touch-I²C, Suspend/Resume); danach `firmware/rp2350/`-Modularchitektur (Phase 2).

**Offene HOLDs (unverändert):** LPDDR5-Topologie (G02), UFS-MPN (G03), FPGA-MPN (G04), DW3000-Suffix (G05), HDI-Stackup (G06), finale Thermik (G10), Akku-Compliance (G11).

---

## 2026-08-27 — Session 1 (Projektgründung)
**Umgesetzt (Phase 0 ✅):**
- Repo `flipper/g4meover-one-x` angelegt (Public Open-Source, GitHub G4MEOVER18).
- Rebranding EVT6 → **G4MEOVER ONE-X**; Master-Spec als Single Source of Truth importiert.
- `tools/spec_validator.py` (FIXED/TARGET/HOLD-Auswertung + forbidden-claim-Scan + derived docs).
- Flaggschiff-README, CLAUDE.md, ARCHITECTURE, ROADMAP (G01–G11), COMPARISON (vs. Flipper One), LICENSE (CERN-OHL-S / MIT / CC-BY-SA).
- Sponsor-Pakete PCBWay + Minewing (Mail-Vorlagen + Datenpakete + Versand-Anleitung).
- Konzept-Präsentation (Artifact) + Konzept-Grafiken (SVG).
- Branding-Tokens/Logo.

**Nächster Schritt (Session 2):** Phase 1 / G01 vorbereiten — Display-Bringup-Plan:
`linux/` Device-Tree-Skelett + DSI-Panel-Bringup-Checkliste für RK3576 + 5″ 720×1280,
sowie `firmware/rp2350/` Modul-/Protokoll-Architektur (Phase 2) als parallelen Strang.

**Offene HOLDs (unverändert, nicht raten):** LPDDR5-Topologie, UFS-MPN, FPGA-MPN, DW3000-Suffix, HDI-Stackup, finale Thermik, Akku-Compliance.
