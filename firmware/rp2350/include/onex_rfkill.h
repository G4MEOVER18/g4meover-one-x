/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X RF-Kill — Zustandsautomat des sicherheitskritischsten Moduls
 * (ONEX_MOD_RF_KILL, Prioritaet 0 im Superloop).
 *
 * Verbindliche Vorgaben:
 *   - firmware/rp2350/ARCHITECTURE.md 5 (Sicherheits-Grundsatz)
 *   - firmware/rp2350/PROTOCOL.md 4 (RF-Kill-Semantik)
 *   - hardware/rf-core/schematic/sheet_01_supervisor_rfkill.md (HW-Gate)
 *
 * ABGRENZUNG — was dieses Modul NICHT ist:
 * Der TX-Disable-Pfad ist HARDWARE-erzwungen. Diese Zustandsmaschine ersetzt
 * ihn nicht, sie steuert und ueberwacht ihn. Ein hoerender RP2350 oder ein
 * korrumpierter Zustand hier laesst die Hardware im sicheren Zustand (Kill),
 * weil jedes PA/TX-Enable per Pull Richtung Kill gezogen ist.
 *
 * Pin-/HAL-frei: Ein- und Ausgaenge sind reine Werte, keine GPIO-Zugriffe.
 * Alle Pin-Zuordnungen bleiben HOLD bis Gate G07. Dadurch ist das Modul
 * vollstaendig auf dem Host testbar (tools/fw_test.py).
 */
#ifndef ONEX_RFKILL_H
#define ONEX_RFKILL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ONEX_RFKILL_TOKEN_LEN 8u

/*
 * Zeitkonstanten — Status TARGET (abstimmbar), nicht FIXED.
 * Owner-Entscheidung 2026-09-07: Link-Verlust => Karenzzeit, dann Kill.
 */
#ifndef ONEX_RFKILL_LINK_GRACE_MS
/* Karenz nach letztem Lebenszeichen des RK3576, bevor der Kill greift.
 * Kurze Aussetzer (Scheduling, Suspend-Uebergang) sollen eine laufende,
 * autorisierte Messung nicht abwuergen; ein echter Absturz aber schon. */
#define ONEX_RFKILL_LINK_GRACE_MS 3000u
#endif

#ifndef ONEX_RFKILL_ARM_TTL_MS
/* Gueltigkeitsfenster nach der physischen Nutzergeste. Danach verfaellt das
 * Nonce und eine erneute Geste ist noetig ("bewusste Freigabe" bleibt frisch). */
#define ONEX_RFKILL_ARM_TTL_MS 10000u
#endif

/* --- Zustaende --------------------------------------------------------- */
typedef enum {
    /* Kill aktiv, TX gesperrt. Default nach Boot/Reset/Fault. */
    ONEX_RFKILL_ENGAGED = 0,
    /* Nutzergeste erkannt, Nonce ausgegeben, Freigabe waere moeglich.
     * ACHTUNG: TX ist hier weiterhin GESPERRT -- nur ein Zeitfenster. */
    ONEX_RFKILL_ARMED,
    /* TX physisch freigegeben. */
    ONEX_RFKILL_RELEASED,
    /* Gate-Diskrepanz o.ae.: Kill erzwungen und GELATCHT. Verlaesst diesen
     * Zustand nur ueber onex_rfkill_clear_fault() (bewusster Eingriff). */
    ONEX_RFKILL_FAULT,
} onex_rfkill_state_t;

