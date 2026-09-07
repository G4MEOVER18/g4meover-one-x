/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X RF-Kill — Zustandsautomat. Vertrag: ../include/onex_rfkill.h
 *
 * Leitlinien in diesem Modul:
 *  1. Kill ist billig, Freigabe ist teuer. Jeder Weg nach ENGAGED/FAULT ist
 *     unbedingt; jeder Weg nach RELEASED prueft die volle Kette.
 *  2. Keine Schleife, keine Allokation, kein blockierender Aufruf
 *     (Modul-Vertrag: tick() < 200 us).
 *  3. Bei Zweifel: Kill. Ein unerwarteter Eingang fuehrt nie zu TX frei.
 */
#include "onex_rfkill.h"

/* Zeitdifferenz mit Wrap-Behandlung: uint32-Millisekunden laufen nach
 * ~49,7 Tagen ueber. Ein Always-On-Geraet erreicht das im Feld -- eine naive
 * Subtraktion liesse die Karenzzeit dann scheinbar nie ablaufen. */
static uint32_t elapsed(uint32_t now, uint32_t since)
{
    return (uint32_t)(now - since);
}

/* Konstantzeitiger Vergleich: keine fruehe Rueckkehr beim ersten
 * abweichenden Byte. Auf einem MCU ist das Zeitleck klein, aber ein
 * Sicherheitspfad wird nicht "wahrscheinlich schon ok" implementiert. */
static bool token_equal(const uint8_t *a, const uint8_t *b)
{
    uint8_t diff = 0u;
    for (size_t i = 0; i < ONEX_RFKILL_TOKEN_LEN; ++i) {
        diff = (uint8_t)(diff | (uint8_t)(a[i] ^ b[i]));
    }
    return diff == 0u;
}

/*
 * Die EINE Definition von "TX ist frei". Bewusst eine einzige Stelle:
 * Sowohl der Sollwert fuer das HW-Gate als auch die Erwartung im
 * Diskrepanz-Abgleich leiten sich hieraus ab. Zwei Kopien derselben Regel
 * waeren ein Sicherheitsrisiko -- aendert jemand nur eine, prueft der
 * Gate-Abgleich gegen eine Erwartung, die nicht mehr dem Befehl entspricht.
 *
 * ARMED gehoert ausdruecklich NICHT dazu: das ist nur ein Zeitfenster.
 */
static bool tx_allowed(const onex_rfkill_t *ctx)
{
    return ctx->state == ONEX_RFKILL_RELEASED;
}

/* Zustandswechsel + Flankenmerker. Ein Wechsel auf denselben Zustand mit
 * neuem Grund gilt NICHT als Aenderung (kein Event-Spam im tick). */
static void go(onex_rfkill_t *ctx, onex_rfkill_state_t st, onex_rfkill_reason_t why)
{
    if (ctx->state != st) {
        ctx->state = st;
        ctx->reason = why;
        ctx->changed = true;
    }
}

static void invalidate_nonce(onex_rfkill_t *ctx)
{
    for (size_t i = 0; i < ONEX_RFKILL_TOKEN_LEN; ++i) {
        ctx->nonce[i] = 0u;
    }
    ctx->nonce_valid = false;
}

static void make_nonce(onex_rfkill_t *ctx)
{
    if (ctx->rand32 == NULL) {
        /* Ohne Entropiequelle waere das Token vorhersagbar -> lieber keins.
         * Jede Freigabe scheitert dann an (d). Fail-safe. */
        invalidate_nonce(ctx);
        return;
    }
    for (size_t i = 0; i < ONEX_RFKILL_TOKEN_LEN; i += 4u) {
        const uint32_t r = ctx->rand32();
        ctx->nonce[i]      = (uint8_t)(r & 0xFFu);
        ctx->nonce[i + 1u] = (uint8_t)((r >> 8) & 0xFFu);
        ctx->nonce[i + 2u] = (uint8_t)((r >> 16) & 0xFFu);
        ctx->nonce[i + 3u] = (uint8_t)((r >> 24) & 0xFFu);
    }
    ctx->nonce_valid = true;
}

void onex_rfkill_init(onex_rfkill_t *ctx, uint32_t (*rand32)(void))
{
    if (ctx == NULL) {
        return;
    }
    /* Regel 1 aus sheet_01: Default nach Boot/Reset/Fault = Kill aktiv. */
    ctx->state = ONEX_RFKILL_ENGAGED;
    ctx->reason = ONEX_RFK_R_BOOT_DEFAULT;
    ctx->last_link_ms = 0u;
    ctx->armed_at_ms = 0u;
    ctx->link_seen = false;
    ctx->changed = true;   /* Startzustand einmal melden */
    ctx->rand32 = rand32;
    ctx->grace_ms = ONEX_RFKILL_LINK_GRACE_MS;
    ctx->arm_ttl_ms = ONEX_RFKILL_ARM_TTL_MS;
    invalidate_nonce(ctx);
}

