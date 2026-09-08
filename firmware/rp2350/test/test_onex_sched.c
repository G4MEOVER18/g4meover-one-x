/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * Host-Unit-Tests fuer den Superloop-Scheduler (../src/onex_sched.c).
 *
 * Der Modul-Vertrag (onex_modules.h) kennt keine user-Zeiger -- init/tick/
 * event sind parameterlos bzw. bekommen nur die Zeit. Die Testmodule
 * arbeiten deshalb mit Dateiglobalen. Das entspricht der Realitaet auf dem
 * Geraet, wo jedes Modul genau einmal existiert.
 *
 * Aufruf ueber tools/fw_test.py -> tools/check_all.py.
 */
#include <stdio.h>
#include <string.h>

#include "onex_sched.h"

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

/* ------------------------------------------------------- Testmodule */

/* Aufzeichnung: in welcher Reihenfolge wurde getickt? */
static uint8_t  g_order[ONEX_MOD_COUNT];
static unsigned g_order_len;

static void record(onex_module_id_t id)
{
    if (g_order_len < ONEX_MOD_COUNT) {
        g_order[g_order_len++] = (uint8_t)id;
    }
}

/* Steuerbare Zustaende der Fake-Module. */
static bool          g_init_ok[ONEX_MOD_COUNT];
static onex_health_t g_health[ONEX_MOD_COUNT];
static unsigned      g_ticks[ONEX_MOD_COUNT];
static unsigned      g_events[ONEX_MOD_COUNT];

/* Simulierte Uhr fuer die Budget-Messung. */
static uint64_t g_clock_us;
static uint64_t clock_us(void) { return g_clock_us; }
/* Wie viel Zeit "verbraucht" ein bestimmtes Modul in seinem tick? */
static uint64_t g_cost_us[ONEX_MOD_COUNT];

#define MK_MODULE(NAME, ID)                                            \
    static bool NAME##_init(void) { return g_init_ok[ID]; }            \
    static onex_health_t NAME##_tick(uint64_t now_us) {                \
        (void)now_us;                                                  \
        record(ID);                                                    \
        g_ticks[ID]++;                                                 \
        g_clock_us += g_cost_us[ID];                                   \
        return g_health[ID];                                           \
    }                                                                  \
    static void NAME##_event(const onex_event_t *ev) {                 \
        (void)ev;                                                      \
        g_events[ID]++;                                                \
    }

MK_MODULE(rfk,   ONEX_MOD_RF_KILL)
MK_MODULE(pwr,   ONEX_MOD_POWER)
MK_MODULE(wdg,   ONEX_MOD_WATCHDOG)
MK_MODULE(hap,   ONEX_MOD_HAPTIC)

static const onex_module_t M_RFK = {
    ONEX_MOD_RF_KILL, "rf_kill", true, rfk_init, rfk_tick, rfk_event };
static const onex_module_t M_PWR = {
    ONEX_MOD_POWER, "power", true, pwr_init, pwr_tick, pwr_event };
static const onex_module_t M_WDG = {
    ONEX_MOD_WATCHDOG, "watchdog", true, wdg_init, wdg_tick, wdg_event };
static const onex_module_t M_HAP = {
    ONEX_MOD_HAPTIC, "haptic", false, hap_init, hap_tick, hap_event };

/* Tabelle in Prioritaetsreihenfolge (wie onex_modules.h sie vorsieht). */
static const onex_module_t *const TABLE[] = { &M_RFK, &M_PWR, &M_WDG, &M_HAP };
#define TABLE_N (sizeof TABLE / sizeof TABLE[0])

static void reset_modules(void)
{
    for (unsigned i = 0; i < (unsigned)ONEX_MOD_COUNT; ++i) {
        g_init_ok[i] = true;
        g_health[i] = ONEX_HEALTH_OK;
        g_ticks[i] = 0u;
        g_events[i] = 0u;
        g_cost_us[i] = 10u;      /* deutlich unter dem 200-us-Budget */
    }
    g_order_len = 0u;
    g_clock_us = 0u;
}

