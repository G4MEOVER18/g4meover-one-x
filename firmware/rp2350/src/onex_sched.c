/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X Superloop-Scheduler. Vertrag: ../include/onex_sched.h
 *
 * Leitlinien:
 *  1. Tabellenreihenfolge ist Sicherheitsreihenfolge -- nie umsortieren,
 *     nie "das schnelle Modul zuerst".
 *  2. Ein fehlendes oder nicht gestartetes Sicherheitsmodul ist ein Fehler,
 *     kein leerer Platz.
 *  3. Events werden aus einem Schnappschuss zugestellt: was ein Handler
 *     postet, laeuft im naechsten Durchlauf -- keine Rekursion im Superloop.
 */
#include "onex_sched.h"

/*
 * Aktiver Scheduler fuer onex_post_event() aus onex_modules.h.
 * Der Vertrag dort ist parameterlos, also braucht die Zustellung einen
 * Anker. Auf dem Geraet gibt es genau einen Superloop -- im Test wird der
 * Anker mit jedem onex_sched_init() neu gesetzt.
 */
static onex_sched_t *g_active;

static bool slot_usable(const onex_sched_t *s, unsigned i)
{
    return s->modules[i] != NULL && !s->disabled[i];
}

void onex_sched_init(onex_sched_t *s,
                     const onex_module_t *const *modules, unsigned count,
                     onex_watchdog_t *wd)
{
    if (s == NULL || modules == NULL) {
        return;
    }
    if (count > (unsigned)ONEX_MOD_COUNT) {
        count = (unsigned)ONEX_MOD_COUNT;
    }

    s->modules = modules;
    s->count = count;
    s->wd = wd;
    s->budget_us = ONEX_TICK_BUDGET_US;
    s->q_len = 0u;
    s->initialized = true;

    for (unsigned i = 0; i < (unsigned)ONEX_MOD_COUNT; ++i) {
        s->disabled[i] = true;                       /* bis init() zustimmt */
        s->health[i] = (uint8_t)ONEX_HEALTH_FAULT;
        s->last_us[i] = 0u;
    }
    s->stats.loops = 0u;
    s->stats.module_ticks = 0u;
    s->stats.budget_overruns = 0u;
    s->stats.init_failures = 0u;
    s->stats.events_posted = 0u;
    s->stats.events_dropped = 0u;
    s->stats.kicks = 0u;
    s->stats.kicks_withheld = 0u;

    g_active = s;

    for (unsigned i = 0; i < count; ++i) {
        const onex_module_t *m = modules[i];
        if (m == NULL) {
            continue;   /* Platzhalter -- Modul existiert noch nicht */
        }
        const bool ok = (m->init == NULL) || m->init();
        s->disabled[i] = !ok;
        if (ok) {
            /*
             * Frisch initialisiert heisst noch nicht gesund: erst der erste
             * tick liefert eine echte Meldung. Bis dahin OK anzunehmen waere
             * genau die optimistische Annahme, die der watchdog vermeidet.
             */
            s->health[i] = (uint8_t)ONEX_HEALTH_OK;
        } else {
            s->stats.init_failures++;
            /*
             * Ein nicht gestartetes Sicherheitsmodul bleibt sichtbar defekt.
             * Die Meldung an den watchdog passiert bewusst NICHT hier: die
             * Schleife in run_once() meldet jedes deaktivierte kritische
             * Modul in jedem Durchlauf, und der watchdog wird ohnehin nur
             * dort ausgewertet. Eine zweite Meldestelle waere eine Kopie
             * derselben Regel -- und Kopien driften auseinander.
             */
            s->health[i] = (uint8_t)ONEX_HEALTH_FAULT;
        }
    }
}

void onex_sched_set_budget(onex_sched_t *s, uint32_t budget_us)
{
    if (s != NULL) {
        s->budget_us = budget_us;
    }
}

void onex_sched_post(onex_sched_t *s, const onex_event_t *ev)
{
    if (s == NULL || ev == NULL) {
        return;
    }
    s->stats.events_posted++;
    if (s->q_len >= ONEX_SCHED_EVENT_QUEUE) {
        /* Neuestes verwerfen: bereits angenommene Events werden garantiert
         * zugestellt und behalten ihre Reihenfolge. Verlust bleibt sichtbar. */
        s->stats.events_dropped++;
        return;
    }
    s->queue[s->q_len++] = *ev;
}

/* Vertrag aus onex_modules.h -- leitet auf den aktiven Scheduler. */
void onex_post_event(const onex_event_t *ev)
{
    onex_sched_post(g_active, ev);
}

