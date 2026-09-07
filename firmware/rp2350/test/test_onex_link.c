/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * Host-Unit-Tests fuer den Protokoll-Endpunkt (../src/onex_link.c).
 *
 * Hier laufen alle drei Bausteine zusammen: Codec (onex_proto), RF-Kill
 * (onex_rfkill) und der Endpunkt. Die Tests fahren deshalb bewusst echte
 * Ablaeufe ueber die Drahtdarstellung -- nicht nur Einzelfunktionen.
 *
 * Aufruf ueber tools/fw_test.py -> tools/check_all.py.
 */
#include <stdio.h>
#include <string.h>

#include "onex_link.h"

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

/* --------------------------------------------------- Test-Transport */

/* Sammelt alles, was der Manager sendet, und zerlegt es wieder in Frames. */
typedef struct {
    uint8_t buf[4096];
    size_t  len;
} sink_t;

static void sink_write(const uint8_t *data, size_t len, void *user)
{
    sink_t *s = (sink_t *)user;
    if (s->len + len <= sizeof s->buf) {
        memcpy(&s->buf[s->len], data, len);
        s->len += len;
    }
}

static void sink_reset(sink_t *s) { s->len = 0u; }

/* Findet den n-ten gesendeten Frame eines Typs. */
static bool sink_find(const sink_t *s, uint8_t type, unsigned nth,
                      onex_hdr_t *hdr, uint8_t *payload_out)
{
    size_t pos = 0u;
    unsigned seen = 0u;
    while (pos < s->len) {
        onex_hdr_t h;
        const uint8_t *pl = NULL;
        const int r = onex_frame_decode(&s->buf[pos], s->len - pos, &h, &pl);
        if (r <= 0) {
            break;
        }
        if (h.type == type) {
            if (seen == nth) {
                *hdr = h;
                if (payload_out != NULL && pl != NULL) {
                    memcpy(payload_out, pl, h.len);
                }
                return true;
            }
            ++seen;
        }
        pos += (size_t)r;
    }
    return false;
}

static unsigned sink_count(const sink_t *s, uint8_t type)
{
    size_t pos = 0u;
    unsigned n = 0u;
    while (pos < s->len) {
        onex_hdr_t h;
        const uint8_t *pl = NULL;
        const int r = onex_frame_decode(&s->buf[pos], s->len - pos, &h, &pl);
        if (r <= 0) {
            break;
        }
        if (h.type == type) { ++n; }
        pos += (size_t)r;
    }
    return n;
}

/* --------------------------------------------------------- Fixtures */

static uint32_t g_rand_state;
static uint32_t fake_rand(void)
{
    g_rand_state = g_rand_state * 1664525u + 1013904223u;
    return g_rand_state;
}

typedef struct {
    onex_rfkill_t        rfk;
    onex_link_t          lnk;
    sink_t               out;
    onex_rfkill_inputs_t in;
} fixture_t;

static void fx_init(fixture_t *fx, uint32_t now_ms)
{
    memset(fx, 0, sizeof *fx);
    g_rand_state = 0xBEEF01u;
    onex_rfkill_init(&fx->rfk, fake_rand);
    onex_rfkill_configure(&fx->rfk, 3000u, 10000u);
    onex_link_init(&fx->lnk, &fx->rfk, sink_write, &fx->out, now_ms);

    fx->in.tx_gate_ok = false;
    fx->in.emergency_switch = false;
    fx->in.regulatory_profile_valid = true;
    fx->in.system_fault = false;
}

/* Kommando senden, wie es der Host tut. */
static void host_send(fixture_t *fx, uint8_t type, uint8_t seq,
                      const uint8_t *pl, uint8_t len, uint32_t now_ms)
{
    uint8_t frame[ONEX_MAX_FRAME];
    const size_t n = onex_frame_encode(type, seq, pl, len, frame);
    onex_link_rx(&fx->lnk, &fx->in, frame, n, now_ms);
}

/* ------------------------------------------------------------ Tests */

