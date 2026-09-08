/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X watchdog — Gesundheitswaechter. Vertrag: ../include/onex_watchdog.h
 *
 * Die Wirkung dieses Moduls liegt im Unterlassen: es entzieht dem
 * HW-Watchdog das Futter. Deshalb ist "im Zweifel nicht kicken" hier die
 * sichere Richtung -- und jeder unbekannte Zustand zaehlt als ungesund.
 */
#include "onex_watchdog.h"

/* Wrap-sichere Differenz (uint32-ms laufen nach ~49,7 Tagen ueber). */
static uint32_t elapsed(uint32_t now, uint32_t since)
{
    return (uint32_t)(now - since);
}

static bool is_critical(const onex_watchdog_t *wd, unsigned i)
{
    return (wd->critical_mask & (1u << i)) != 0u;
}

void onex_watchdog_init(onex_watchdog_t *wd, uint32_t now_ms)
{
    if (wd == NULL) {
        return;
    }
    for (unsigned i = 0; i < (unsigned)ONEX_MOD_COUNT; ++i) {
        /*
         * Die eigentliche Absicherung gegen "nie gemeldet" ist reported[i]:
         * solange es false ist, gilt das Modul als ungesund, egal was in
         * health[] steht. Der Startwert FAULT ist bewusst redundante
         * Verteidigung fuer den Fall, dass jemand diese Reihenfolge spaeter
         * umbaut -- er ist im heutigen Ablauf nicht wirksam (und deshalb auch
         * nicht durch einen Test abgedeckt).
         */
        wd->health[i] = (uint8_t)ONEX_HEALTH_FAULT;
        wd->last_report_ms[i] = now_ms;
        wd->reported[i] = false;
    }
    wd->critical_mask = (1u << (unsigned)ONEX_MOD_RF_KILL)
                      | (1u << (unsigned)ONEX_MOD_POWER)
                      | (1u << (unsigned)ONEX_MOD_WATCHDOG);
    wd->started_ms = now_ms;
    wd->report_timeout_ms = ONEX_WD_REPORT_TIMEOUT_MS;
    wd->grace_ms = ONEX_WD_STARTUP_GRACE_MS;
    wd->latched_fault = false;
}

void onex_watchdog_set_critical(onex_watchdog_t *wd, uint32_t mask)
{
    if (wd != NULL) {
        wd->critical_mask = mask;
    }
}

void onex_watchdog_configure(onex_watchdog_t *wd, uint32_t report_timeout_ms,
                             uint32_t grace_ms)
{
    if (wd != NULL) {
        wd->report_timeout_ms = report_timeout_ms;
        wd->grace_ms = grace_ms;
    }
}

void onex_watchdog_report(onex_watchdog_t *wd, onex_module_id_t id,
                          onex_health_t health, uint32_t now_ms)
{
    if (wd == NULL || (unsigned)id >= (unsigned)ONEX_MOD_COUNT) {
        return;
    }
    wd->health[(unsigned)id] = (uint8_t)health;
    wd->last_report_ms[(unsigned)id] = now_ms;
    wd->reported[(unsigned)id] = true;
}

/* Haben alle kritischen Module mindestens einmal gemeldet? */
static bool all_critical_reported(const onex_watchdog_t *wd)
{
    for (unsigned i = 0; i < (unsigned)ONEX_MOD_COUNT; ++i) {
        if (is_critical(wd, i) && !wd->reported[i]) {
            return false;
        }
    }
    return true;
}

void onex_watchdog_tick(onex_watchdog_t *wd, uint32_t now_ms,
                        onex_watchdog_output_t *out)
{
    if (out == NULL) {
        return;
    }
    if (wd == NULL) {
        /* Ohne Kontext keine Erlaubnis. Fail-safe. */
        out->kick = false;
        out->escalate = true;
        out->culprit = (uint8_t)ONEX_MOD_WATCHDOG;
        out->in_startup_grace = false;
        return;
    }

    bool healthy = true;
    uint8_t culprit = (uint8_t)ONEX_MOD_COUNT;

    for (unsigned i = 0; i < (unsigned)ONEX_MOD_COUNT; ++i) {
        if (!is_critical(wd, i)) {
            continue;   /* unkritische Module beeinflussen den Kick nicht */
        }
        if (!wd->reported[i]) {
            /* Waehrend der Karenz unten gesondert behandelt. */
            healthy = false;
            if (culprit == (uint8_t)ONEX_MOD_COUNT) { culprit = (uint8_t)i; }
            continue;
        }
        /*
         * Schweigen zaehlt wie ein Fault. Genau das faengt den Fall, den ein
         * reiner Fehlerzaehler nicht sieht: ein Modul, das haengt und deshalb
         * gar nichts mehr meldet -- auch keinen Fehler.
         */
        if (elapsed(now_ms, wd->last_report_ms[i]) > wd->report_timeout_ms) {
            healthy = false;
            if (culprit == (uint8_t)ONEX_MOD_COUNT) { culprit = (uint8_t)i; }
            continue;
        }
        /* DEGRADED laeuft weiter (onex_modules.h) -- nur FAULT entzieht den Kick. */
        if (wd->health[i] == (uint8_t)ONEX_HEALTH_FAULT) {
            healthy = false;
            if (culprit == (uint8_t)ONEX_MOD_COUNT) { culprit = (uint8_t)i; }
        }
    }

    /*
     * Startkarenz: gilt NUR, solange noch nicht alle kritischen Module
     * gemeldet haben, und laeuft in jedem Fall nach grace_ms aus. Sie ist
     * ausdruecklich kein Freibrief -- meldet ein Modul in dieser Zeit bereits
     * FAULT, wird trotzdem nicht gekickt.
     */
    const bool grace_window = !all_critical_reported(wd)
                              && (elapsed(now_ms, wd->started_ms) <= wd->grace_ms);

    bool explicit_fault = false;
    for (unsigned i = 0; i < (unsigned)ONEX_MOD_COUNT; ++i) {
        if (is_critical(wd, i) && wd->reported[i]
            && wd->health[i] == (uint8_t)ONEX_HEALTH_FAULT) {
            explicit_fault = true;
            break;
        }
    }

    if (!healthy && !(grace_window && !explicit_fault)) {
        /* Einmal ungesund -> gelatcht. Ein Watchdog, der sich selbst wieder
         * beruhigt, verschleiert genau die Sprunghaftigkeit, die er melden
         * soll. Zuruecksetzen nur bewusst ueber onex_watchdog_clear(). */
        wd->latched_fault = true;
    }

    out->in_startup_grace = grace_window;
    out->culprit = culprit;

    if (wd->latched_fault) {
        out->kick = false;
        out->escalate = true;
        return;
    }

    out->kick = true;
    out->escalate = false;
}

void onex_watchdog_clear(onex_watchdog_t *wd, uint32_t now_ms)
{
    if (wd == NULL) {
        return;
    }
    onex_watchdog_init(wd, now_ms);
}
