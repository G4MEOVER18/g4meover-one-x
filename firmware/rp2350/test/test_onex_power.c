/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * Host-Unit-Tests fuer power (../src/onex_power.c) und watchdog
 * (../src/onex_watchdog.c) -- die beiden verbleibenden safety-critical
 * Module -- sowie ihre Kopplung an den RF-Kill.
 *
 * Schwerpunkt wie bei onex_rfkill: was NICHT passieren darf. Beim Watchdog
 * heisst das vor allem: er darf nicht kicken, wenn etwas kaputt ist -- denn
 * seine gesamte Wirkung liegt im Unterlassen.
 *
 * Aufruf ueber tools/fw_test.py -> tools/check_all.py.
 */
#include <stdio.h>
#include <string.h>

#include "onex_power.h"
#include "onex_watchdog.h"
#include "onex_rfkill.h"

static int g_checks;
static int g_failures;

static void check(int cond, const char *what)
{
    ++g_checks;
    if (!cond) {
        ++g_failures;
        printf("  [FAIL] %s\n", what);
    }
}

static void check_eq_int(long got, long want, const char *what)
{
    ++g_checks;
    if (got != want) {
        ++g_failures;
        printf("  [FAIL] %s: got %ld, want %ld\n", what, got, want);
    }
}

/* ------------------------------------------------------ Power-Fixtures */

/* Eingangsbild "alles in Ordnung". Power-Good folgt den Enables. */
static onex_power_inputs_t good_inputs(void)
{
    onex_power_inputs_t in;
    memset(&in, 0, sizeof in);
    in.aon_ok = true;
    in.vsys_mv = 7400u;         /* 2S nominal */
    in.host_alive = false;
    in.battery_critical = false;
    in.thermal_critical = false;
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        in.rail_pg[i] = false;
    }
    return in;
}

/* Simuliert ideale Hardware: jede eingeschaltete Rail wird power-good. */
static void follow_rails(onex_power_inputs_t *in, const onex_power_output_t *out)
{
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        in->rail_pg[i] = out->rail_enable[i];
    }
}

/*
 * Faehrt den Bringup bis RUN. Gibt die Anzahl benoetigter ticks zurueck,
 * oder 0 wenn RUN nicht erreicht wurde.
 */
static unsigned boot_to_run(onex_power_t *pw, onex_power_inputs_t *in, uint32_t *t)
{
    onex_power_output_t out;
    onex_power_request_boot(pw);
    for (unsigned i = 1; i <= 50u; ++i) {
        onex_power_tick(pw, in, *t, &out);
        follow_rails(in, &out);
        /* Sobald alle Rails stehen, meldet sich der RK3576. */
        if (out.rail_enable[ONEX_RAIL_PMIC]) {
            in->host_alive = true;
        }
        *t += 10u;
        if (out.state == ONEX_STATE_RUN) {
            return i;
        }
    }
    return 0u;
}

/* ------------------------------------------------------------- Tests */

static void test_power_starts_off_with_rails_down(void)
{
    printf("test_power_starts_off_with_rails_down\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;

    onex_power_tick(&pw, &in, 0u, &out);
    check_eq_int(out.state, ONEX_STATE_OFF, "Start = OFF");

    int all_off = 1;
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        if (out.rail_enable[i]) { all_off = 0; }
    }
    check(all_off, "alle geschalteten Rails aus");
    check_eq_int(onex_power_state(NULL), ONEX_STATE_FAULT, "NULL gilt als FAULT");
    check(!onex_power_is_healthy(NULL), "NULL gilt nicht als gesund");
}

static void test_rails_come_up_in_order(void)
{
    printf("test_rails_come_up_in_order\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    onex_power_request_boot(&pw);

    /* Reihenfolge protokollieren: in welchem tick ging welche Rail an? */
    unsigned turn_on[ONEX_RAIL_COUNT];
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) { turn_on[i] = 0u; }

    for (unsigned step = 1; step <= 30u; ++step) {
        onex_power_tick(&pw, &in, t, &out);
        for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
            if (out.rail_enable[i] && turn_on[i] == 0u) { turn_on[i] = step; }
        }
        follow_rails(&in, &out);
        t += 10u;
        if (out.state == ONEX_STATE_RUN || out.state == ONEX_STATE_FAULT) { break; }
    }

    check(turn_on[ONEX_RAIL_VSYS] > 0u, "VSYS eingeschaltet");
    check(turn_on[ONEX_RAIL_VSYS] < turn_on[ONEX_RAIL_5V_SYS], "VSYS vor +5V_SYS");
    check(turn_on[ONEX_RAIL_5V_SYS] < turn_on[ONEX_RAIL_3V3_SYS], "+5V_SYS vor +3V3_SYS");
    check(turn_on[ONEX_RAIL_3V3_SYS] < turn_on[ONEX_RAIL_PMIC], "+3V3_SYS vor PMIC");
}

