/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * Host-Unit-Tests fuer den RF-Kill-Zustandsautomaten (../src/onex_rfkill.c).
 *
 * Schwerpunkt: NEGATIVE Tests. Bei einem Sicherheitsmodul ist nicht wichtig,
 * dass die Freigabe funktioniert, sondern dass sie auf JEDEM anderen Weg
 * scheitert. Jede einzelne Bedingung der Freigabekette bekommt deshalb einen
 * eigenen Test, in dem genau sie -- und nur sie -- verletzt ist.
 *
 * Aufruf ueber tools/fw_test.py -> tools/check_all.py.
 */
#include <stdio.h>
#include <string.h>

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

/* Deterministische "Entropie" fuer reproduzierbare Tests. */
static uint32_t g_rand_state;
static uint32_t fake_rand(void)
{
    g_rand_state = g_rand_state * 1664525u + 1013904223u;
    return g_rand_state;
}

/* Standard-Eingangsbild: alles erlaubt, Gate meldet gesperrt. */
static onex_rfkill_inputs_t base_inputs(void)
{
    onex_rfkill_inputs_t in;
    in.tx_gate_ok = false;
    in.emergency_switch = false;
    in.regulatory_profile_valid = true;
    in.system_fault = false;
    return in;
}

static void boot(onex_rfkill_t *ctx)
{
    g_rand_state = 0xC0FFEEu;
    onex_rfkill_init(ctx, fake_rand);
    onex_rfkill_configure(ctx, 3000u, 10000u);
}

/* Bringt den Automaten regulaer auf RELEASED. Gibt false zurueck, wenn das
 * nicht klappt -- die positiven Tests pruefen das, die negativen bauen darauf. */
static bool release_ok(onex_rfkill_t *ctx, const onex_rfkill_inputs_t *in, uint32_t t)
{
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN];
    onex_rfkill_note_link(ctx, t);
    onex_rfkill_note_gesture(ctx, t);
    if (!onex_rfkill_nonce(ctx, tok)) {
        return false;
    }
    return onex_rfkill_request(ctx, false, tok, in, t) == ONEX_RFK_REQ_OK;
}

/* ------------------------------------------------------- Grundzustaende */

static void test_boot_default_is_kill(void)
{
    printf("test_boot_default_is_kill\n");
    onex_rfkill_t ctx;
    boot(&ctx);

    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "Start = ENGAGED");
    check(onex_rfkill_is_active(&ctx), "Kill nach Boot aktiv");

    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;
    onex_rfkill_tick(&ctx, &in, 0u, &out);
    check(!out.tx_enable, "TX nach Boot gesperrt");
    check(out.state_changed, "Startzustand wird einmal gemeldet");

    /* NULL-Kontext darf nie "frei" behaupten. */
    check(onex_rfkill_is_active(NULL), "NULL-Kontext gilt als Kill aktiv");
}

static void test_armed_does_not_enable_tx(void)
{
    printf("test_armed_does_not_enable_tx\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    onex_rfkill_note_gesture(&ctx, 1000u);
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ARMED, "Geste -> ARMED");

    onex_rfkill_tick(&ctx, &in, 1000u, &out);
    /* Der haeufigste Denkfehler: ARMED ist NICHT frei, nur ein Zeitfenster. */
    check(!out.tx_enable, "ARMED gibt TX NICHT frei");
    check(onex_rfkill_is_active(&ctx), "ARMED zaehlt als Kill aktiv");
}

