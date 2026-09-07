/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X rk3576_link — Protokoll-Endpunkt. Vertrag: ../include/onex_link.h
 *
 * Leitlinien:
 *  1. Jede Antwort spiegelt die SEQ des Kommandos -- ausser wenn die SEQ
 *     nicht vertrauenswuerdig ist (siehe CRC-Fall unten).
 *  2. Wiederholungen duerfen nie doppelt wirken (Duplikat-Cache).
 *  3. Kein Frame-Bau ohne Codec: alles laeuft ueber onex_frame_encode/decode.
 */
#include "onex_link.h"

#include <string.h>

/* ----------------------------------------------------------------- TX */

static void raw_write(onex_link_t *lnk, const uint8_t *data, size_t len)
{
    if (lnk->write != NULL && len > 0u) {
        lnk->write(data, len, lnk->write_user);
    }
}

/* Antwort auf ein Kommando: SEQ des Kommandos wird gespiegelt. */
static void send_response(onex_link_t *lnk, uint8_t resp_type,
                          uint8_t ack_seq, uint8_t status)
{
    uint8_t frame[ONEX_MAX_FRAME];
    const uint8_t pl[2] = { ack_seq, status };
    const size_t n = onex_frame_encode(resp_type, ack_seq, pl, 2u, frame);
    raw_write(lnk, frame, n);
}

void onex_link_send_event(onex_link_t *lnk, uint8_t type,
                          const uint8_t *payload, uint8_t len)
{
    if (lnk == NULL) {
        return;
    }
    uint8_t frame[ONEX_MAX_FRAME];
    /* Events tragen eine eigene, fortlaufende SEQ (PROTOCOL.md 2):
     * der Host darf Luecken erkennen, muss aber nicht quittieren. */
    const size_t n = onex_frame_encode(type, lnk->tx_seq, payload, len, frame);
    if (n > 0u) {
        lnk->tx_seq = (uint8_t)(lnk->tx_seq + 1u);   /* Wrap ist zulaessig */
        raw_write(lnk, frame, n);
    }
}

static void send_heartbeat(onex_link_t *lnk, uint32_t now_ms)
{
    uint8_t flags = 0u;
    if (lnk->rfk == NULL || onex_rfkill_is_active(lnk->rfk)) {
        /* Kein RF-Kill-Modul -> sicherheitshalber "Kill aktiv" melden.
         * Ein fehlendes Modul darf nie als "TX frei" erscheinen. */
        flags |= ONEX_HB_RFKILL_ACTIVE;
    }

    const uint32_t uptime_s = (uint32_t)(now_ms - lnk->boot_ms) / 1000u;
    const uint8_t pl[6] = {
        lnk->sys_state,
        flags,
        (uint8_t)((uptime_s >> 24) & 0xFFu),   /* big-endian, wie das CRC-Feld */
        (uint8_t)((uptime_s >> 16) & 0xFFu),
        (uint8_t)((uptime_s >> 8) & 0xFFu),
        (uint8_t)(uptime_s & 0xFFu),
    };
    onex_link_send_event(lnk, ONEX_EVT_HEARTBEAT, pl, 6u);
}

static void send_rfkill_event(onex_link_t *lnk)
{
    if (lnk->rfk == NULL) {
        return;
    }
    const uint8_t pl[2] = {
        (uint8_t)onex_rfkill_state(lnk->rfk),
        (uint8_t)0u,   /* Grund wird vom rf_kill-Modul ueber tick() geliefert */
    };
    onex_link_send_event(lnk, ONEX_EVT_RFKILL, pl, 2u);
}

/* ------------------------------------------------------ Kommandos */

static uint8_t handle_rfkill_set(onex_link_t *lnk,
                                 const onex_rfkill_inputs_t *in,
                                 const uint8_t *pl, uint8_t len,
                                 uint32_t now_ms)
{
    if (lnk->rfk == NULL || in == NULL) {
        return ONEX_NACK_BUSY;
    }
    /* Payload: u8 engage + u8 token[8] (PROTOCOL.md 3). Ein Kill darf auch
     * ohne Token kommen -- dafuer genuegt 1 Byte. */
    if (len < 1u) {
        return ONEX_NACK_BADARG;
    }
    const bool engage = (pl[0] != 0u);
    if (!engage && len < (1u + ONEX_RFKILL_TOKEN_LEN)) {
        return ONEX_NACK_BADARG;
    }

    const onex_rfkill_req_result_t r =
        onex_rfkill_request(lnk->rfk, engage, engage ? NULL : &pl[1], in, now_ms);

    switch (r) {
    case ONEX_RFK_REQ_OK:            return ONEX_NACK_OK;
    case ONEX_RFK_REQ_BADARG:        return ONEX_NACK_BADARG;
    case ONEX_RFK_REQ_DENIED_POLICY: /* fallthrough */
    case ONEX_RFK_REQ_DENIED_FAULT:  return ONEX_NACK_POLICY;
    default:                         return ONEX_NACK_POLICY;
    }
}