static void test_ping_is_acked_with_mirrored_seq(void)
{
    printf("test_ping_is_acked_with_mirrored_seq\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    host_send(&fx, ONEX_CMD_PING, 0x5Cu, NULL, 0u, 100u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "PING wird beantwortet");
    check_eq_int(pl[0], 0x5Cu, "ACK spiegelt die SEQ des Kommandos");
    check_eq_int(pl[1], ONEX_NACK_OK, "status = OK");
    check_eq_int((long)onex_link_stats(&fx.lnk)->frames_ok, 1, "ein gueltiger Frame gezaehlt");
}

static void test_unknown_command_is_nacked(void)
{
    printf("test_unknown_command_is_nacked\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    host_send(&fx, 0x7Fu, 3u, NULL, 0u, 100u);   /* Typ existiert nicht */

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_NACK, 0u, &h, pl), "NACK gesendet");
    check_eq_int(pl[1], ONEX_NACK_UNKNOWN, "reason = UNKNOWN");
    check_eq_int((long)onex_link_stats(&fx.lnk)->unknown_cmds, 1, "Zaehler");
}

static void test_missing_module_answers_busy_not_ack(void)
{
    printf("test_missing_module_answers_busy_not_ack\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Kein Delegat registriert -> das fan-Modul existiert noch nicht.
     * Ein ACK wuerde eine Wirkung behaupten, die es nicht gibt. */
    const uint8_t pl_in[2] = { 1u, 128u };
    host_send(&fx, ONEX_CMD_FAN, 7u, pl_in, 2u, 100u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_NACK, 0u, &h, pl), "NACK statt ACK");
    check_eq_int(pl[1], ONEX_NACK_BUSY, "reason = BUSY (Modul fehlt)");
    check(!sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "kein ACK gesendet");
}

static uint8_t delegate_ok(uint8_t type, const uint8_t *pl, uint8_t len, void *user)
{
    (void)pl;
    (void)len;
    unsigned *seen = (unsigned *)user;
    *seen = type;
    return ONEX_NACK_OK;
}

/* Zaehlt die TATSAECHLICHEN Ausfuehrungen -- entscheidend fuer den
 * Duplikat-Cache: ein wiederholtes CMD_POWER darf nicht zweimal wirken. */
static uint8_t delegate_counting(uint8_t type, const uint8_t *pl, uint8_t len, void *user)
{
    (void)type;
    (void)pl;
    (void)len;
    unsigned *calls = (unsigned *)user;
    (*calls)++;
    return ONEX_NACK_OK;
}

static void test_delegate_receives_foreign_commands(void)
{
    printf("test_delegate_receives_foreign_commands\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    unsigned seen = 0u;
    onex_link_set_command_handler(&fx.lnk, delegate_ok, &seen);

    const uint8_t pl_in[1] = { 2u };
    host_send(&fx, ONEX_CMD_POWER, 9u, pl_in, 1u, 100u);

    check_eq_int((long)seen, ONEX_CMD_POWER, "Delegat sieht den Kommandotyp");
    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "Delegat-OK -> ACK");
}

/* ------------------------------------------------- Fehlerbehandlung */

