/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X Superloop-Scheduler — faehrt die Modul-Tabelle aus onex_modules.h.
 *
 * Referenz: firmware/rp2350/ARCHITECTURE.md 1
 *
 *   Core 0 (Superloop, ~1 kHz Basistakt):
 *     for each module in ORDER: module.tick(now_us)
 *     service rk3576_link (RX/TX)
 *     kick hardware watchdog        // nur wenn alle Pflichtmodule OK
 *
 * Reihenfolge der Tabelle = Sicherheitsprioritaet (onex_modules.h): rf_kill,
 * power und watchdog laufen VOR allem anderen. Das ist keine Optimierung,
 * sondern Teil der Sicherheitsauslegung -- ein spaeter laufendes Modul darf
 * nie zwischen einen Sicherheitszustand und seine Wirkung geraten.
 *
 * WAS DIESER SCHEDULER NICHT KANN -- bewusst benannt:
 * Er ist kooperativ. Ein Modul, das in tick() blockiert, kann von ihm NICHT
 * unterbrochen werden; er kann die Ueberschreitung nur erkennen und melden.
 * Die tatsaechliche Rettung ist der Hardware-Watchdog: bleibt der Superloop
 * stehen, wird nicht mehr gekickt, der Chip resettet, und die Firmware
 * startet im sicheren Default (RF-Kill an, Rails aus). Wer von einem
 * kooperativen Scheduler mehr verspricht, verkauft eine Sicherheit, die es
 * nicht gibt.
 *
 * Pin-/HAL-frei: Zeit kommt als Parameter herein, der Watchdog-Kick geht als
 * Erlaubnis hinaus. Alle Pin-Zuordnungen bleiben HOLD bis Gate G07.
 */
#ifndef ONEX_SCHED_H
#define ONEX_SCHED_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "onex_modules.h"
#include "onex_watchdog.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifndef ONEX_TICK_BUDGET_US
/* Zeitbudget je Modul-tick (onex_modules.h: "MUSS < 200 us bleiben"). */
#define ONEX_TICK_BUDGET_US 200u
#endif

#ifndef ONEX_SCHED_EVENT_QUEUE
/* Interne Event-Warteschlange. Klein und fest -- kein malloc im Superloop. */
#define ONEX_SCHED_EVENT_QUEUE 16u
#endif

/* Diagnose-Zaehler (Bringup, Feldanalyse). */
typedef struct {
    uint32_t loops;
    uint32_t module_ticks;
    uint32_t budget_overruns;    /* tick > ONEX_TICK_BUDGET_US */
    uint32_t init_failures;
    uint32_t events_posted;
    uint32_t events_dropped;     /* Warteschlange war voll */
    uint32_t kicks;
    uint32_t kicks_withheld;
} onex_sched_stats_t;

typedef struct {
    /* true = der Aufrufer darf den HW-Watchdog jetzt fuettern. */
    bool     kick;
    /* Modul, das den Kick verhindert hat (ONEX_MOD_COUNT = keins). */
    uint8_t  culprit;
    /* Ein Modul hat sein Zeitbudget in diesem Durchlauf ueberschritten. */
    bool     budget_exceeded;
    uint8_t  slow_module;
} onex_sched_output_t;

typedef struct {
    const onex_module_t *const *modules;   /* Tabelle in Prioritaetsreihenfolge */
    unsigned                    count;

    /* Deaktiviert, weil init() false lieferte -- wird nicht mehr getickt. */
    bool     disabled[ONEX_MOD_COUNT];
    /* Zuletzt gemeldete Gesundheit je Modul. */
    uint8_t  health[ONEX_MOD_COUNT];
    /* Laufzeit des letzten ticks in us (Diagnose). */
    uint32_t last_us[ONEX_MOD_COUNT];

    onex_event_t queue[ONEX_SCHED_EVENT_QUEUE];
    unsigned     q_len;

    onex_watchdog_t  *wd;         /* darf NULL sein */
    uint32_t          budget_us;
    bool              initialized;

    onex_sched_stats_t stats;
} onex_sched_t;

/*
 * Registriert die Modul-Tabelle und ruft jedes init() genau einmal.
 *
 * init() == false deaktiviert das Modul dauerhaft. Ist es safety-critical,
 * bleibt es zusaetzlich als FAULT gemeldet -- ein Sicherheitsmodul, das nicht
 * startet, darf nicht einfach fehlen, sonst kickt der Watchdog fuer ein
 * System, dessen Schutz gar nicht laeuft.
 *
 * modules darf Eintraege mit NULL enthalten (noch nicht implementierte
 * Module); die werden uebersprungen und wie "nicht vorhanden" behandelt.
 *
 * Braucht keine Zeit: die Meldung deaktivierter Sicherheitsmodule an den
 * watchdog passiert in run_once() -- dort, wo der watchdog auch ausgewertet
 * wird. Eine zweite Meldestelle waere eine Kopie derselben Regel.
 */
void onex_sched_init(onex_sched_t *s,
                     const onex_module_t *const *modules, unsigned count,
                     onex_watchdog_t *wd);

/* Zeitbudget je tick ueberschreiben (Tests, Abstimmung). */
void onex_sched_set_budget(onex_sched_t *s, uint32_t budget_us);

/*
 * Ein Superloop-Durchlauf:
 *   1. anstehende Events zustellen (Schnappschuss, siehe unten)
 *   2. alle aktiven Module in Tabellenreihenfolge ticken, Laufzeit messen
 *   3. Gesundheit an den watchdog melden
 *   4. Kick-Erlaubnis ermitteln
 *
 * now_us muss monoton steigen. Die Laufzeitmessung braucht eine Zeitquelle,
 * die WAEHREND des ticks weiterlaeuft -- sie wird ueber elapsed_us gestellt.
 * Ist elapsed_us NULL, entfaellt die Budget-Ueberwachung (und wird auch nicht
 * behauptet: budget_exceeded bleibt dann false).
 */
void onex_sched_run_once(onex_sched_t *s, uint64_t now_us,
                         uint64_t (*elapsed_us)(void),
                         onex_sched_output_t *out);

/*
 * Event in die Warteschlange stellen. Zustellung erfolgt im NAECHSTEN
 * Durchlauf -- nie rekursiv aus einem event()-Handler heraus. Damit kann ein
 * Handler, der selbst postet, keine unbegrenzte Rekursion ausloesen.
 *
 * Ist die Warteschlange voll, wird das NEUE Event verworfen und gezaehlt:
 * bereits angenommene Events werden garantiert zugestellt, die Reihenfolge
 * bleibt erhalten, und der Verlust ist sichtbar statt still.
 */
void onex_sched_post(onex_sched_t *s, const onex_event_t *ev);

bool onex_sched_is_disabled(const onex_sched_t *s, onex_module_id_t id);
const onex_sched_stats_t *onex_sched_stats(const onex_sched_t *s);

#ifdef __cplusplus
}
#endif
#endif /* ONEX_SCHED_H */