/* Events aus einem Schnappschuss zustellen (Regel 3). */
static void deliver_events(onex_sched_t *s)
{
    if (s->q_len == 0u) {
        return;
    }

    onex_event_t snapshot[ONEX_SCHED_EVENT_QUEUE];
    const unsigned n = s->q_len;
    for (unsigned i = 0; i < n; ++i) {
        snapshot[i] = s->queue[i];
    }
    /*
     * Warteschlange VOR der Zustellung leeren: postet ein Handler etwas,
     * landet es in der jetzt leeren Schlange und wird im naechsten Durchlauf
     * zugestellt -- nicht in dieser Runde. Damit ist die Zustellung endlich,
     * egal was die Handler tun.
     */
    s->q_len = 0u;

    for (unsigned e = 0; e < n; ++e) {
        for (unsigned i = 0; i < s->count; ++i) {
            if (!slot_usable(s, i)) {
                continue;
            }
            const onex_module_t *m = s->modules[i];
            if (m->event != NULL) {
                m->event(&snapshot[e]);
            }
        }
    }
}

void onex_sched_run_once(onex_sched_t *s, uint64_t now_us,
                         uint64_t (*elapsed_us)(void),
                         onex_sched_output_t *out)
{
    if (out == NULL) {
        return;
    }
    out->kick = false;
    out->culprit = (uint8_t)ONEX_MOD_COUNT;
    out->budget_exceeded = false;
    out->slow_module = (uint8_t)ONEX_MOD_COUNT;

    if (s == NULL || !s->initialized) {
        return;   /* ohne Scheduler keine Kick-Erlaubnis (fail-safe) */
    }

    s->stats.loops++;
    deliver_events(s);

    const uint32_t now_ms = (uint32_t)(now_us / 1000u);

    /* Regel 1: strikt in Tabellenreihenfolge. */
    for (unsigned i = 0; i < s->count; ++i) {
        if (!slot_usable(s, i)) {
            continue;
        }
        const onex_module_t *m = s->modules[i];
        if (m->tick == NULL) {
            continue;
        }

        const uint64_t t0 = (elapsed_us != NULL) ? elapsed_us() : 0u;
        const onex_health_t h = m->tick(now_us);
        s->stats.module_ticks++;

        if (elapsed_us != NULL) {
            const uint64_t dt = elapsed_us() - t0;
            s->last_us[i] = (dt > 0xFFFFFFFFu) ? 0xFFFFFFFFu : (uint32_t)dt;
            if (s->last_us[i] > s->budget_us) {
                /*
                 * Erkennen, nicht verhindern: ein kooperativer Scheduler kann
                 * einen laufenden tick nicht abbrechen. Die Ueberschreitung
                 * wird gemeldet; die Rettung bei echtem Stillstand ist der
                 * HW-Watchdog.
                 */
                s->stats.budget_overruns++;
                if (!out->budget_exceeded) {
                    out->budget_exceeded = true;
                    out->slow_module = (uint8_t)m->id;
                }
            }
        }

        s->health[i] = (uint8_t)h;
        if (s->wd != NULL && m->is_safety_critical) {
            onex_watchdog_report(s->wd, m->id, h, now_ms);
        }
    }

    /*
     * Ein safety-critical Modul, das in der Tabelle fehlt (NULL) oder
     * deaktiviert wurde, darf nicht unbemerkt bleiben -- sonst haette der
     * watchdog nie etwas von ihm gehoert und die Startkarenz liefe ins Leere,
     * waehrend das System ohne diesen Schutz laeuft.
     */
    for (unsigned i = 0; i < s->count; ++i) {
        const onex_module_t *m = s->modules[i];
        if (m == NULL) {
            continue;
        }
        if (m->is_safety_critical && s->disabled[i] && s->wd != NULL) {
            onex_watchdog_report(s->wd, m->id, ONEX_HEALTH_FAULT, now_ms);
        }
    }

    if (s->wd != NULL) {
        onex_watchdog_output_t wo;
        onex_watchdog_tick(s->wd, now_ms, &wo);
        out->kick = wo.kick;
        out->culprit = wo.culprit;
    } else {
        /* Ohne watchdog-Modul gibt es niemanden, der die Erlaubnis pruefen
         * koennte -- also auch keine Erlaubnis. */
        out->kick = false;
    }

    if (out->kick) {
        s->stats.kicks++;
    } else {
        s->stats.kicks_withheld++;
    }
}

bool onex_sched_is_disabled(const onex_sched_t *s, onex_module_id_t id)
{
    if (s == NULL || (unsigned)id >= (unsigned)ONEX_MOD_COUNT) {
        return true;
    }
    return s->disabled[(unsigned)id];
}

const onex_sched_stats_t *onex_sched_stats(const onex_sched_t *s)
{
    return (s == NULL) ? NULL : &s->stats;
}