static void test_crc_error_gets_no_response(void)
{
    printf("test_crc_error_gets_no_response\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    uint8_t frame[ONEX_MAX_FRAME];
    const size_t n = onex_frame_encode(ONEX_CMD_PING, 0x11u, NULL, 0u, frame);
    frame[4] ^= 0x40u;   /* SEQ verfaelschen -> CRC passt nicht mehr */

    onex_link_rx(&fx.lnk, &fx.in, frame, n, 100u);

    /*
     * Bewusst KEINE Antwort: bei CRC-Fehler ist auch die SEQ unglaubwuerdig.
     * Ein NACK mit geratener SEQ koennte beim Host ein ganz anderes, noch
     * offenes Kommando als abgelehnt markieren.
     */
    check_eq_int((long)fx.out.len, 0, "keine Antwort auf korrupten Frame");
    check_eq_int((long)onex_link_stats(&fx.lnk)->crc_errors, 1, "CRC-Fehler gezaehlt");
}

static void test_version_error_is_nacked_with_seq(void)
{
    printf("test_version_error_is_nacked_with_seq\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    uint8_t frame[ONEX_MAX_FRAME];
    size_t n = onex_frame_encode(ONEX_CMD_PING, 0x44u, NULL, 0u, frame);
    frame[2] = 0x02u;                       /* fremde Version ... */
    const uint16_t crc = onex_crc16(&frame[2], 4u);
    frame[n - 2] = (uint8_t)(crc >> 8);      /* ... CRC nachziehen */
    frame[n - 1] = (uint8_t)(crc & 0xFFu);

    onex_link_rx(&fx.lnk, &fx.in, frame, n, 100u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_NACK, 0u, &h, pl), "NACK gesendet");
    check_eq_int(pl[1], ONEX_NACK_VERSION, "reason = VERSION");
    /* Genau dafuer prueft onex_proto CRC VOR Version: die SEQ ist gedeckt. */
    check_eq_int(pl[0], 0x44u, "SEQ wird korrekt gespiegelt");
}

static void test_byte_by_byte_and_garbage(void)
{
    printf("test_byte_by_byte_and_garbage\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Leitungsmuell, dann ein Frame -- byteweise eingespeist. */
    const uint8_t junk[] = { 0x00u, 0xFFu, 0xA5u, 0x13u };
    for (size_t i = 0; i < sizeof junk; ++i) {
        onex_link_rx(&fx.lnk, &fx.in, &junk[i], 1u, 100u);
    }

    uint8_t frame[ONEX_MAX_FRAME];
    const size_t n = onex_frame_encode(ONEX_CMD_PING, 0x21u, NULL, 0u, frame);
    for (size_t i = 0; i < n; ++i) {
        onex_link_rx(&fx.lnk, &fx.in, &frame[i], 1u, 100u);
    }

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "Frame trotz Stueckelung erkannt");
    check_eq_int(pl[0], 0x21u, "richtige SEQ");
}

static void test_rx_overrun_does_not_deadlock(void)
{
    printf("test_rx_overrun_does_not_deadlock\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Puffer mit SOF-aehnlichem Muell fluten, der nie einen Frame ergibt.
     * Der Link muss sich befreien -- ein stehender Link waere schlimmer
     * als Datenverlust. */
    uint8_t flood[ONEX_LINK_RX_BUF * 3u];
    for (size_t i = 0; i < sizeof flood; ++i) {
        flood[i] = (i % 2u == 0u) ? ONEX_SOF0 : 0x00u;
    }
    onex_link_rx(&fx.lnk, &fx.in, flood, sizeof flood, 100u);

    /* Danach muss ein echter Frame wieder durchkommen. */
    host_send(&fx, ONEX_CMD_PING, 0x55u, NULL, 0u, 200u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "Link erholt sich nach Flut");
    check_eq_int(pl[0], 0x55u, "richtige SEQ nach Erholung");
}

static void test_responses_are_not_echoed(void)
{
    printf("test_responses_are_not_echoed\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Der Host schickt ein ACK. Wuerde der Manager darauf mit NACK(UNKNOWN)
     * antworten, schaukelten sich beide Seiten endlos hoch. */
    const uint8_t pl_in[2] = { 1u, 0u };
    host_send(&fx, ONEX_ACK, 1u, pl_in, 2u, 100u);
    host_send(&fx, ONEX_NACK, 2u, pl_in, 2u, 100u);

    check_eq_int((long)fx.out.len, 0, "auf ACK/NACK folgt keine Antwort");
}

/* -------------------------------------------- Duplikat-Cache (Kernfall) */

static void test_duplicate_command_executes_once(void)
{
    printf("test_duplicate_command_executes_once\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    unsigned calls = 0u;

    /* Delegat zaehlt, wie oft das Kommando WIRKLICH ausgefuehrt wird. */
    onex_link_set_command_handler(&fx.lnk, delegate_counting, &calls);

    const uint8_t pl_in[1] = { 1u };   /* CMD_POWER action=1 = reboot */
    host_send(&fx, ONEX_CMD_POWER, 0x30u, pl_in, 1u, 100u);
    const size_t after_first = fx.out.len;
    host_send(&fx, ONEX_CMD_POWER, 0x30u, pl_in, 1u, 120u);   /* Retry, gleiche SEQ */

    /* Der eigentliche Schaden: ein zweiter Reboot. Das ist der Grund fuer
     * den Cache -- nicht die Zaehlerstatistik. */
    check_eq_int((long)calls, 1, "Kommando wird trotz Retry nur EINMAL ausgefuehrt");
    check(fx.out.len > after_first, "Wiederholung wird dennoch erneut beantwortet");
    check_eq_int((long)onex_link_stats(&fx.lnk)->duplicates, 1, "als Duplikat erkannt");
    check_eq_int((long)sink_count(&fx.out, ONEX_ACK), 2, "zwei ACKs gesendet");

    /* Eine NEUE SEQ desselben Typs muss dagegen wieder wirken. */
    host_send(&fx, ONEX_CMD_POWER, 0x31u, pl_in, 1u, 140u);
    check_eq_int((long)calls, 2, "neue SEQ fuehrt das Kommando erneut aus");
}

static void test_lost_ack_on_rfkill_release_stays_consistent(void)
{
    printf("test_lost_ack_on_rfkill_release_stays_consistent\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Nutzer drueckt am Geraet -> Nonce entsteht. */
    onex_rfkill_note_gesture(&fx.rfk, 1000u);

    /* Host holt das Nonce per CMD_GET ab. */
    const uint8_t get_nonce[1] = { ONEX_GET_RFKILL_NONCE };
    host_send(&fx, ONEX_CMD_GET, 0x60u, get_nonce, 1u, 1000u);

    onex_hdr_t h;
    uint8_t evt[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_EVT_NONCE, 0u, &h, evt), "EVT_NONCE gesendet");
    check_eq_int(evt[0], 1u, "Nonce ist gueltig (Geste lag vor)");

    /* Freigabe anfordern. */
    uint8_t req[1u + ONEX_RFKILL_TOKEN_LEN];
    req[0] = 0u;                                   /* engage=0 = Freigabe */
    memcpy(&req[1], &evt[1], ONEX_RFKILL_TOKEN_LEN);

    sink_reset(&fx.out);
    host_send(&fx, ONEX_CMD_RFKILL_SET, 0x61u, req, sizeof req, 1000u);

    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "Freigabe wird bestaetigt");
    check(onex_rfkill_state(&fx.rfk) == ONEX_RFKILL_RELEASED, "TX ist frei");

    /*
     * Jetzt der kritische Fall: Das ACK ging auf der Leitung verloren.
     * Der Host wiederholt mit DERSELBEN SEQ. Das Nonce ist One-Shot und
     * laengst verbraucht -- ohne Duplikat-Cache kaeme NACK(policy) zurueck
     * und der Host hielte die Freigabe faelschlich fuer gescheitert.
     */
    sink_reset(&fx.out);
    host_send(&fx, ONEX_CMD_RFKILL_SET, 0x61u, req, sizeof req, 1020u);

    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "Retry erhaelt wieder ACK");
    check(!sink_find(&fx.out, ONEX_NACK, 0u, &h, pl), "kein widerspruechliches NACK");
    check(onex_rfkill_state(&fx.rfk) == ONEX_RFKILL_RELEASED, "TX bleibt frei");
    check_eq_int((long)onex_link_stats(&fx.lnk)->duplicates, 1, "als Duplikat gewertet");
}

static void test_different_seq_is_not_a_duplicate(void)
{
    printf("test_different_seq_is_not_a_duplicate\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    host_send(&fx, ONEX_CMD_PING, 1u, NULL, 0u, 100u);
    host_send(&fx, ONEX_CMD_PING, 2u, NULL, 0u, 110u);

    check_eq_int((long)onex_link_stats(&fx.lnk)->duplicates, 0, "kein Duplikat");
    check_eq_int((long)sink_count(&fx.out, ONEX_ACK), 2, "beide beantwortet");
}

/* ------------------------------------------------------- RF-Kill-Dienst */

static void test_nonce_not_available_without_gesture(void)
{
    printf("test_nonce_not_available_without_gesture\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Ohne physische Geste darf der Host kein brauchbares Nonce bekommen --
     * das ist der Kern der Policy (Owner-Entscheidung 2026-09-07). */
    const uint8_t get_nonce[1] = { ONEX_GET_RFKILL_NONCE };
    host_send(&fx, ONEX_CMD_GET, 1u, get_nonce, 1u, 100u);

    onex_hdr_t h;
    uint8_t evt[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_EVT_NONCE, 0u, &h, evt), "EVT_NONCE gesendet");
    check_eq_int(evt[0], 0u, "valid = 0 ohne Geste");

    /* Und eine Freigabe mit Nullen scheitert. */
    uint8_t req[1u + ONEX_RFKILL_TOKEN_LEN];
    memset(req, 0, sizeof req);
    host_send(&fx, ONEX_CMD_RFKILL_SET, 2u, req, sizeof req, 100u);

    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_NACK, 0u, &h, pl), "Freigabe abgelehnt");
    check_eq_int(pl[1], ONEX_NACK_POLICY, "reason = POLICY");
    check(onex_rfkill_is_active(&fx.rfk), "Kill bleibt aktiv");
}

static void test_engage_needs_no_token(void)
{
    printf("test_engage_needs_no_token\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    /* Kill mit 1 Byte Payload, ohne Token -- muss durchgehen. */
    const uint8_t req[1] = { 1u };
    host_send(&fx, ONEX_CMD_RFKILL_SET, 5u, req, 1u, 100u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_ACK, 0u, &h, pl), "Kill wird bestaetigt");
    check(onex_rfkill_is_active(&fx.rfk), "Kill aktiv");
}

static void test_release_request_without_token_is_badarg(void)
{
    printf("test_release_request_without_token_is_badarg\n");
    fixture_t fx;
    fx_init(&fx, 0u);

    const uint8_t req[1] = { 0u };   /* Freigabe, aber Token fehlt */
    host_send(&fx, ONEX_CMD_RFKILL_SET, 6u, req, 1u, 100u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_NACK, 0u, &h, pl), "abgelehnt");
    check_eq_int(pl[1], ONEX_NACK_BADARG, "reason = BADARG");
}