static void test_boot_reaches_run(void)
{
    printf("test_boot_reaches_run\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Bringup erreicht RUN");
    check_eq_int(onex_power_state(&pw), ONEX_STATE_RUN, "Zustand RUN");
    check(onex_power_is_healthy(&pw), "System gilt als gesund");
}

static void test_rail_without_power_good_faults(void)
{
    printf("test_rail_without_power_good_faults\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_configure(&pw, 50u, 15000u, 6000u);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    onex_power_request_boot(&pw);

    /* Hardware antwortet NIE mit Power-Good. Der Sequencer darf hier nicht
     * endlos warten -- eine stille Endlosschleife waere der schlimmste Fall. */
    for (unsigned i = 0; i < 30u; ++i) {
        onex_power_tick(&pw, &in, t, &out);
        t += 10u;
        if (out.state == ONEX_STATE_FAULT) { break; }
    }

    check_eq_int(onex_power_state(&pw), ONEX_STATE_FAULT, "Timeout fuehrt nach FAULT");
    check_eq_int(out.fault, ONEX_PWR_FAULT_RAIL_TIMEOUT, "Fehlercode = RAIL_TIMEOUT");

    int all_off = 1;
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
        if (out.rail_enable[i]) { all_off = 0; }
    }
    check(all_off, "FAULT ist sicherer Ruhezustand: Rails aus");
}

