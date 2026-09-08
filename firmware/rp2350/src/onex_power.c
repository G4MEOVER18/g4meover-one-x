/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X power — Rail-Sequencing + System-Zustandsmaschine.
 * Vertrag: ../include/onex_power.h
 *
 * Leitlinien:
 *  1. Nie endlos warten. Jeder Sequenzschritt hat eine Frist; laeuft sie ab,
 *     geht es nach FAULT -- nicht in eine stille Endlosschleife.
 *  2. Abschalten laeuft exakt umgekehrt zum Einschalten.
 *  3. FAULT ist ein sicherer Ruhezustand und gelatcht: raus nur ueber einen
 *     bewussten Eingriff, und dann nach OFF -- nie direkt zurueck nach RUN.
 */
#include "onex_power.h"

/* Wrap-sichere Differenz (uint32-ms laufen nach ~49,7 Tagen ueber). */
static uint32_t elapsed(uint32_t now, uint32_t since)
{
    return (uint32_t)(now - since);
}

static void go(onex_power_t *pw, uint8_t state)
{
    if (pw->state != state) {
        pw->state = state;
        pw->changed = true;
    }
}

static void all_rails_off(onex_power_t *pw)
{
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        pw->rail_on[i] = false;
    }
}

static void enter_fault(onex_power_t *pw, uint8_t code)
{
    /*
     * Sicherer Ruhezustand (ARCHITECTURE.md 3): geschaltete Rails aus,
     * +3V3_AON bleibt (nicht von uns geschaltet) -- der Manager selbst laeuft
     * weiter und kann die Ursache melden. Der ERSTE Fehlercode bleibt stehen:
     * Folgefehler sind Symptome, die Erstursache ist die Diagnose.
     */
    all_rails_off(pw);
    pw->seq_index = 0u;
    if (pw->state != ONEX_STATE_FAULT) {
        pw->fault = code;
    }
    go(pw, ONEX_STATE_FAULT);
}

/* Gibt es einen Grund, der SOFORT alles beendet? */
static uint8_t hard_stop_reason(const onex_power_t *pw, const onex_power_inputs_t *in)
{
    if (!in->aon_ok) {
        /* Die eigene Versorgung wackelt -- der schwerwiegendste Fall. */
        return ONEX_PWR_FAULT_AON_LOST;
    }
    if (in->battery_critical) {
        return ONEX_PWR_FAULT_BATTERY;
    }
    if (in->thermal_critical) {
        return ONEX_PWR_FAULT_THERMAL;
    }
    /*
     * Brown-out nur pruefen, wenn VSYS ueberhaupt eingeschaltet ist --
     * im Zustand OFF ist eine niedrige Messung normal, kein Fehler.
     */
    if (pw->rail_on[ONEX_RAIL_VSYS] && in->vsys_mv < pw->brownout_mv) {
        return ONEX_PWR_FAULT_BROWNOUT;
    }
    return ONEX_PWR_FAULT_NONE;
}

/* Sind alle Rails bis einschliesslich up_to eingeschaltet UND power-good? */
static bool rails_good_through(const onex_power_t *pw, const onex_power_inputs_t *in,
                               unsigned up_to)
{
    for (unsigned i = 0; i <= up_to && i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        if (!pw->rail_on[i] || !in->rail_pg[i]) {
            return false;
        }
    }
    return true;
}

/* --- BOOT: Rails der Reihe nach hoch, jede mit eigener Frist. --- */
static void step_boot(onex_power_t *pw, const onex_power_inputs_t *in, uint32_t now_ms)
{
    if (pw->seq_index < (unsigned)ONEX_RAIL_COUNT) {
        const unsigned i = pw->seq_index;

        if (!pw->rail_on[i]) {
            pw->rail_on[i] = true;
            pw->step_started_ms = now_ms;
            return;   /* Power-Good im naechsten tick pruefen (Soft-Start) */
        }
        if (in->rail_pg[i]) {
            pw->seq_index++;
            pw->step_started_ms = now_ms;
            if (pw->seq_index >= (unsigned)ONEX_RAIL_COUNT) {
                pw->host_wait_ms = now_ms;   /* jetzt auf den RK3576 warten */
            }
            return;
        }
        if (elapsed(now_ms, pw->step_started_ms) > pw->rail_timeout_ms) {
            /* Regel 1: nie endlos warten. */
            enter_fault(pw, ONEX_PWR_FAULT_RAIL_TIMEOUT);
        }
        return;
    }

    /* Alle Rails stehen -- auf das Lebenszeichen des RK3576 warten. */
    if (in->host_alive) {
        go(pw, ONEX_STATE_RUN);
        return;
    }
    if (elapsed(now_ms, pw->host_wait_ms) > pw->host_timeout_ms) {
        enter_fault(pw, ONEX_PWR_FAULT_HOST_TIMEOUT);
    }
}

/* --- SHUTDOWN: exakt umgekehrte Reihenfolge. --- */
static void step_shutdown(onex_power_t *pw, uint32_t now_ms)
{
    (void)now_ms;

    /* seq_index zeigt hier auf die Anzahl noch eingeschalteter Rails. */
    unsigned highest = (unsigned)ONEX_RAIL_COUNT;
    while (highest > 0u && !pw->rail_on[highest - 1u]) {
        --highest;
    }
    if (highest == 0u) {
        pw->seq_index = 0u;
        go(pw, ONEX_STATE_OFF);
        return;
    }
    pw->rail_on[highest - 1u] = false;
}