static void test_valid_frame_feeds_rfkill_grace(void)
{
    printf("test_valid_frame_feeds_rfkill_grace\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    onex_rfkill_output_t rout;

    /* Freigeben. */
    onex_rfkill_note_gesture(&fx.rfk, 1000u);
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN];
    onex_rfkill_nonce(&fx.rfk, tok);
    uint8_t req[1u + ONEX_RFKILL_TOKEN_LEN];
    req[0] = 0u;
    memcpy(&req[1], tok, sizeof tok);
    host_send(&fx, ONEX_CMD_RFKILL_SET, 1u, req, sizeof req, 1000u);
    check(onex_rfkill_state(&fx.rfk) == ONEX_RFKILL_RELEASED, "Vorbedingung: frei");

    /* Jeder gueltige Frame ist ein Lebenszeichen -> Karenz laeuft nicht ab. */
    int stayed = 1;
    for (uint32_t t = 2000u; t <= 20000u; t += 1000u) {
        host_send(&fx, ONEX_CMD_PING, (uint8_t)(t / 1000u), NULL, 0u, t);
        onex_rfkill_tick(&fx.rfk, &fx.in, t, &rout);
        if (!rout.tx_enable) { stayed = 0; }
    }
    check(stayed, "laufender Verkehr haelt die Freigabe");

    /* Verkehr endet -> Karenz greift. */
    onex_rfkill_tick(&fx.rfk, &fx.in, 20000u + 3001u, &rout);
    check(!rout.tx_enable, "ohne Verkehr greift die Karenz");
}