static void test_host_never_alive_times_out(void)
{
    printf("test_host_never_alive_times_out\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_configure(&pw, 50u, 200u, 6000u);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    onex_power_request_boot(&pw);
    /* Rails kommen sauber hoch, aber der RK3576 meldet sich nie. */
    for (unsigned i = 0; i < 60u; ++i) {
        onex_power_tick(&pw, &in, t, &out);
        follow_rails(&in, &out);
        t += 10u;
        if (out.state == ONEX_STATE_FAULT) { break; }
    }

    check_eq_int(onex_power_state(&pw), ONEX_STATE_FAULT, "haengender Host -> FAULT");
    check_eq_int(out.fault, ONEX_PWR_FAULT_HOST_TIMEOUT, "Fehlercode = HOST_TIMEOUT");
}

static void test_power_good_lost_during_run(void)
{
    printf("test_power_good_lost_during_run\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");

    /* Eine Rail bricht im Betrieb weg -- das ist ein Fehler, kein
     * geordnetes Abschalten. */
    in.rail_pg[ONEX_RAIL_3V3_SYS] = false;
    onex_power_tick(&pw, &in, t, &out);

    check_eq_int(onex_power_state(&pw), ONEX_STATE_FAULT, "Power-Good-Verlust -> FAULT");
    check_eq_int(out.fault, ONEX_PWR_FAULT_RAIL_LOST, "Fehlercode = RAIL_LOST");
}

static void test_brownout_and_critical_inputs(void)
{
    printf("test_brownout_and_critical_inputs\n");

    /* Brown-out */
    onex_power_t a;
    onex_power_init(&a);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;
    check(boot_to_run(&a, &in, &t) > 0u, "Vorbedingung: RUN");
    in.vsys_mv = 5500u;                      /* unter 6000 mV */
    onex_power_tick(&a, &in, t, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_BROWNOUT, "Brown-out erkannt");

    /* Akku kritisch */
    onex_power_t b;
    onex_power_init(&b);
    onex_power_inputs_t in_b = good_inputs();
    t = 0u;
    check(boot_to_run(&b, &in_b, &t) > 0u, "Vorbedingung: RUN");
    in_b.battery_critical = true;
    onex_power_tick(&b, &in_b, t, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_BATTERY, "Akku kritisch erkannt");

    /* Thermik kritisch */
    onex_power_t c;
    onex_power_init(&c);
    onex_power_inputs_t in_c = good_inputs();
    t = 0u;
    check(boot_to_run(&c, &in_c, &t) > 0u, "Vorbedingung: RUN");
    in_c.thermal_critical = true;
    onex_power_tick(&c, &in_c, t, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_THERMAL, "Thermik kritisch erkannt");
}

static void test_low_vsys_in_off_is_not_a_fault(void)
{
    printf("test_low_vsys_in_off_is_not_a_fault\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;

    /* Im Zustand OFF ist VSYS naturgemaess niedrig -- das ist kein Fehler,
     * sonst waere das Geraet nach dem Einschalten sofort im FAULT. */
    in.vsys_mv = 0u;
    onex_power_tick(&pw, &in, 0u, &out);
    check_eq_int(out.state, ONEX_STATE_OFF, "OFF bleibt OFF");
    check_eq_int(out.fault, ONEX_PWR_FAULT_NONE, "kein Brown-out im OFF");
}

static void test_aon_loss_is_worst_case(void)
{
    printf("test_aon_loss_is_worst_case\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");

    /* +3V3_AON speist den Manager selbst (sheet_01). Faellt sie, ist nichts
     * mehr verlaesslich. */
    in.aon_ok = false;
    onex_power_tick(&pw, &in, t, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_AON_LOST, "AON-Verlust erkannt");
    check_eq_int(out.state, ONEX_STATE_FAULT, "-> FAULT");
}

static void test_null_inputs_are_treated_as_unsafe(void)
{
    printf("test_null_inputs_are_treated_as_unsafe\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");
    onex_power_tick(&pw, NULL, t, &out);
    check_eq_int(out.state, ONEX_STATE_FAULT, "tick ohne Eingaenge -> FAULT");
}

static void test_shutdown_reverses_the_sequence(void)
{
    printf("test_shutdown_reverses_the_sequence\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");

    onex_power_request_shutdown(&pw);

    unsigned turn_off[ONEX_RAIL_COUNT];
    for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) { turn_off[i] = 0u; }

    for (unsigned step = 1; step <= 30u; ++step) {
        onex_power_tick(&pw, &in, t, &out);
        for (unsigned i = 0; i < (unsigned)ONEX_RAIL_COUNT; ++i) {
            if (!out.rail_enable[i] && turn_off[i] == 0u) { turn_off[i] = step; }
        }
        follow_rails(&in, &out);
        t += 10u;
        if (out.state == ONEX_STATE_OFF) { break; }
    }

    check_eq_int(onex_power_state(&pw), ONEX_STATE_OFF, "erreicht OFF");
    /* Genau umgekehrt zum Einschalten. */
    check(turn_off[ONEX_RAIL_PMIC] < turn_off[ONEX_RAIL_3V3_SYS], "PMIC zuerst aus");
    check(turn_off[ONEX_RAIL_3V3_SYS] < turn_off[ONEX_RAIL_5V_SYS], "dann +3V3_SYS");
    check(turn_off[ONEX_RAIL_5V_SYS] < turn_off[ONEX_RAIL_VSYS], "dann +5V_SYS, VSYS zuletzt");
}

static void test_suspend_resume(void)
{
    printf("test_suspend_resume\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");

    onex_power_request_suspend(&pw);
    onex_power_tick(&pw, &in, t, &out);
    check_eq_int(out.state, ONEX_STATE_SUSPEND, "RUN -> SUSPEND");

    onex_power_request_resume(&pw);
    onex_power_tick(&pw, &in, t + 10u, &out);
    check_eq_int(out.state, ONEX_STATE_RUN, "SUSPEND -> RUN");
}

static void test_resume_with_dead_rails_faults(void)
{
    printf("test_resume_with_dead_rails_faults\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");
    onex_power_request_suspend(&pw);
    onex_power_tick(&pw, &in, t, &out);

    /* Waehrend des Suspends ist eine Rail weggebrochen. Ein Resume darf das
     * nicht ueberspringen, nur weil der Zustand vorher RUN war. */
    in.rail_pg[ONEX_RAIL_5V_SYS] = false;
    onex_power_request_resume(&pw);
    onex_power_tick(&pw, &in, t + 10u, &out);

    check_eq_int(out.state, ONEX_STATE_FAULT, "Resume auf toter Rail -> FAULT");
    check_eq_int(out.fault, ONEX_PWR_FAULT_RAIL_LOST, "Fehlercode = RAIL_LOST");
}

static void test_fault_is_latched_and_first_cause_wins(void)
{
    printf("test_fault_is_latched_and_first_cause_wins\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");

    in.thermal_critical = true;              /* Erstursache */
    onex_power_tick(&pw, &in, t, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_THERMAL, "Erstursache = THERMAL");

    /* Folgefehler duerfen die Diagnose nicht ueberschreiben. */
    in.battery_critical = true;
    onex_power_tick(&pw, &in, t + 10u, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_THERMAL, "Erstursache bleibt stehen");

    /* Auch nach Wegfall aller Ursachen bleibt FAULT gelatcht. */
    in.thermal_critical = false;
    in.battery_critical = false;
    onex_power_tick(&pw, &in, t + 20u, &out);
    check_eq_int(out.state, ONEX_STATE_FAULT, "FAULT bleibt gelatcht");

    /* Nur bewusst -- und dann nach OFF, nie direkt zurueck nach RUN. */
    onex_power_clear_fault(&pw);
    check_eq_int(onex_power_state(&pw), ONEX_STATE_OFF, "clear_fault -> OFF");
    onex_power_tick(&pw, &in, t + 30u, &out);
    check_eq_int(out.state, ONEX_STATE_OFF, "kein automatischer Wiederanlauf");
}

static void test_notify_fault_keeps_first_cause(void)
{
    printf("test_notify_fault_keeps_first_cause\n");
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t in = good_inputs();
    onex_power_output_t out;
    uint32_t t = 0u;

    check(boot_to_run(&pw, &in, &t) > 0u, "Vorbedingung: RUN");

    /*
     * Anderer Weg in den FAULT als ueber tick(): die direkte Eskalation.
     * Der tick-Pfad wertet im FAULT keine Ursachen mehr aus -- nur hier
     * koennen sich Folgemeldungen ueberhaupt ueberschreiben.
     */
    onex_power_notify_fault(&pw, ONEX_PWR_FAULT_WATCHDOG);   /* Erstursache */
    onex_power_tick(&pw, &in, t, &out);
    check_eq_int(out.fault, ONEX_PWR_FAULT_WATCHDOG, "Erstursache = WATCHDOG");

    /* Weitere Module melden hinterher ihre Symptome. */
    onex_power_notify_fault(&pw, ONEX_PWR_FAULT_RAIL_LOST);
    onex_power_notify_fault(&pw, ONEX_PWR_FAULT_BROWNOUT);
    onex_power_tick(&pw, &in, t + 10u, &out);

    /* Folgefehler sind Symptome -- die Erstursache ist die Diagnose. */
    check_eq_int(out.fault, ONEX_PWR_FAULT_WATCHDOG, "Folgefehler ueberschreiben nicht");
    check_eq_int(out.state, ONEX_STATE_FAULT, "bleibt im FAULT");
}

/* --------------------------------------------------------- Watchdog */

static void test_watchdog_kicks_when_all_healthy(void)
{
    printf("test_watchdog_kicks_when_all_healthy\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_output_t out;

    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 0u);

    onex_watchdog_tick(&wd, 10u, &out);
    check(out.kick, "alle kritischen Module OK -> kick");
    check(!out.escalate, "keine Eskalation");
}

static void test_watchdog_withholds_kick_on_fault(void)
{
    printf("test_watchdog_withholds_kick_on_fault\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_output_t out;

    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_FAULT, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 0u);

    onex_watchdog_tick(&wd, 10u, &out);
    /* Der gefaehrliche Fehler waere "kickt weiter, obwohl etwas kaputt ist". */
    check(!out.kick, "Fault eines kritischen Moduls entzieht den Kick");
    check(out.escalate, "Eskalation gemeldet");
    check_eq_int(out.culprit, ONEX_MOD_POWER, "Verursacher benannt");
}

static void test_watchdog_degraded_still_kicks(void)
{
    printf("test_watchdog_degraded_still_kicks\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_output_t out;

    /* DEGRADED = laeuft eingeschraenkt weiter, kein Reset (onex_modules.h). */
    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_DEGRADED, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 0u);

    onex_watchdog_tick(&wd, 10u, &out);
    check(out.kick, "DEGRADED loest keinen Reset aus");
}

static void test_watchdog_silence_counts_as_fault(void)
{
    printf("test_watchdog_silence_counts_as_fault\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_configure(&wd, 250u, 2000u);
    onex_watchdog_output_t out;

    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 0u);

    onex_watchdog_tick(&wd, 100u, &out);
    check(out.kick, "innerhalb der Frist wird gekickt");

    /*
     * Jetzt meldet sich niemand mehr. Ein reiner Fehlerzaehler saehe hier
     * nichts -- genau deshalb zaehlt Schweigen wie ein Fault.
     */
    onex_watchdog_tick(&wd, 400u, &out);
    check(!out.kick, "abgelaufene Meldefrist entzieht den Kick");
    check(out.escalate, "Eskalation gemeldet");
}

static void test_watchdog_startup_grace(void)
{
    printf("test_watchdog_startup_grace\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_configure(&wd, 250u, 500u);
    onex_watchdog_output_t out;

    /* Direkt nach dem Reset hat noch niemand gemeldet. Ohne Karenz wuerde
     * sofort erneut resettet -> Reset-Schleife, das Geraet kaeme nie hoch. */
    onex_watchdog_tick(&wd, 10u, &out);
    check(out.kick, "Startkarenz erlaubt den Kick");
    check(out.in_startup_grace, "Karenz wird ausgewiesen");

    /* Sie ist aber begrenzt. */
    onex_watchdog_t wd2;
    onex_watchdog_init(&wd2, 0u);
    onex_watchdog_configure(&wd2, 250u, 500u);
    onex_watchdog_tick(&wd2, 600u, &out);
    check(!out.kick, "nach Ablauf der Karenz kein Kick ohne Meldungen");
}

static void test_startup_grace_is_no_blank_cheque(void)
{
    printf("test_startup_grace_is_no_blank_cheque\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_configure(&wd, 250u, 5000u);
    onex_watchdog_output_t out;

    /* Meldet ein Modul waehrend der Karenz bereits FAULT, wird trotzdem
     * nicht gekickt -- die Karenz deckt Unwissenheit ab, nicht Defekte. */
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_FAULT, 10u);
    onex_watchdog_tick(&wd, 20u, &out);

    check(!out.kick, "expliziter Fault schlaegt die Startkarenz");
    check(out.escalate, "Eskalation trotz Karenz");
}

static void test_watchdog_fault_is_latched(void)
{
    printf("test_watchdog_fault_is_latched\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_output_t out;

    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_FAULT, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 0u);
    onex_watchdog_tick(&wd, 10u, &out);
    check(!out.kick, "Vorbedingung: kein Kick");

    /* Das Modul meldet sich wieder gesund. Ein Watchdog, der sich davon
     * beruhigen laesst, verschleiert genau die Sprunghaftigkeit, die er
     * melden soll. */
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_OK, 20u);
    onex_watchdog_tick(&wd, 30u, &out);
    check(!out.kick, "Erholung hebt den Entzug nicht auf");

    /* Nur ein bewusster Eingriff. */
    onex_watchdog_clear(&wd, 40u);
    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 40u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_OK, 40u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 40u);
    onex_watchdog_tick(&wd, 50u, &out);
    check(out.kick, "nach bewusstem clear wieder Kick");
}