static uint8_t handle_get(onex_link_t *lnk, const uint8_t *pl, uint8_t len,
                          uint32_t now_ms)
{
    if (len < 1u) {
        return ONEX_NACK_BADARG;
    }

    switch (pl[0]) {
    case ONEX_GET_STATUS:
        send_heartbeat(lnk, now_ms);
        return ONEX_NACK_OK;

    case ONEX_GET_RFKILL:
        if (lnk->rfk == NULL) {
            return ONEX_NACK_BUSY;
        }
        send_rfkill_event(lnk);
        return ONEX_NACK_OK;

    case ONEX_GET_RFKILL_NONCE: {
        /* Die Bruecke zur Freigabe-Policy: der Host kann das Nonce nur
         * abholen, NACHDEM am Geraet eine physische Geste erkannt wurde.
         * Vorher meldet der Manager valid=0 -- kein Fehler, nur "noch nicht". */
        uint8_t pl_out[1u + ONEX_RFKILL_TOKEN_LEN];
        memset(pl_out, 0, sizeof pl_out);
        if (lnk->rfk == NULL) {
            return ONEX_NACK_BUSY;
        }
        pl_out[0] = onex_rfkill_nonce(lnk->rfk, &pl_out[1]) ? 1u : 0u;
        onex_link_send_event(lnk, ONEX_EVT_NONCE, pl_out, (uint8_t)sizeof pl_out);
        return ONEX_NACK_OK;
    }

    case ONEX_GET_BATTERY:
        /* battery-Modul existiert in Phase 2 noch nicht -> ehrlich BUSY,
         * statt eine erfundene Telemetrie zu senden. */
        return ONEX_NACK_BUSY;

    default:
        return ONEX_NACK_BADARG;
    }
}

/* Fuehrt genau EIN Kommando aus. Rueckgabe = NACK-Grund (OK => ACK). */
static uint8_t execute(onex_link_t *lnk, const onex_rfkill_inputs_t *in,
                       const onex_hdr_t *hdr, const uint8_t *pl, uint32_t now_ms)
{
    switch (hdr->type) {
    case ONEX_CMD_PING:
        return ONEX_NACK_OK;

    case ONEX_CMD_RFKILL_SET:
        return handle_rfkill_set(lnk, in, pl, hdr->len, now_ms);

    case ONEX_CMD_GET:
        return handle_get(lnk, pl, hdr->len, now_ms);

    case ONEX_CMD_POWER:
    case ONEX_CMD_FAN:
    case ONEX_CMD_HAPTIC:
    case ONEX_CMD_STATUS_LED:
    case ONEX_CMD_RECOVERY:
    case ONEX_CMD_TIME_SYNC:
        /* Zustaendige Module folgen in spaeteren Phasen. Ohne Delegat ist
         * NACK(BUSY) die ehrliche Antwort -- ein ACK wuerde eine Wirkung
         * behaupten, die es nicht gibt. */
        if (lnk->cmd == NULL) {
            return ONEX_NACK_BUSY;
        }
        return lnk->cmd(hdr->type, pl, hdr->len, lnk->cmd_user);

    default:
        lnk->stats.unknown_cmds++;
        return ONEX_NACK_UNKNOWN;
    }
}

/*
 * Ein vollstaendig dekodierter, CRC-gepruefter Frame.
 * Hier sitzt der Duplikat-Cache.
 */