static void test_full_release_path(void)
{
    printf("test_full_release_path\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "vollstaendige Kette gibt frei");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_RELEASED, "Zustand RELEASED");

    onex_rfkill_tick(&ctx, &in, 1000u, &out);
    check(out.tx_enable, "TX freigegeben");
    check(!onex_rfkill_is_active(&ctx), "Kill nicht mehr aktiv");
}

/* ------------------------------------- Freigabekette: je Bedingung ein Test */

static void test_release_needs_gesture(void)
{
    printf("test_release_needs_gesture\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();

    /* Host kennt ein Token, aber es gab keine Geste -> kein Nonce, keine Freigabe.
     * Das ist der Kernschutz: kompromittiertes Linux darf nicht senden. */
    const uint8_t guess[ONEX_RFKILL_TOKEN_LEN] = { 0 };
    const onex_rfkill_req_result_t r =
        onex_rfkill_request(&ctx, false, guess, &in, 1000u);

    check(r == ONEX_RFK_REQ_DENIED_POLICY, "ohne Geste -> DENIED_POLICY");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "bleibt ENGAGED");
}

static void test_release_needs_correct_token(void)
{
    printf("test_release_needs_correct_token\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN];

    onex_rfkill_note_gesture(&ctx, 1000u);
    check(onex_rfkill_nonce(&ctx, tok), "Nonce nach Geste verfuegbar");

    tok[3] ^= 0x01;   /* ein einziges Bit daneben */
    check(onex_rfkill_request(&ctx, false, tok, &in, 1000u) == ONEX_RFK_REQ_DENIED_POLICY,
          "falsches Token -> DENIED_POLICY");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "faellt auf ENGAGED zurueck");
}

static void test_nonce_is_one_shot(void)
{
    printf("test_nonce_is_one_shot\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN], again[ONEX_RFKILL_TOKEN_LEN];

    onex_rfkill_note_gesture(&ctx, 1000u);
    onex_rfkill_nonce(&ctx, tok);

    uint8_t wrong[ONEX_RFKILL_TOKEN_LEN];
    memcpy(wrong, tok, sizeof wrong);
    wrong[0] ^= 0xFF;

    /* Fehlversuch verbrennt das Nonce -- sonst waere es im offenen Zeitfenster
     * durch Wiederholung ratbar. */
    onex_rfkill_request(&ctx, false, wrong, &in, 1000u);
    check(!onex_rfkill_nonce(&ctx, again), "Nonce nach Fehlversuch ungueltig");

    /* Und das urspruenglich korrekte Token zieht jetzt nicht mehr. */
    check(onex_rfkill_request(&ctx, false, tok, &in, 1000u) == ONEX_RFK_REQ_DENIED_POLICY,
          "korrektes Token nach Fehlversuch wirkungslos");
}

static void test_release_needs_regulatory_profile(void)
{
    printf("test_release_needs_regulatory_profile\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    in.regulatory_profile_valid = false;   /* nur DAS ist verletzt */

    check(!release_ok(&ctx, &in, 1000u), "ohne Regulierungsprofil keine Freigabe");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "bleibt ENGAGED");
}

static void test_release_denied_while_emergency_or_fault(void)
{
    printf("test_release_denied_while_emergency_or_fault\n");

    onex_rfkill_t a;
    boot(&a);
    onex_rfkill_inputs_t in_sw = base_inputs();
    in_sw.emergency_switch = true;
    check(!release_ok(&a, &in_sw, 1000u), "Notfallschalter verhindert Freigabe");

    onex_rfkill_t b;
    boot(&b);
    onex_rfkill_inputs_t in_f = base_inputs();
    in_f.system_fault = true;
    check(!release_ok(&b, &in_f, 1000u), "System-Fault verhindert Freigabe");
}

static void test_arm_window_expires(void)
{
    printf("test_arm_window_expires\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN];

    onex_rfkill_note_gesture(&ctx, 1000u);
    onex_rfkill_nonce(&ctx, tok);

    /* 10 s Fenster: bei 11 s+1 ms ist es zu. */
    onex_rfkill_tick(&ctx, &in, 1000u + 10001u, &out);
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "Fenster verfaellt im tick");
    check(out.reason == ONEX_RFK_R_ARM_EXPIRED, "Grund = ARM_EXPIRED");
    check(onex_rfkill_request(&ctx, false, tok, &in, 1000u + 10001u) ==
          ONEX_RFK_REQ_DENIED_POLICY, "Token nach Ablauf wertlos");
}

static void test_no_entropy_means_no_release(void)
{
    printf("test_no_entropy_means_no_release\n");
    onex_rfkill_t ctx;
    onex_rfkill_init(&ctx, NULL);   /* keine Entropiequelle */
    onex_rfkill_inputs_t in = base_inputs();
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN];

    onex_rfkill_note_gesture(&ctx, 1000u);
    check(!onex_rfkill_nonce(&ctx, tok), "ohne RNG kein Nonce");

    /* Lieber gar keine Freigabe als ein vorhersagbares Token. */
    const uint8_t zeros[ONEX_RFKILL_TOKEN_LEN] = { 0 };
    check(onex_rfkill_request(&ctx, false, zeros, &in, 1000u) != ONEX_RFK_REQ_OK,
          "ohne RNG keine Freigabe (fail-safe)");
}

/* ------------------------------------------------- Kill ist immer moeglich */

static void test_engage_is_unconditional(void)
{
    printf("test_engage_is_unconditional\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    /* Kill ohne Token, ohne Profil, ohne Geste -- muss trotzdem sofort greifen. */
    in.regulatory_profile_valid = false;
    check(onex_rfkill_request(&ctx, true, NULL, &in, 2000u) == ONEX_RFK_REQ_OK,
          "Kill ohne Token wird akzeptiert");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "sofort ENGAGED");

    onex_rfkill_tick(&ctx, &in, 2000u, &out);
    check(!out.tx_enable, "TX sofort gesperrt");
}

/* ------------------------------------------- Link-Verlust (Owner-Politik) */

static void test_link_loss_grace_then_kill(void)
{
    printf("test_link_loss_grace_then_kill\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    /* Innerhalb der Karenz (3 s) bleibt die Freigabe bestehen -- ein kurzer
     * Aussetzer darf keine laufende autorisierte Messung abwuergen. */
    onex_rfkill_tick(&ctx, &in, 1000u + 2999u, &out);
    check(out.tx_enable, "innerhalb der Karenz bleibt TX frei");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_RELEASED, "noch RELEASED");

    /* Danach greift der Kill. */
    onex_rfkill_tick(&ctx, &in, 1000u + 3001u, &out);
    check(!out.tx_enable, "nach der Karenz greift der Kill");
    check(out.reason == ONEX_RFK_R_LINK_LOSS, "Grund = LINK_LOSS");
    check(out.state_changed, "Wechsel wird als Event gemeldet");
}

static void test_link_activity_resets_grace(void)
{
    printf("test_link_activity_resets_grace\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    /* Regelmaessige Lebenszeichen -> Freigabe haelt beliebig lange. */
    int stayed = 1;
    for (uint32_t t = 1000u; t < 30000u; t += 1000u) {
        onex_rfkill_note_link(&ctx, t);
        onex_rfkill_tick(&ctx, &in, t, &out);
        if (!out.tx_enable) { stayed = 0; }
    }
    check(stayed, "laufender Link haelt die Freigabe");
}

static void test_grace_survives_ms_counter_wrap(void)
{
    printf("test_grace_survives_ms_counter_wrap\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    /* Kurz vor dem uint32-Ueberlauf (~49,7 Tage Always-On -- im Feld erreichbar). */
    const uint32_t near_wrap = 0xFFFFFF00u;
    check(release_ok(&ctx, &in, near_wrap), "Freigabe kurz vor dem Wrap");

    /* Zeit laeuft ueber den Nullpunkt. Eine naive Subtraktion wuerde hier eine
     * riesige Differenz sehen und sofort killen -- oder gar keine. */
    onex_rfkill_tick(&ctx, &in, near_wrap + 1000u, &out);   /* 1 s spaeter */
    check(out.tx_enable, "1 s nach dem Wrap: Freigabe haelt");

    onex_rfkill_tick(&ctx, &in, near_wrap + 4000u, &out);   /* 4 s spaeter */
    check(!out.tx_enable, "4 s nach dem Wrap: Karenz abgelaufen, Kill");
    check(out.reason == ONEX_RFK_R_LINK_LOSS, "Grund auch ueber den Wrap korrekt");
}

/* ----------------------------------------------- Laufender Betrieb / Gate */

static void test_profile_loss_during_operation(void)
{
    printf("test_profile_loss_during_operation\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    /* Regionswechsel/Profil ungueltig waehrend TX frei ist. */
    in.regulatory_profile_valid = false;
    onex_rfkill_note_link(&ctx, 1500u);
    onex_rfkill_tick(&ctx, &in, 1500u, &out);
    check(!out.tx_enable, "Profilverlust im Betrieb killt sofort");
}

static void test_emergency_switch_overrides_everything(void)
{
    printf("test_emergency_switch_overrides_everything\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    in.emergency_switch = true;
    onex_rfkill_note_link(&ctx, 1100u);
    onex_rfkill_tick(&ctx, &in, 1100u, &out);
    check(!out.tx_enable, "Notfallschalter killt sofort");
    check(out.reason == ONEX_RFK_R_EMERGENCY_SW, "Grund = EMERGENCY_SW");
}

static void test_gate_mismatch_latches_fault(void)
{
    printf("test_gate_mismatch_latches_fault\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    /* Der gefaehrliche Fall: wir killen, aber das Gate meldet TX physisch frei.
     * Heisst: der Kill-Pfad wirkt nicht. Das darf nie durchgehen. */
    in.tx_gate_ok = true;
    onex_rfkill_tick(&ctx, &in, 100u, &out);

    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_FAULT, "Gate-Diskrepanz -> FAULT");
    check(out.reason == ONEX_RFK_R_GATE_MISMATCH, "Grund = GATE_MISMATCH");
    check(!out.tx_enable, "FAULT sperrt TX");

    /* Gelatcht: verschwindet nicht, wenn das Gate sich wieder normal meldet. */
    in.tx_gate_ok = false;
    onex_rfkill_tick(&ctx, &in, 200u, &out);
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_FAULT, "FAULT bleibt gelatcht");

    /* Und ist per Geste/Anfrage nicht wegzuwischen. */
    onex_rfkill_note_gesture(&ctx, 300u);
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_FAULT, "Geste hebt FAULT nicht auf");
    const uint8_t z[ONEX_RFKILL_TOKEN_LEN] = { 0 };
    check(onex_rfkill_request(&ctx, false, z, &in, 300u) == ONEX_RFK_REQ_DENIED_FAULT,
          "Freigabe im FAULT -> DENIED_FAULT");

    /* Nur der bewusste Eingriff -- und der fuehrt nach ENGAGED, nicht RELEASED. */
    onex_rfkill_clear_fault(&ctx);
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "clear_fault -> ENGAGED");
    check(onex_rfkill_is_active(&ctx), "nach clear_fault ist Kill weiter aktiv");
}

static void test_gate_not_ok_while_released_is_no_fault(void)
{
    printf("test_gate_not_ok_while_released_is_no_fault\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    /* Umgekehrte Richtung: freigegeben, aber Gate meldet (noch) nicht ok.
     * Unkritisch -- Einschwingzeit, ungespeistes Radio. Kein Fehlalarm. */
    in.tx_gate_ok = false;
    onex_rfkill_note_link(&ctx, 1100u);
    onex_rfkill_tick(&ctx, &in, 1100u, &out);
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_RELEASED, "kein Fault bei Gate-Verzug");
}

static void test_null_inputs_are_treated_as_unsafe(void)
{
    printf("test_null_inputs_are_treated_as_unsafe\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    check(release_ok(&ctx, &in, 1000u), "Vorbedingung: freigegeben");

    /* Kein Eingangsbild -> nichts glauben, killen. */
    onex_rfkill_tick(&ctx, NULL, 1100u, &out);
    check(!out.tx_enable, "tick ohne Eingaenge killt");
    check(onex_rfkill_state(&ctx) == ONEX_RFKILL_ENGAGED, "Zustand ENGAGED");
}

static void test_event_only_on_change(void)
{
    printf("test_event_only_on_change\n");
    onex_rfkill_t ctx;
    boot(&ctx);
    onex_rfkill_inputs_t in = base_inputs();
    onex_rfkill_output_t out;

    onex_rfkill_tick(&ctx, &in, 0u, &out);      /* Startzustand */
    check(out.state_changed, "erster tick meldet");

    /* Ohne Zustandswechsel kein EVT_RFKILL -- sonst flutet der Link. */
    int quiet = 1;
    for (uint32_t t = 1u; t < 50u; ++t) {
        onex_rfkill_tick(&ctx, &in, t, &out);
        if (out.state_changed) { quiet = 0; }
    }
    check(quiet, "unveraenderter Zustand erzeugt keine Events");
}

/* ----------------------------------------------------------------- main */

int main(void)
{
    printf("ONE-X RF-Kill -- Zustandsautomat-Tests (firmware/rp2350)\n\n");

    test_boot_default_is_kill();
    test_armed_does_not_enable_tx();
    test_full_release_path();

    test_release_needs_gesture();
    test_release_needs_correct_token();
    test_nonce_is_one_shot();
    test_release_needs_regulatory_profile();
    test_release_denied_while_emergency_or_fault();
    test_arm_window_expires();
    test_no_entropy_means_no_release();

    test_engage_is_unconditional();

    test_link_loss_grace_then_kill();
    test_link_activity_resets_grace();
    test_grace_survives_ms_counter_wrap();

    test_profile_loss_during_operation();
    test_emergency_switch_overrides_everything();
    test_gate_mismatch_latches_fault();
    test_gate_not_ok_while_released_is_no_fault();
    test_null_inputs_are_treated_as_unsafe();
    test_event_only_on_change();

    printf("\n%d Pruefungen, %d Fehler\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