static void test_noncritical_module_does_not_block_kick(void)
{
    printf("test_noncritical_module_does_not_block_kick\n");
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_output_t out;

    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_OK, 0u);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, 0u);
    /* Ein defektes Haptik-Modul ist aergerlich, aber kein Reset-Grund. */
    onex_watchdog_report(&wd, ONEX_MOD_HAPTIC, ONEX_HEALTH_FAULT, 0u);

    onex_watchdog_tick(&wd, 10u, &out);
    check(out.kick, "unkritisches Modul blockiert den Kick nicht");
}

static void test_watchdog_null_is_fail_safe(void)
{
    printf("test_watchdog_null_is_fail_safe\n");
    onex_watchdog_output_t out;
    onex_watchdog_tick(NULL, 0u, &out);
    check(!out.kick, "ohne Kontext kein Kick");
    check(out.escalate, "und Eskalation");
}

static void test_watchdog_survives_ms_wrap(void)
{
    printf("test_watchdog_survives_ms_wrap\n");
    const uint32_t near_wrap = 0xFFFFFF00u;
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, near_wrap);
    onex_watchdog_configure(&wd, 250u, 100u);
    onex_watchdog_output_t out;

    onex_watchdog_report(&wd, ONEX_MOD_RF_KILL, ONEX_HEALTH_OK, near_wrap);
    onex_watchdog_report(&wd, ONEX_MOD_POWER, ONEX_HEALTH_OK, near_wrap);
    onex_watchdog_report(&wd, ONEX_MOD_WATCHDOG, ONEX_HEALTH_OK, near_wrap);

    /* Zeit laeuft ueber den Nullpunkt. */
    onex_watchdog_tick(&wd, near_wrap + 100u, &out);
    check(out.kick, "innerhalb der Frist ueber den Wrap hinweg");

    onex_watchdog_tick(&wd, near_wrap + 400u, &out);
    check(!out.kick, "Frist laeuft auch ueber den Wrap korrekt ab");
}