static void dispatch(onex_link_t *lnk, const onex_rfkill_inputs_t *in,
                     const onex_hdr_t *hdr, const uint8_t *pl, uint32_t now_ms)
{
    /* Antworten (ACK/NACK) vom Host werden nicht erwartet -- der Manager ist
     * die antwortende Seite. Still verwerfen statt NACK(UNKNOWN) zu spiegeln,
     * sonst schaukeln sich beide Seiten hoch. */
    if (hdr->type == ONEX_ACK || hdr->type == ONEX_NACK) {
        return;
    }

    /*
     * Wiederholung erkennen: gleiche SEQ UND gleicher Typ wie zuletzt.
     * Dann die gespeicherte Antwort erneut senden, das Kommando aber NICHT
     * erneut ausfuehren.
     *
     * Der Host wiederholt bei Timeout (PROTOCOL.md 2, 3x/20 ms) -- er kann
     * ein verlorenes Kommando nicht von einer verlorenen Antwort
     * unterscheiden. Ohne Cache wirkt jede Wiederholung ein zweites Mal.
     * Am teuersten bei nicht-idempotenten Kommandos: ein wiederholtes
     * CMD_POWER (reboot/shutdown) oder CMD_RECOVERY darf sich nicht doppeln.
     *
     * Beim RF-Kill kommt der Cache als ZWEITE Sicherung dazu -- der Automat
     * beantwortet eine Freigabe im Zustand RELEASED bereits selbst idempotent
     * (onex_rfkill.c). Beide Ebenen zusammen halten Host und Manager auch bei
     * verlorenem ACK auf derselben Vorstellung vom TX-Zustand.
     */
    if (lnk->have_last && lnk->last_seq == hdr->seq && lnk->last_type == hdr->type) {
        lnk->stats.duplicates++;
        send_response(lnk, lnk->last_resp, hdr->seq, lnk->last_status);
        return;
    }

    const uint8_t status = execute(lnk, in, hdr, pl, now_ms);
    const uint8_t resp = (status == ONEX_NACK_OK) ? ONEX_ACK : ONEX_NACK;

    lnk->have_last = true;
    lnk->last_seq = hdr->seq;
    lnk->last_type = hdr->type;
    lnk->last_resp = resp;
    lnk->last_status = status;

    send_response(lnk, resp, hdr->seq, status);
}

/* ----------------------------------------------------------------- RX */

static void consume(onex_link_t *lnk, size_t n)
{
    if (n >= lnk->rx_len) {
        lnk->rx_len = 0u;
        return;
    }
    memmove(lnk->rx, &lnk->rx[n], lnk->rx_len - n);
    lnk->rx_len -= n;
}

static void drain(onex_link_t *lnk, const onex_rfkill_inputs_t *in, uint32_t now_ms)
{
    /*
     * Schleifengrenze: jeder Durchlauf konsumiert mindestens ein Byte oder
     * bricht ab. Die Obergrenze ist die Puffergroesse -- damit bleibt der
     * tick beschraenkt (Modul-Vertrag), auch bei voellig zerhacktem Strom.
     */
    for (size_t guard = 0; guard < ONEX_LINK_RX_BUF; ++guard) {
        onex_hdr_t hdr;
        const uint8_t *pl = NULL;
        const int r = onex_frame_decode(lnk->rx, lnk->rx_len, &hdr, &pl);

        if (r > 0) {
            lnk->stats.frames_ok++;
            /*
             * Jeder gueltige Frame ist ein Lebenszeichen des RK3576 und setzt
             * die RF-Kill-Karenz zurueck (Owner-Entscheidung 2026-09-07).
             */
            if (lnk->rfk != NULL) {
                onex_rfkill_note_link(lnk->rfk, now_ms);
            }
            dispatch(lnk, in, &hdr, pl, now_ms);
            consume(lnk, (size_t)r);
            continue;
        }

        if (r == ONEX_DEC_ERR_VERSION) {
            /*
             * Die SEQ ist hier CRC-gedeckt (onex_proto prueft CRC VOR Version),
             * also darf sie gespiegelt werden -- genau dafuer ist die
             * Pruefreihenfolge so gewaehlt.
             */
            lnk->stats.version_errors++;
            send_response(lnk, ONEX_NACK, hdr.seq, ONEX_NACK_VERSION);
            consume(lnk, onex_frame_resync(lnk->rx, lnk->rx_len));
            continue;
        }

        if (r == ONEX_DEC_ERR_CRC) {
            /*
             * BEWUSST KEINE ANTWORT.
             * Bei CRC-Fehler ist kein Header-Feld vertrauenswuerdig -- auch
             * die SEQ nicht. Ein NACK mit geratener SEQ koennte beim Host ein
             * ganz anderes, noch offenes Kommando als abgelehnt markieren.
             * Der Host laeuft stattdessen in seinen Timeout und wiederholt
             * (PROTOCOL.md 2). Der Zaehler bleibt fuer die Diagnose.
             */
            lnk->stats.crc_errors++;
            consume(lnk, onex_frame_resync(lnk->rx, lnk->rx_len));
            continue;
        }

        /* r == 0: unvollstaendig. */
        if (lnk->rx_len >= ONEX_LINK_RX_BUF) {
            /*
             * Puffer voll, aber kein verwertbarer Frame: der Strom ist so
             * zerstoert, dass Warten nichts bringt. Resync statt Blockade --
             * ein stillstehender Link waere schlimmer als Datenverlust.
             */
            lnk->stats.rx_overruns++;
            const size_t skip = onex_frame_resync(lnk->rx, lnk->rx_len);
            consume(lnk, (skip > 0u) ? skip : 1u);   /* immer Fortschritt */
            continue;
        }
        break;   /* auf mehr Bytes warten */
    }
}