void onex_rfkill_configure(onex_rfkill_t *ctx, uint32_t grace_ms, uint32_t arm_ttl_ms)
{
    if (ctx == NULL) {
        return;
    }
    ctx->grace_ms = grace_ms;
    ctx->arm_ttl_ms = arm_ttl_ms;
}

void onex_rfkill_note_link(onex_rfkill_t *ctx, uint32_t now_ms)
{
    if (ctx == NULL) {
        return;
    }
    ctx->last_link_ms = now_ms;
    ctx->link_seen = true;
}

void onex_rfkill_note_gesture(onex_rfkill_t *ctx, uint32_t now_ms)
{
    if (ctx == NULL) {
        return;
    }
    /* Im FAULT bleibt eine Geste wirkungslos: ein gelatchter Fault wird
     * bewusst geloescht, nicht durch Tastendruck weggewischt. */
    if (ctx->state == ONEX_RFKILL_FAULT) {
        return;
    }
    /* Bereits freigegeben -> Geste ist bedeutungslos (kein erneutes Arming). */
    if (ctx->state == ONEX_RFKILL_RELEASED) {
        return;
    }

    ctx->armed_at_ms = now_ms;
    make_nonce(ctx);
    go(ctx, ONEX_RFKILL_ARMED, ONEX_RFK_R_USER_GESTURE);
}

bool onex_rfkill_nonce(const onex_rfkill_t *ctx, uint8_t *out)
{
    if (ctx == NULL || out == NULL || !ctx->nonce_valid) {
        return false;
    }
    for (size_t i = 0; i < ONEX_RFKILL_TOKEN_LEN; ++i) {
        out[i] = ctx->nonce[i];
    }
    return true;
}

onex_rfkill_req_result_t onex_rfkill_request(onex_rfkill_t *ctx,
                                             bool engage,
                                             const uint8_t *token,
                                             const onex_rfkill_inputs_t *in,
                                             uint32_t now_ms)
{
    if (ctx == NULL || in == NULL) {
        return ONEX_RFK_REQ_BADARG;
    }

    /* --- Kill: unbedingt, sofort, in jedem Zustand. ---------------------
     * Kein Token, kein Profil, keine Zustandsbedingung. Wenn irgendjemand
     * "aus" sagt, geht es aus. */
    if (engage) {
        invalidate_nonce(ctx);
        if (ctx->state != ONEX_RFKILL_FAULT) {
            go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_HOST_REQUEST);
        }
        return ONEX_RFK_REQ_OK;
    }

    /* --- Ab hier: Freigabe-ANFRAGE. Alles muss stimmen. ----------------- */

    if (token == NULL) {
        return ONEX_RFK_REQ_BADARG;
    }

    /* Gelatchter Fault ist nicht verhandelbar. */
    if (ctx->state == ONEX_RFKILL_FAULT) {
        return ONEX_RFK_REQ_DENIED_FAULT;
    }

    /* Bereits frei: idempotent bestaetigen, aber Nonce trotzdem verbrauchen. */
    if (ctx->state == ONEX_RFKILL_RELEASED) {
        invalidate_nonce(ctx);
        return ONEX_RFK_REQ_OK;
    }

    /*
     * One-Shot: Das Nonce ist nach dieser Anfrage in JEDEM Fall verbraucht --
     * auch bei Ablehnung. Sonst koennte der Host es mit wiederholten Anfragen
     * erraten, solange das Zeitfenster offen ist.
     */
    const bool had_nonce = ctx->nonce_valid;
    uint8_t expect[ONEX_RFKILL_TOKEN_LEN];
    for (size_t i = 0; i < ONEX_RFKILL_TOKEN_LEN; ++i) {
        expect[i] = ctx->nonce[i];
    }
    invalidate_nonce(ctx);

    /* (a) physische Geste liegt vor */
    if (ctx->state != ONEX_RFKILL_ARMED) {
        go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_POLICY_DENIED);
        return ONEX_RFK_REQ_DENIED_POLICY;
    }
    /* (b) Zeitfenster offen */
    if (elapsed(now_ms, ctx->armed_at_ms) > ctx->arm_ttl_ms) {
        go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_ARM_EXPIRED);
        return ONEX_RFK_REQ_DENIED_POLICY;
    }
    /* (c) gueltiges Regulierungsprofil */
    if (!in->regulatory_profile_valid) {
        go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_POLICY_DENIED);
        return ONEX_RFK_REQ_DENIED_POLICY;
    }
    /* (e) nichts, was ohnehin killen wuerde */
    if (in->emergency_switch || in->system_fault) {
        go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_POLICY_DENIED);
        return ONEX_RFK_REQ_DENIED_POLICY;
    }
    /* (d) Token == ausgegebenes Nonce */
    if (!had_nonce || !token_equal(token, expect)) {
        go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_POLICY_DENIED);
        return ONEX_RFK_REQ_DENIED_POLICY;
    }

    go(ctx, ONEX_RFKILL_RELEASED, ONEX_RFK_R_USER_RELEASE);
    return ONEX_RFK_REQ_OK;
}