/* ------------------------------------------- Kopplung an den RF-Kill */

static void test_power_fault_kills_rf(void)
{
    printf("test_power_fault_kills_rf\n");

    /* Die Kette aus ARCHITECTURE.md 4: Modul-Fault -> power -> rf_kill. */
    onex_power_t pw;
    onex_power_init(&pw);
    onex_power_inputs_t pin = good_inputs();
    onex_power_output_t pout;
    uint32_t t = 0u;
    check(boot_to_run(&pw, &pin, &t) > 0u, "Vorbedingung: RUN");

    onex_rfkill_t rfk;
    onex_rfkill_init(&rfk, NULL);
    onex_rfkill_inputs_t rin;
    memset(&rin, 0, sizeof rin);
    rin.regulatory_profile_valid = true;
    onex_rfkill_output_t rout;

    /* Watchdog eskaliert -> power geht nach FAULT. */
    onex_power_notify_fault(&pw, ONEX_PWR_FAULT_WATCHDOG);
    onex_power_tick(&pw, &pin, t, &pout);
    check_eq_int(pout.state, ONEX_STATE_FAULT, "power im FAULT");

    /* Der Systemzustand wird zum RF-Kill-Eingang. */
    rin.system_fault = !onex_power_is_healthy(&pw);
    onex_rfkill_tick(&rfk, &rin, t, &rout);

    check(rin.system_fault, "power meldet sich als ungesund");
    check(!rout.tx_enable, "RF-Kill sperrt TX bei System-Fault");
    check(onex_rfkill_is_active(&rfk), "Kill aktiv");
}