/* ------------------------------------------------------------ Heartbeat */

static void test_heartbeat_cadence_and_flags(void)
{
    printf("test_heartbeat_cadence_and_flags\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    onex_link_set_heartbeat_period(&fx.lnk, 1000u);
    onex_link_set_system_state(&fx.lnk, ONEX_STATE_RUN);

    onex_link_tick(&fx.lnk, 0u);
    check_eq_int((long)sink_count(&fx.out, ONEX_EVT_HEARTBEAT), 1, "erster tick sendet");

    onex_link_tick(&fx.lnk, 500u);
    check_eq_int((long)sink_count(&fx.out, ONEX_EVT_HEARTBEAT), 1, "vor Ablauf kein zweiter");

    onex_link_tick(&fx.lnk, 1000u);
    check_eq_int((long)sink_count(&fx.out, ONEX_EVT_HEARTBEAT), 2, "nach 1 s der zweite");

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_EVT_HEARTBEAT, 1u, &h, pl), "Heartbeat lesbar");
    check_eq_int(pl[0], ONEX_STATE_RUN, "state im Heartbeat");
    check((pl[1] & ONEX_HB_RFKILL_ACTIVE) != 0u, "Kill-Flag gesetzt (Default)");
    check_eq_int(pl[5], 1, "uptime_s = 1 (big-endian)");
}

static void test_heartbeat_reports_release(void)
{
    printf("test_heartbeat_reports_release\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    onex_link_set_heartbeat_period(&fx.lnk, 1000u);

    onex_rfkill_note_gesture(&fx.rfk, 100u);
    uint8_t tok[ONEX_RFKILL_TOKEN_LEN];
    onex_rfkill_nonce(&fx.rfk, tok);
    uint8_t req[1u + ONEX_RFKILL_TOKEN_LEN];
    req[0] = 0u;
    memcpy(&req[1], tok, sizeof tok);
    host_send(&fx, ONEX_CMD_RFKILL_SET, 1u, req, sizeof req, 100u);

    sink_reset(&fx.out);
    onex_link_tick(&fx.lnk, 5000u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&fx.out, ONEX_EVT_HEARTBEAT, 0u, &h, pl), "Heartbeat gesendet");
    check((pl[1] & ONEX_HB_RFKILL_ACTIVE) == 0u, "Kill-Flag geloescht bei RELEASED");
}