void onex_rfkill_tick(onex_rfkill_t *ctx,
                      const onex_rfkill_inputs_t *in,
                      uint32_t now_ms,
                      onex_rfkill_output_t *out)
{
    if (ctx == NULL || out == NULL) {
        return;
    }
    if (in == NULL) {
        /* Kein Eingangsbild -> nichts glauben, killen. */
        go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_FAULT_ESCALATION);
    } else {
        /* Reihenfolge = Vorrang. Das Staerkste zuerst. */

        /* 1. Physischer Notfallschalter schlaegt alles. */
        if (in->emergency_switch) {
            invalidate_nonce(ctx);
            go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_EMERGENCY_SW);
        }
        /* 2. Anderes safety-critical Modul im Fault -> Eskalation. */
        else if (in->system_fault) {
            invalidate_nonce(ctx);
            go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_FAULT_ESCALATION);
        }
        else if (ctx->state == ONEX_RFKILL_RELEASED) {
            /* 3. Regulierungsprofil darf im laufenden Betrieb nicht wegfallen. */
            if (!in->regulatory_profile_valid) {
                go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_POLICY_DENIED);
            }
            /* 4. Link-Karenz (Owner-Entscheidung 2026-09-07).
             * Nur wirksam, wenn je ein Lebenszeichen kam -- sonst wuerde ein
             * Geraet ohne laufendes Linux nie freigeben koennen. */
            else if (ctx->link_seen &&
                     elapsed(now_ms, ctx->last_link_ms) > ctx->grace_ms) {
                go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_LINK_LOSS);
            }
        }
        else if (ctx->state == ONEX_RFKILL_ARMED) {
            /* 5. Freigabefenster verfallen -> zurueck in den sicheren Zustand. */
            if (elapsed(now_ms, ctx->armed_at_ms) > ctx->arm_ttl_ms) {
                invalidate_nonce(ctx);
                go(ctx, ONEX_RFKILL_ENGAGED, ONEX_RFK_R_ARM_EXPIRED);
            }
        }
    }

    /* Sollzustand fuer das HW-Gate -- aus der einen Definition. */
    const bool want_tx = tx_allowed(ctx);

    /*
     * 6. Gate-Abgleich — der eigentliche Zweck von TX_GATE_OK.
     * Der gemessene Zustand ist die Wahrheit, nicht der befohlene.
     * Die gefaehrliche Richtung ist "wir killen, aber TX ist physisch frei":
     * das bedeutet, der Kill-Pfad wirkt nicht. Das wird als FAULT gelatcht.
     *
     * Die andere Richtung (freigegeben, Gate meldet nicht ok) ist unkritisch --
     * das Gate braucht Einschwingzeit oder ein Radio ist ungespeist. Sie fuehrt
     * NICHT in den Fault, sonst waere jede Freigabe ein Fehlalarm.
     */
    if (in != NULL && !want_tx && in->tx_gate_ok && ctx->state != ONEX_RFKILL_FAULT) {
        go(ctx, ONEX_RFKILL_FAULT, ONEX_RFK_R_GATE_MISMATCH);
    }

    /* Nach dem Gate-Abgleich erneut auswerten: der Abgleich kann den Zustand
     * gerade auf FAULT gezogen haben. Gleiche Definition, aktueller Zustand. */
    out->tx_enable = tx_allowed(ctx);
    out->state = ctx->state;
    out->reason = ctx->reason;
    out->state_changed = ctx->changed;
    ctx->changed = false;
}

void onex_rfkill_clear_fault(onex_rfkill_t *ctx)
{
    if (ctx == NULL || ctx->state != ONEX_RFKILL_FAULT) {
        return;
    }
    invalidate_nonce(ctx);
    ctx->state = ONEX_RFKILL_ENGAGED;   /* nie direkt nach RELEASED */
    ctx->reason = ONEX_RFK_R_FAULT_CLEARED;
    ctx->changed = true;
}

onex_rfkill_state_t onex_rfkill_state(const onex_rfkill_t *ctx)
{
    return (ctx == NULL) ? ONEX_RFKILL_ENGAGED : ctx->state;
}

bool onex_rfkill_is_active(const onex_rfkill_t *ctx)
{
    /* "Kill aktiv" = alles ausser RELEASED. NULL -> sicherer Default. */
    return (ctx == NULL) || (ctx->state != ONEX_RFKILL_RELEASED);
}