void onex_power_tick(onex_power_t *pw, const onex_power_inputs_t *in,
                     uint32_t now_ms, onex_power_output_t *out)
{
    if (pw == NULL || out == NULL) {
        return;
    }
    if (in == NULL) {
        /* Kein Eingangsbild -> nichts glauben, sicher stellen. */
        enter_fault(pw, ONEX_PWR_FAULT_AON_LOST);
    } else if (pw->state != ONEX_STATE_FAULT) {
        const uint8_t hard = hard_stop_reason(pw, in);
        if (hard != ONEX_PWR_FAULT_NONE) {
            enter_fault(pw, hard);
        } else {
            switch (pw->state) {
            case ONEX_STATE_OFF:
                if (pw->want_boot) {
                    pw->want_boot = false;
                    /* Ohne stabile eigene Versorgung kein Bringup. aon_ok ist
                     * oben bereits geprueft -- hier nur die Sequenz starten. */
                    pw->seq_index = 0u;
                    pw->step_started_ms = now_ms;
                    go(pw, ONEX_STATE_BOOT);
                }
                break;

            case ONEX_STATE_BOOT:
                if (pw->want_shutdown) {
                    pw->want_shutdown = false;
                    go(pw, ONEX_STATE_SHUTDOWN);
                } else {
                    step_boot(pw, in, now_ms);
                }
                break;

            case ONEX_STATE_RUN:
                /* Ein weggebrochenes Power-Good im Betrieb ist ein Fehler,
                 * kein geordnetes Abschalten. */
                if (!rails_good_through(pw, in, (unsigned)ONEX_RAIL_COUNT - 1u)) {
                    enter_fault(pw, ONEX_PWR_FAULT_RAIL_LOST);
                } else if (pw->want_shutdown) {
                    pw->want_shutdown = false;
                    go(pw, ONEX_STATE_SHUTDOWN);
                } else if (pw->want_suspend) {
                    pw->want_suspend = false;
                    go(pw, ONEX_STATE_SUSPEND);
                }
                break;

            case ONEX_STATE_SUSPEND:
                if (pw->want_shutdown) {
                    pw->want_shutdown = false;
                    go(pw, ONEX_STATE_SHUTDOWN);
                } else if (pw->resume_req) {
                    pw->resume_req = false;
                    /* Rails blieben im Suspend stehen -- nur zurueckwechseln,
                     * wenn sie es auch wirklich noch tun. */
                    if (rails_good_through(pw, in, (unsigned)ONEX_RAIL_COUNT - 1u)) {
                        go(pw, ONEX_STATE_RUN);
                    } else {
                        enter_fault(pw, ONEX_PWR_FAULT_RAIL_LOST);
                    }
                }
                break;

            case ONEX_STATE_SHUTDOWN:
                step_shutdown(pw, now_ms);
                break;

            default:
                break;
            }
        }
    }

    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        out->rail_enable[i] = pw->rail_on[i];
    }
    out->state = pw->state;
    out->fault = pw->fault;
    out->state_changed = pw->changed;
    pw->changed = false;
}

/* ------------------------------------------------------------- Setup */

void onex_power_init(onex_power_t *pw)
{
    if (pw == NULL) {
        return;
    }
    pw->state = ONEX_STATE_OFF;
    pw->fault = ONEX_PWR_FAULT_NONE;
    pw->changed = true;
    pw->seq_index = 0u;
    pw->step_started_ms = 0u;
    pw->host_wait_ms = 0u;
    all_rails_off(pw);
    pw->want_suspend = false;
    pw->want_shutdown = false;
    pw->want_boot = false;
    pw->resume_req = false;
    pw->rail_timeout_ms = ONEX_PWR_RAIL_TIMEOUT_MS;
    pw->host_timeout_ms = ONEX_PWR_HOST_BOOT_TIMEOUT_MS;
    pw->brownout_mv = ONEX_PWR_BROWNOUT_MV;
}

void onex_power_configure(onex_power_t *pw, uint32_t rail_timeout_ms,
                          uint32_t host_timeout_ms, uint16_t brownout_mv)
{
    if (pw == NULL) {
        return;
    }
    pw->rail_timeout_ms = rail_timeout_ms;
    pw->host_timeout_ms = host_timeout_ms;
    pw->brownout_mv = brownout_mv;
}

void onex_power_request_boot(onex_power_t *pw)
{
    if (pw != NULL && pw->state == ONEX_STATE_OFF) {
        pw->want_boot = true;
    }
}

void onex_power_request_shutdown(onex_power_t *pw)
{
    if (pw != NULL) {
        pw->want_shutdown = true;
    }
}

void onex_power_request_suspend(onex_power_t *pw)
{
    if (pw != NULL) {
        pw->want_suspend = true;
    }
}

void onex_power_request_resume(onex_power_t *pw)
{
    if (pw != NULL) {
        pw->resume_req = true;
    }
}

void onex_power_notify_fault(onex_power_t *pw, uint8_t fault_code)
{
    if (pw != NULL) {
        enter_fault(pw, fault_code);
    }
}

void onex_power_clear_fault(onex_power_t *pw)
{
    if (pw == NULL || pw->state != ONEX_STATE_FAULT) {
        return;
    }
    all_rails_off(pw);
    pw->seq_index = 0u;
    pw->fault = ONEX_PWR_FAULT_NONE;
    pw->want_boot = false;      /* kein automatischer Wiederanlauf */
    pw->want_suspend = false;
    pw->want_shutdown = false;
    pw->resume_req = false;
    pw->state = ONEX_STATE_OFF; /* nie direkt zurueck nach RUN */
    pw->changed = true;
}

uint8_t onex_power_state(const onex_power_t *pw)
{
    return (pw == NULL) ? (uint8_t)ONEX_STATE_FAULT : pw->state;
}

bool onex_power_is_healthy(const onex_power_t *pw)
{
    /* NULL -> nicht gesund. Ein fehlendes Modul darf nie gesund wirken. */
    return (pw != NULL) && (pw->state != ONEX_STATE_FAULT);
}