/* ------------------------------------------------------------- Tests */

static void test_modules_tick_in_priority_order(void)
{
    printf("test_modules_tick_in_priority_order\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check_eq_int((long)g_order_len, 4, "alle vier Module getickt");
    /* Die Reihenfolge ist Sicherheitsauslegung, keine Optimierung. */
    check_eq_int(g_order[0], ONEX_MOD_RF_KILL, "rf_kill zuerst");
    check_eq_int(g_order[1], ONEX_MOD_POWER, "dann power");
    check_eq_int(g_order[2], ONEX_MOD_WATCHDOG, "dann watchdog");
    check_eq_int(g_order[3], ONEX_MOD_HAPTIC, "unkritische zuletzt");
}

static void test_healthy_loop_permits_kick(void)
{
    printf("test_healthy_loop_permits_kick\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check(out.kick, "gesunder Durchlauf erlaubt den Kick");
    check_eq_int((long)onex_sched_stats(&s)->kicks, 1, "Kick gezaehlt");
}

static void test_critical_fault_withholds_kick(void)
{
    printf("test_critical_fault_withholds_kick\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    g_health[ONEX_MOD_POWER] = ONEX_HEALTH_FAULT;
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check(!out.kick, "Fault eines kritischen Moduls entzieht den Kick");
    check_eq_int(out.culprit, ONEX_MOD_POWER, "Verursacher benannt");
    check_eq_int((long)onex_sched_stats(&s)->kicks_withheld, 1, "gezaehlt");
}

static void test_noncritical_fault_still_kicks(void)
{
    printf("test_noncritical_fault_still_kicks\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    g_health[ONEX_MOD_HAPTIC] = ONEX_HEALTH_FAULT;
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    /* Ein defektes Haptik-Modul ist aergerlich, aber kein Reset-Grund. */
    check(out.kick, "unkritisches Modul blockiert den Kick nicht");
}

static void test_failed_init_disables_module(void)
{
    printf("test_failed_init_disables_module\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    g_init_ok[ONEX_MOD_HAPTIC] = false;
    onex_sched_init(&s, TABLE, TABLE_N, &wd);

    check(onex_sched_is_disabled(&s, ONEX_MOD_HAPTIC), "Modul deaktiviert");
    check_eq_int((long)onex_sched_stats(&s)->init_failures, 1, "gezaehlt");

    onex_sched_run_once(&s, 1000u, clock_us, &out);
    check_eq_int((long)g_ticks[ONEX_MOD_HAPTIC], 0, "wird nicht mehr getickt");
    check_eq_int((long)g_ticks[ONEX_MOD_RF_KILL], 1, "andere laufen weiter");
    check(out.kick, "unkritischer Init-Fehler blockiert den Kick nicht");
}

static void test_failed_init_of_critical_module_blocks_kick(void)
{
    printf("test_failed_init_of_critical_module_blocks_kick\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    /* Der RF-Kill startet nicht. Er wird dann nie getickt -- und meldet
     * folglich nie. Ohne besondere Behandlung liefe die Startkarenz ins
     * Leere und das System bekaeme Kicks, obwohl sein Schutz gar nicht laeuft. */
    g_init_ok[ONEX_MOD_RF_KILL] = false;
    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check(onex_sched_is_disabled(&s, ONEX_MOD_RF_KILL), "deaktiviert");
    check_eq_int((long)g_ticks[ONEX_MOD_RF_KILL], 0, "nicht getickt");
    check(!out.kick, "nicht gestartetes Sicherheitsmodul verhindert den Kick");
}

static void test_missing_critical_module_blocks_kick(void)
{
    printf("test_missing_critical_module_blocks_kick\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    /* power fehlt komplett (NULL-Platzhalter -- Modul noch nicht gebaut). */
    static const onex_module_t *const partial[] = { &M_RFK, NULL, &M_WDG, &M_HAP };
    onex_watchdog_configure(&wd, 250u, 2000u);
    onex_sched_init(&s, partial, 4u, &wd);

    /*
     * Wichtiger Unterschied zum fehlgeschlagenen init():
     * Bei einem NULL-Platzhalter kennt der Scheduler nicht einmal die
     * Modul-ID -- die steht ja IM Modul. Er kann also nichts melden. Der
     * Schutz greift hier nur PASSIV ueber reported[] im watchdog, und damit
     * erst nach der Startkarenz. Waehrend der Karenz laeuft das System an,
     * wie es soll.
     *
     * Die Tabellenposition als ID zu deuten waere die naheliegende
     * Alternative -- aber eine stille Annahme, die die Tabelle nicht
     * garantiert. Deshalb bewusst nicht.
     */
    onex_sched_run_once(&s, 1000u, clock_us, &out);
    check_eq_int((long)g_ticks[ONEX_MOD_RF_KILL], 1, "vorhandene Module laufen");
    check(out.kick, "waehrend der Startkarenz laeuft das System an");

    /* Nach der Karenz hat der watchdog von power immer noch nie gehoert. */
    onex_sched_run_once(&s, 2500000u, clock_us, &out);   /* 2500 ms */
    check(!out.kick, "dauerhaft fehlendes Sicherheitsmodul entzieht den Kick");
}

static void test_null_tick_is_skipped(void)
{
    printf("test_null_tick_is_skipped\n");
    reset_modules();
    onex_sched_t s;
    onex_sched_output_t out;

    /* Modul ohne tick (z.B. rein event-getrieben) darf nicht abstuerzen. */
    static const onex_module_t M_NOTICK = {
        ONEX_MOD_HAPTIC, "haptic", false, NULL, NULL, NULL };
    static const onex_module_t *const tbl[] = { &M_RFK, &M_NOTICK };

    onex_sched_init(&s, tbl, 2u, NULL);
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check_eq_int((long)g_ticks[ONEX_MOD_RF_KILL], 1, "anderes Modul laeuft");
    check(!out.kick, "ohne watchdog-Modul keine Kick-Erlaubnis");
}

static void test_budget_overrun_is_detected(void)
{
    printf("test_budget_overrun_is_detected\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    onex_sched_set_budget(&s, 200u);

    g_cost_us[ONEX_MOD_HAPTIC] = 500u;   /* deutlich ueber Budget */
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check(out.budget_exceeded, "Ueberschreitung erkannt");
    check_eq_int(out.slow_module, ONEX_MOD_HAPTIC, "Verursacher benannt");
    check_eq_int((long)onex_sched_stats(&s)->budget_overruns, 1, "gezaehlt");
    /* Erkennen ist nicht verhindern: der Durchlauf laeuft trotzdem zu Ende. */
    check_eq_int((long)g_ticks[ONEX_MOD_HAPTIC], 1, "tick lief vollstaendig");
}

static void test_no_budget_claim_without_clock(void)
{
    printf("test_no_budget_claim_without_clock\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);
    g_cost_us[ONEX_MOD_HAPTIC] = 5000u;

    /* Ohne Zeitquelle kann nicht gemessen werden -- dann wird auch nichts
     * behauptet, statt "alles im Budget" zu melden. */
    onex_sched_run_once(&s, 1000u, NULL, &out);
    check(!out.budget_exceeded, "keine Aussage ohne Zeitquelle");
    check_eq_int((long)onex_sched_stats(&s)->budget_overruns, 0, "nichts gezaehlt");
}

/* ------------------------------------------------------------ Events */

static void test_events_reach_all_active_modules(void)
{
    printf("test_events_reach_all_active_modules\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_sched_t s;
    onex_sched_output_t out;

    onex_sched_init(&s, TABLE, TABLE_N, &wd);

    const onex_event_t ev = { (uint8_t)ONEX_MOD_BUTTONS, 1u, 0u, 0u };
    onex_sched_post(&s, &ev);

    /* Zustellung erfolgt im naechsten Durchlauf, nicht sofort. */
    check_eq_int((long)g_events[ONEX_MOD_RF_KILL], 0, "noch nicht zugestellt");

    onex_sched_run_once(&s, 1000u, clock_us, &out);
    check_eq_int((long)g_events[ONEX_MOD_RF_KILL], 1, "rf_kill erhielt Event");
    check_eq_int((long)g_events[ONEX_MOD_HAPTIC], 1, "haptic erhielt Event");
}

static void test_disabled_module_gets_no_events(void)
{
    printf("test_disabled_module_gets_no_events\n");
    reset_modules();
    onex_sched_t s;
    onex_sched_output_t out;

    g_init_ok[ONEX_MOD_HAPTIC] = false;
    onex_sched_init(&s, TABLE, TABLE_N, NULL);

    const onex_event_t ev = { (uint8_t)ONEX_MOD_BUTTONS, 1u, 0u, 0u };
    onex_sched_post(&s, &ev);
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check_eq_int((long)g_events[ONEX_MOD_HAPTIC], 0, "deaktiviertes Modul bleibt aussen vor");
    check_eq_int((long)g_events[ONEX_MOD_POWER], 1, "aktive Module bekommen es");
}

static void test_event_queue_overflow_is_visible(void)
{
    printf("test_event_queue_overflow_is_visible\n");
    reset_modules();
    onex_sched_t s;
    onex_sched_output_t out;
    onex_sched_init(&s, TABLE, TABLE_N, NULL);

    const onex_event_t ev = { (uint8_t)ONEX_MOD_BUTTONS, 7u, 0u, 0u };
    for (unsigned i = 0; i < ONEX_SCHED_EVENT_QUEUE + 5u; ++i) {
        onex_sched_post(&s, &ev);
    }

    const onex_sched_stats_t *st = onex_sched_stats(&s);
    check_eq_int((long)st->events_posted, ONEX_SCHED_EVENT_QUEUE + 5, "alle gezaehlt");
    /* Verlust ist sichtbar statt still. */
    check_eq_int((long)st->events_dropped, 5, "Ueberzaehlige verworfen und gezaehlt");

    onex_sched_run_once(&s, 1000u, clock_us, &out);
    check_eq_int((long)g_events[ONEX_MOD_POWER], ONEX_SCHED_EVENT_QUEUE,
                 "angenommene Events werden alle zugestellt");
}

/* Handler, der beim Zustellen selbst postet -- Rekursionsfalle. */
static onex_sched_t *g_reentrant_target;
static unsigned      g_reentrant_seen;
static void reentrant_event(const onex_event_t *ev)
{
    (void)ev;
    g_reentrant_seen++;
    const onex_event_t again = { (uint8_t)ONEX_MOD_POWER, 9u, 0u, 0u };
    onex_sched_post(g_reentrant_target, &again);   /* postet waehrend Zustellung */
}

static void test_reentrant_post_does_not_recurse(void)
{
    printf("test_reentrant_post_does_not_recurse\n");
    reset_modules();
    onex_sched_t s;
    onex_sched_output_t out;

    static const onex_module_t M_RE = {
        ONEX_MOD_POWER, "reentrant", false, NULL, NULL, reentrant_event };
    static const onex_module_t *const tbl[] = { &M_RE };

    onex_sched_init(&s, tbl, 1u, NULL);
    g_reentrant_target = &s;
    g_reentrant_seen = 0u;

    const onex_event_t ev = { (uint8_t)ONEX_MOD_BUTTONS, 1u, 0u, 0u };
    onex_sched_post(&s, &ev);

    /* Ein Durchlauf stellt GENAU den Schnappschuss zu. Was der Handler
     * postet, laeuft erst in der naechsten Runde -- sonst haette dieser Test
     * eine Endlosschleife statt eines Ergebnisses. */
    onex_sched_run_once(&s, 1000u, clock_us, &out);
    check_eq_int((long)g_reentrant_seen, 1, "genau ein Event pro Durchlauf");

    onex_sched_run_once(&s, 2000u, clock_us, &out);
    check_eq_int((long)g_reentrant_seen, 2, "das nachgepostete folgt danach");
}

static void test_global_post_reaches_active_scheduler(void)
{
    printf("test_global_post_reaches_active_scheduler\n");
    reset_modules();
    onex_sched_t s;
    onex_sched_output_t out;
    onex_sched_init(&s, TABLE, TABLE_N, NULL);

    /* onex_post_event() aus onex_modules.h ist parameterlos -- der Vertrag
     * muss trotzdem erfuellt sein. */
    const onex_event_t ev = { (uint8_t)ONEX_MOD_BUTTONS, 3u, 0u, 0u };
    onex_post_event(&ev);
    onex_sched_run_once(&s, 1000u, clock_us, &out);

    check_eq_int((long)g_events[ONEX_MOD_POWER], 1, "globaler Post kommt an");
}

/* ------------------------------------------------------------ Robust */

static void test_uninitialized_scheduler_is_fail_safe(void)
{
    printf("test_uninitialized_scheduler_is_fail_safe\n");
    onex_sched_t s;
    memset(&s, 0, sizeof s);
    onex_sched_output_t out;

    onex_sched_run_once(&s, 1000u, clock_us, &out);
    check(!out.kick, "uninitialisiert -> kein Kick");

    onex_sched_run_once(NULL, 1000u, clock_us, &out);
    check(!out.kick, "NULL -> kein Kick");
    check(onex_sched_is_disabled(NULL, ONEX_MOD_RF_KILL), "NULL gilt als deaktiviert");
}

static void test_repeated_loops_keep_kicking(void)
{
    printf("test_repeated_loops_keep_kicking\n");
    reset_modules();
    onex_watchdog_t wd;
    onex_watchdog_init(&wd, 0u);
    onex_watchdog_configure(&wd, 250u, 2000u);
    onex_sched_t s;
    onex_sched_output_t out;
    onex_sched_init(&s, TABLE, TABLE_N, &wd);

    /* Dauerbetrieb: ~1 kHz Basistakt, hier grob in 10-ms-Schritten. */
    int all_kicked = 1;
    for (uint64_t t = 1000u; t <= 2000000u; t += 10000u) {
        onex_sched_run_once(&s, t, clock_us, &out);
        if (!out.kick) { all_kicked = 0; }
    }
    check(all_kicked, "gesunder Dauerbetrieb kickt durchgehend");
    check_eq_int((long)onex_sched_stats(&s)->kicks_withheld, 0, "kein Entzug");
}

/* ----------------------------------------------------------------- main */

int main(void)
{
    printf("ONE-X Superloop-Scheduler -- Tests (firmware/rp2350)\n\n");

    test_modules_tick_in_priority_order();
    test_healthy_loop_permits_kick();
    test_critical_fault_withholds_kick();
    test_noncritical_fault_still_kicks();
    test_failed_init_disables_module();
    test_failed_init_of_critical_module_blocks_kick();
    test_missing_critical_module_blocks_kick();
    test_null_tick_is_skipped();
    test_budget_overrun_is_detected();
    test_no_budget_claim_without_clock();

    test_events_reach_all_active_modules();
    test_disabled_module_gets_no_events();
    test_event_queue_overflow_is_visible();
    test_reentrant_post_does_not_recurse();
    test_global_post_reaches_active_scheduler();

    test_uninitialized_scheduler_is_fail_safe();
    test_repeated_loops_keep_kicking();

    printf("\n%d Pruefungen, %d Fehler\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