/* --- Gruende (EVT_RFKILL.reason) --------------------------------------- */
typedef enum {
    ONEX_RFK_R_BOOT_DEFAULT = 0, /* sicherer Startzustand */
    ONEX_RFK_R_HOST_REQUEST,     /* CMD_RFKILL_SET engage=1 */
    ONEX_RFK_R_USER_RELEASE,     /* Freigabe mit gueltiger Geste + Token */
    ONEX_RFK_R_LINK_LOSS,        /* Karenzzeit abgelaufen */
    ONEX_RFK_R_POLICY_DENIED,    /* Freigabe abgelehnt */
    ONEX_RFK_R_ARM_EXPIRED,      /* Zeitfenster verfallen */
    ONEX_RFK_R_GATE_MISMATCH,    /* TX_GATE_OK widerspricht dem Befehl */
    ONEX_RFK_R_EMERGENCY_SW,     /* physischer Notfall-Kill */
    ONEX_RFK_R_FAULT_ESCALATION, /* anderes safety-critical Modul im Fault */
    ONEX_RFK_R_USER_GESTURE,     /* Uebergang ENGAGED -> ARMED */
    ONEX_RFK_R_FAULT_CLEARED,    /* bewusster Fault-Reset */
} onex_rfkill_reason_t;

/* --- Ergebnis einer Freigabe-Anfrage ----------------------------------- */
typedef enum {
    ONEX_RFK_REQ_OK = 0,          /* -> ACK */
    ONEX_RFK_REQ_DENIED_POLICY,   /* -> NACK(ONEX_NACK_POLICY) */
    ONEX_RFK_REQ_DENIED_FAULT,    /* -> NACK(ONEX_NACK_POLICY), Fault gelatcht */
    ONEX_RFK_REQ_BADARG,          /* -> NACK(ONEX_NACK_BADARG) */
} onex_rfkill_req_result_t;

/*
 * Eingaenge, die der Superloop pro tick liefert. Bewusst Werte statt Callbacks:
 * die HAL liest die Pins, dieses Modul entscheidet.
 */
typedef struct {
    /* Rueckmeldung des HW-Gates (Netz TX_GATE_OK): TX ist PHYSISCH frei.
     * Das ist die einzige Wahrheit -- nicht das, was wir befohlen haben. */
    bool tx_gate_ok;
    /* Physischer Notfall-Kill (Netz RF_KILL_SW_n, entprellt). */
    bool emergency_switch;
    /* Ein Regulierungsprofil (Region/Baender/Leistung) ist aktiv und gueltig. */
    bool regulatory_profile_valid;
    /* Ein anderes safety-critical Modul meldet Fault (power/watchdog). */
    bool system_fault;
} onex_rfkill_inputs_t;

/* Ausgabe eines ticks: was die HAL setzen soll + ob ein Event zu senden ist. */
typedef struct {
    /* Sollzustand fuer das HW-Gate. false = Kill aktiv (TX gesperrt). */
    bool tx_enable;
    /* true, wenn sich der Zustand geaendert hat -> EVT_RFKILL senden. */
    bool state_changed;
    onex_rfkill_state_t  state;
    onex_rfkill_reason_t reason;
} onex_rfkill_output_t;

/*
 * Kontext. Der Aufrufer haelt ihn statisch; kein malloc.
 * Felder sind privat -- nur ueber die Funktionen unten anfassen.
 */
typedef struct {
    onex_rfkill_state_t  state;
    onex_rfkill_reason_t reason;

    uint32_t last_link_ms;    /* letztes Lebenszeichen des RK3576 */
    uint32_t armed_at_ms;     /* Zeitpunkt der Nutzergeste */
    bool     link_seen;       /* je ein Lebenszeichen erhalten? */
    bool     changed;         /* Flankenmerker fuer den naechsten tick */

    uint8_t  nonce[ONEX_RFKILL_TOKEN_LEN];
    bool     nonce_valid;

    uint32_t (*rand32)(void); /* Entropiequelle (RP2350: HW-RNG) */

    uint32_t grace_ms;
    uint32_t arm_ttl_ms;
} onex_rfkill_t;