void onex_link_rx(onex_link_t *lnk, const onex_rfkill_inputs_t *in,
                  const uint8_t *data, size_t len, uint32_t now_ms)
{
    if (lnk == NULL || data == NULL) {
        return;
    }

    size_t off = 0u;
    while (off < len) {
        const size_t space = ONEX_LINK_RX_BUF - lnk->rx_len;
        size_t chunk = len - off;
        if (chunk > space) {
            chunk = space;
        }
        if (chunk > 0u) {
            memcpy(&lnk->rx[lnk->rx_len], &data[off], chunk);
            lnk->rx_len += chunk;
            off += chunk;
        }
        /* Verarbeiten -- schafft wieder Platz fuer den Rest der Eingabe. */
        drain(lnk, in, now_ms);

        if (chunk == 0u && lnk->rx_len >= ONEX_LINK_RX_BUF) {
            /* drain konnte nichts freimachen: Notbremse gegen Endlosschleife. */
            consume(lnk, 1u);
            lnk->stats.rx_overruns++;
        }
    }
}

/* --------------------------------------------------------------- Takt */

void onex_link_tick(onex_link_t *lnk, uint32_t now_ms)
{
    if (lnk == NULL) {
        return;
    }

    /* RF-Kill-Zustandswechsel melden. Der Vergleich laeuft hier, damit auch
     * Wechsel gemeldet werden, die nicht ueber ein Kommando kamen
     * (Link-Verlust, Notfallschalter, Gate-Diskrepanz). */
    if (lnk->rfk != NULL) {
        const onex_rfkill_state_t st = onex_rfkill_state(lnk->rfk);
        if (st != lnk->rfk_last_state) {
            lnk->rfk_last_state = st;
            send_rfkill_event(lnk);
        }
    }

    /* Wrap-sichere Differenz (uint32-ms laufen nach ~49,7 Tagen ueber). */
    if (!lnk->hb_primed || (uint32_t)(now_ms - lnk->last_hb_ms) >= lnk->hb_period_ms) {
        lnk->hb_primed = true;
        lnk->last_hb_ms = now_ms;
        send_heartbeat(lnk, now_ms);
    }
}

/* --------------------------------------------------------------- Setup */

void onex_link_init(onex_link_t *lnk,
                    onex_rfkill_t *rfk,
                    onex_link_write_fn write, void *write_user,
                    uint32_t now_ms)
{
    if (lnk == NULL) {
        return;
    }
    memset(lnk, 0, sizeof *lnk);
    lnk->rfk = rfk;
    lnk->write = write;
    lnk->write_user = write_user;
    lnk->boot_ms = now_ms;
    lnk->last_hb_ms = now_ms;
    lnk->hb_period_ms = ONEX_LINK_HEARTBEAT_MS;
    lnk->hb_primed = false;    /* erster tick sendet sofort einen Heartbeat */
    lnk->sys_state = ONEX_STATE_BOOT;
    lnk->rfk_last_state = (rfk != NULL) ? onex_rfkill_state(rfk) : ONEX_RFKILL_ENGAGED;
}

void onex_link_set_command_handler(onex_link_t *lnk, onex_link_cmd_fn fn, void *user)
{
    if (lnk != NULL) {
        lnk->cmd = fn;
        lnk->cmd_user = user;
    }
}

void onex_link_set_heartbeat_period(onex_link_t *lnk, uint32_t period_ms)
{
    if (lnk != NULL && period_ms > 0u) {
        lnk->hb_period_ms = period_ms;
    }
}

void onex_link_set_system_state(onex_link_t *lnk, uint8_t state)
{
    if (lnk != NULL) {
        lnk->sys_state = state;
    }
}

const onex_link_stats_t *onex_link_stats(const onex_link_t *lnk)
{
    return (lnk == NULL) ? NULL : &lnk->stats;
}
