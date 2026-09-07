/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X rk3576_link — Protokoll-Endpunkt des System-Managers.
 * Fuehrt den Frame-Codec (onex_proto) und den RF-Kill-Automaten
 * (onex_rfkill) zu einem bedienbaren Link zusammen.
 *
 * Referenzen:
 *   - firmware/rp2350/PROTOCOL.md (Framing, Nachrichten-Set, Zuverlaessigkeit)
 *   - firmware/rp2350/ARCHITECTURE.md 2 (Modul rk3576_link)
 *
 * Aufgaben:
 *   RX: Bytestrom -> Frames -> Kommandos ausfuehren -> ACK/NACK
 *   TX: Events/Telemetrie mit eigener SEQ, Heartbeat im Takt
 *
 * Pin-/HAL-frei: Der Transport (UART primaer, SPI optional -- Busauswahl ist
 * HOLD bis G07) wird ueber einen Schreib-Callback angebunden. Dadurch ist der
 * gesamte Endpunkt auf dem Host testbar (tools/fw_test.py).
 */
#ifndef ONEX_LINK_H
#define ONEX_LINK_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "onex_proto.h"
#include "onex_rfkill.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * RX-Puffer. Zwei Maximalframes: einer kann vollstaendig vorliegen, waehrend
 * der naechste schon hereinlaeuft. Groesser bringt nichts -- der Decoder
 * arbeitet frameweise und der Puffer wird nach jedem Frame kompaktiert.
 */
#define ONEX_LINK_RX_BUF (ONEX_MAX_FRAME * 2u)

#ifndef ONEX_LINK_HEARTBEAT_MS
/* Heartbeat-Takt (PROTOCOL.md 3: ~1 Hz). TARGET, nicht FIXED. */
#define ONEX_LINK_HEARTBEAT_MS 1000u
#endif

/*
 * Senke fuer ausgehende Bytes. Der Aufrufer schiebt sie in den UART/SPI.
 * Darf nicht blockieren (Modul-Vertrag: tick < 200 us).
 */
typedef void (*onex_link_write_fn)(const uint8_t *data, size_t len, void *user);

/*
 * Delegat fuer Kommandos, die dieses Modul nicht selbst abschliesst
 * (POWER, FAN, HAPTIC, STATUS_LED, RECOVERY, TIME_SYNC).
 *
 * Rueckgabe: ONEX_NACK_OK -> ACK, sonst NACK mit diesem Grund.
 * Ist kein Delegat registriert, antwortet der Link mit NACK(BUSY) --
 * ehrlich, denn die zustaendigen Module existieren in Phase 2 noch nicht.
 */
typedef uint8_t (*onex_link_cmd_fn)(uint8_t type, const uint8_t *payload,
                                    uint8_t len, void *user);

/* Zaehler fuer Diagnose/Feldanalyse (EVT_FAULT-Bewertung, Bringup). */
typedef struct {
    uint32_t frames_ok;
    uint32_t crc_errors;
    uint32_t version_errors;
    uint32_t unknown_cmds;
    uint32_t duplicates;      /* per Cache beantwortete Wiederholungen */
    uint32_t rx_overruns;     /* Puffer voll ohne verwertbaren Frame */
} onex_link_stats_t;

typedef struct {
    uint8_t  rx[ONEX_LINK_RX_BUF];
    size_t   rx_len;

    uint8_t  tx_seq;          /* eigene SEQ fuer Events (Mgr -> Host) */

    /*
     * Duplikat-Cache (At-Most-Once).
     * PROTOCOL.md 2 laesst den Host bei Timeout wiederholen. Ohne diesen Cache
     * wuerde eine Wiederholung das Kommando ERNEUT ausfuehren -- fatal beim
     * RF-Kill, dessen Nonce One-Shot ist: das verlorene ACK wuerde zu
     * NACK(policy) fuehren, obwohl die Freigabe laengst erfolgt ist.
     */
    bool     have_last;
    uint8_t  last_seq;
    uint8_t  last_type;       /* Kommandotyp, zu dem die Antwort gehoert */
    uint8_t  last_resp;       /* ONEX_ACK oder ONEX_NACK */
    uint8_t  last_status;     /* status bzw. reason */

    uint32_t boot_ms;
    uint32_t last_hb_ms;
    uint32_t hb_period_ms;
    bool     hb_primed;

    uint8_t  sys_state;       /* ONEX_STATE_* fuer den Heartbeat */

    onex_rfkill_t     *rfk;   /* darf NULL sein (dann kein RF-Kill-Dienst) */
    onex_rfkill_state_t rfk_last_state;

    onex_link_write_fn write;
    void              *write_user;
    onex_link_cmd_fn   cmd;
    void              *cmd_user;

    onex_link_stats_t stats;
} onex_link_t;

/*
 * Initialisierung. write darf nicht NULL sein (sonst ist der Link stumm).
 * rfk darf NULL sein; dann werden RF-Kill-Kommandos mit NACK(BUSY) beantwortet.
 */
void onex_link_init(onex_link_t *lnk,
                    onex_rfkill_t *rfk,
                    onex_link_write_fn write, void *write_user,
                    uint32_t now_ms);

/* Optionaler Delegat fuer Kommandos anderer Module. */
void onex_link_set_command_handler(onex_link_t *lnk, onex_link_cmd_fn fn, void *user);

/* Heartbeat-Takt setzen (Tests/Abstimmung). */
void onex_link_set_heartbeat_period(onex_link_t *lnk, uint32_t period_ms);

/* Systemzustand fuer EVT_HEARTBEAT.state melden (vom power-Modul). */
void onex_link_set_system_state(onex_link_t *lnk, uint8_t state);

/*
 * Empfangene Bytes einspeisen. Beliebige Stueckelung -- auch byteweise.
 * Vollstaendige Frames werden sofort verarbeitet und beantwortet.
 */
void onex_link_rx(onex_link_t *lnk, const onex_rfkill_inputs_t *in,
                  const uint8_t *data, size_t len, uint32_t now_ms);

/*
 * Superloop-Schritt: Heartbeat senden, RF-Kill-Zustandswechsel als
 * EVT_RFKILL melden. Ruft NICHT onex_rfkill_tick() -- das macht das
 * rf_kill-Modul selbst (Prioritaet 0, laeuft frueher im Superloop).
 */
void onex_link_tick(onex_link_t *lnk, uint32_t now_ms);

/* Ein Event/Telemetrie senden (eigene SEQ, fire-and-forget). */
void onex_link_send_event(onex_link_t *lnk, uint8_t type,
                          const uint8_t *payload, uint8_t len);

const onex_link_stats_t *onex_link_stats(const onex_link_t *lnk);

#ifdef __cplusplus
}
#endif
#endif /* ONEX_LINK_H */