/*
 * Initialisierung. Startet IMMER in ONEX_RFKILL_ENGAGED (Kill aktiv) --
 * unabhaengig davon, was vor einem Reset galt.
 *
 * rand32 darf NULL sein; dann kann kein Nonce ausgegeben werden und jede
 * Freigabe wird abgelehnt (fail-safe statt vorhersagbares Token).
 */
void onex_rfkill_init(onex_rfkill_t *ctx, uint32_t (*rand32)(void));

/* Optional: Zeitkonstanten ueberschreiben (Tests, Feldabstimmung). */
void onex_rfkill_configure(onex_rfkill_t *ctx, uint32_t grace_ms, uint32_t arm_ttl_ms);

/* Lebenszeichen vom RK3576 (jeder gueltig dekodierte Frame). Setzt die Karenz zurueck. */
void onex_rfkill_note_link(onex_rfkill_t *ctx, uint32_t now_ms);

/*
 * Physische Nutzergeste am Geraet (Taste/Ring) -- vom buttons/touch_ring-Modul.
 * Oeffnet das Freigabefenster: ENGAGED -> ARMED, Nonce wird erzeugt.
 * Im FAULT-Zustand wirkungslos (Fault muss bewusst geloescht werden).
 */
void onex_rfkill_note_gesture(onex_rfkill_t *ctx, uint32_t now_ms);

/*
 * Aktuelles Nonce lesen (Host holt es per CMD_GET und spiegelt es im token).
 * false, wenn keins gueltig ist. out muss ONEX_RFKILL_TOKEN_LEN gross sein.
 */
bool onex_rfkill_nonce(const onex_rfkill_t *ctx, uint8_t *out);

/*
 * CMD_RFKILL_SET.
 *
 * engage=true  : Kill. Wird IMMER und SOFORT ausgefuehrt -- ohne Token, ohne
 *                Regulierungsprofil, in jedem Zustand. Absichtlich asymmetrisch:
 *                Sicherheit darf nie an einer Pruefung scheitern.
 * engage=false : Freigabe-ANFRAGE. Nur erfolgreich, wenn ALLES zutrifft:
 *                  (a) Zustand ist ARMED (physische Geste liegt vor),
 *                  (b) Zeitfenster nicht abgelaufen,
 *                  (c) Regulierungsprofil gueltig,
 *                  (d) token == aktuelles Nonce (konstantzeitiger Vergleich),
 *                  (e) kein system_fault, kein Notfallschalter.
 *                Das Nonce ist danach in JEDEM Fall verbraucht (One-Shot) --
 *                auch bei Ablehnung, sonst waere es ratbar.
 *
 * token darf bei engage=true NULL sein.
 */
onex_rfkill_req_result_t onex_rfkill_request(onex_rfkill_t *ctx,
                                             bool engage,
                                             const uint8_t *token,
                                             const onex_rfkill_inputs_t *in,
                                             uint32_t now_ms);

/*
 * Superloop-Schritt. Wertet Karenzzeit, Zeitfenster, Notfallschalter,
 * System-Fault und die Gate-Rueckmeldung aus.
 * Muss < 200 us bleiben (Modul-Vertrag) -- ist schleifenfrei.
 */
void onex_rfkill_tick(onex_rfkill_t *ctx,
                      const onex_rfkill_inputs_t *in,
                      uint32_t now_ms,
                      onex_rfkill_output_t *out);

/* Bewusstes Loeschen des gelatchten FAULT-Zustands. Fuehrt nach ENGAGED, nie
 * direkt nach RELEASED -- eine Freigabe erfordert danach erneut eine Geste. */
void onex_rfkill_clear_fault(onex_rfkill_t *ctx);

/* Aktueller Zustand / Heartbeat-Flag (ONEX_HB_RFKILL_ACTIVE). */
onex_rfkill_state_t onex_rfkill_state(const onex_rfkill_t *ctx);
bool onex_rfkill_is_active(const onex_rfkill_t *ctx);

#ifdef __cplusplus
}
#endif
#endif /* ONEX_RFKILL_H */