static void test_missing_rfkill_module_reports_kill_active(void)
{
    printf("test_missing_rfkill_module_reports_kill_active\n");
    sink_t out;
    memset(&out, 0, sizeof out);
    onex_link_t lnk;
    onex_link_init(&lnk, NULL, sink_write, &out, 0u);   /* kein RF-Kill-Modul */

    onex_link_tick(&lnk, 0u);

    onex_hdr_t h;
    uint8_t pl[ONEX_MAX_PAYLOAD];
    check(sink_find(&out, ONEX_EVT_HEARTBEAT, 0u, &h, pl), "Heartbeat gesendet");
    /* Ein fehlendes Sicherheitsmodul darf nie als "TX frei" erscheinen. */
    check((pl[1] & ONEX_HB_RFKILL_ACTIVE) != 0u, "ohne Modul gilt Kill als aktiv");
}

static void test_state_change_emits_rfkill_event(void)
{
    printf("test_state_change_emits_rfkill_event\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    onex_link_set_heartbeat_period(&fx.lnk, 100000u);   /* Heartbeat stumm halten */
    onex_link_tick(&fx.lnk, 0u);
    sink_reset(&fx.out);

    /* Zustandswechsel ohne Kommando -- z.B. durch das rf_kill-Modul selbst. */
    onex_rfkill_note_gesture(&fx.rfk, 1000u);
    onex_link_tick(&fx.lnk, 1000u);

    check_eq_int((long)sink_count(&fx.out, ONEX_EVT_RFKILL), 1, "Wechsel wird gemeldet");

    /* Ohne weiteren Wechsel kein zweites Event. */
    onex_link_tick(&fx.lnk, 1100u);
    check_eq_int((long)sink_count(&fx.out, ONEX_EVT_RFKILL), 1, "kein Event-Spam");
}

static void test_event_seq_increments(void)
{
    printf("test_event_seq_increments\n");
    fixture_t fx;
    fx_init(&fx, 0u);
    onex_link_set_heartbeat_period(&fx.lnk, 1000u);

    onex_link_tick(&fx.lnk, 0u);
    onex_link_tick(&fx.lnk, 1000u);
    onex_link_tick(&fx.lnk, 2000u);

    onex_hdr_t a, b, c;
    check(sink_find(&fx.out, ONEX_EVT_HEARTBEAT, 0u, &a, NULL) &&
          sink_find(&fx.out, ONEX_EVT_HEARTBEAT, 1u, &b, NULL) &&
          sink_find(&fx.out, ONEX_EVT_HEARTBEAT, 2u, &c, NULL), "drei Heartbeats");
    check(b.seq == (uint8_t)(a.seq + 1u) && c.seq == (uint8_t)(b.seq + 1u),
          "Event-SEQ zaehlt hoch (Host kann Luecken erkennen)");
}

/* ----------------------------------------------------------------- main */

int main(void)
{
    printf("ONE-X rk3576_link -- Endpunkt-Tests (firmware/rp2350)\n\n");

    test_ping_is_acked_with_mirrored_seq();
    test_unknown_command_is_nacked();
    test_missing_module_answers_busy_not_ack();
    test_delegate_receives_foreign_commands();

    test_crc_error_gets_no_response();
    test_version_error_is_nacked_with_seq();
    test_byte_by_byte_and_garbage();
    test_rx_overrun_does_not_deadlock();
    test_responses_are_not_echoed();

    test_duplicate_command_executes_once();
    test_lost_ack_on_rfkill_release_stays_consistent();
    test_different_seq_is_not_a_duplicate();

    test_nonce_not_available_without_gesture();
    test_engage_needs_no_token();
    test_release_request_without_token_is_badarg();
    test_valid_frame_feeds_rfkill_grace();

    test_heartbeat_cadence_and_flags();
    test_heartbeat_reports_release();
    test_missing_rfkill_module_reports_kill_active();
    test_state_change_emits_rfkill_event();
    test_event_seq_increments();

    printf("\n%d Pruefungen, %d Fehler\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