/* ----------------------------------------------------------------- main */

int main(void)
{
    printf("ONE-X power + watchdog -- Tests (firmware/rp2350)\n\n");

    test_power_starts_off_with_rails_down();
    test_rails_come_up_in_order();
    test_boot_reaches_run();
    test_rail_without_power_good_faults();
    test_host_never_alive_times_out();
    test_power_good_lost_during_run();
    test_brownout_and_critical_inputs();
    test_low_vsys_in_off_is_not_a_fault();
    test_aon_loss_is_worst_case();
    test_null_inputs_are_treated_as_unsafe();
    test_shutdown_reverses_the_sequence();
    test_suspend_resume();
    test_resume_with_dead_rails_faults();
    test_fault_is_latched_and_first_cause_wins();
    test_notify_fault_keeps_first_cause();

    test_watchdog_kicks_when_all_healthy();
    test_watchdog_withholds_kick_on_fault();
    test_watchdog_degraded_still_kicks();
    test_watchdog_silence_counts_as_fault();
    test_watchdog_startup_grace();
    test_startup_grace_is_no_blank_cheque();
    test_watchdog_fault_is_latched();
    test_noncritical_module_does_not_block_kick();
    test_watchdog_null_is_fail_safe();
    test_watchdog_survives_ms_wrap();

    test_power_fault_kills_rf();

    printf("\n%d Pruefungen, %d Fehler\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
