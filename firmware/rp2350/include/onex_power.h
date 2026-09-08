/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X power — Rail-Sequencing und System-Zustandsmaschine.
 * Modul ONEX_MOD_POWER (safety-critical, Prioritaet 1 im Superloop).
 *
 * Referenzen:
 *   - firmware/rp2350/ARCHITECTURE.md 3 (System-Zustandsmaschine)
 *   - hardware/mainboard/schematic/sheet_01_power_tree.md (Rails, Sequencing)
 *
 * ABGRENZUNG (HOLD-Disziplin):
 * Die RK806S-**Rail-Map** (welche RK3576-Rails in welcher Reihenfolge, mit
 * welchen Spannungen) ist HOLD -- sie braucht die Rockchip-Referenz. Dieses
 * Modul sequenziert deshalb ausschliesslich die Board-Ebene, die im
 * Power-Tree feststeht, und behandelt den PMIC als Black-Box mit genau einem
 * Enable und einem Power-Good. Die HOLD-Grenze ist hier bewusst die
 * Modulgrenze -- nichts wird geraten.
 *
 * +3V3_AON ist KEIN Sequenzschritt, sondern Voraussetzung: die Rail speist
 * den RP2350B selbst (sheet_01: "immer zuerst / immer an"). Ein Controller
 * kann seine eigene Versorgung nicht sequenzieren.
 *
 * Pin-/HAL-frei: Rails werden als Werte geschaltet und als Power-Good
 * zurueckgelesen. Alle GPIO-Zuordnungen bleiben HOLD bis Gate G07.
 */
#ifndef ONEX_POWER_H
#define ONEX_POWER_H

#include <stdint.h>
#include <stdbool.h>

#include "onex_proto.h"   /* ONEX_STATE_* -- gleiche Zustaende wie im Heartbeat */

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Geschaltete Rails in Einschaltreihenfolge (sheet_01_power_tree.md).
 * Ausschalten laeuft exakt umgekehrt.
 */
typedef enum {
    ONEX_RAIL_VSYS = 0,   /* Power-Path des Chargers */
    ONEX_RAIL_5V_SYS,     /* High-Current-Buck (10 A transient) */
    ONEX_RAIL_3V3_SYS,    /* System-Buck (Logik, Radios, M.2) */
    ONEX_RAIL_PMIC,       /* RK806S-Freigabe -- interne Rail-Map HOLD */
    ONEX_RAIL_COUNT
} onex_rail_t;

/* Fehlercodes (EVT_FAULT.code). */
typedef enum {
    ONEX_PWR_FAULT_NONE = 0,
    ONEX_PWR_FAULT_RAIL_TIMEOUT,   /* Rail meldet kein Power-Good */
    ONEX_PWR_FAULT_RAIL_LOST,      /* Power-Good faellt im Betrieb weg */
    ONEX_PWR_FAULT_BROWNOUT,       /* VSYS unter Grenze */
    ONEX_PWR_FAULT_BATTERY,        /* Akku kritisch (Gauge/Schutz) */
    ONEX_PWR_FAULT_THERMAL,        /* Temperatur kritisch */
    ONEX_PWR_FAULT_AON_LOST,       /* Versorgung des Managers selbst gestoert */
    ONEX_PWR_FAULT_WATCHDOG,       /* Eskalation vom watchdog-Modul */
    ONEX_PWR_FAULT_HOST_TIMEOUT,   /* RK3576 wird im BOOT nicht lebendig */
} onex_power_fault_t;

#ifndef ONEX_PWR_RAIL_TIMEOUT_MS
/* Wartezeit auf Power-Good je Rail. TARGET -- exakte Werte folgen aus den
 * Buck-Datenblaettern (Soft-Start) nach Gate G07. Nie endlos warten. */
#define ONEX_PWR_RAIL_TIMEOUT_MS 50u
#endif

#ifndef ONEX_PWR_HOST_BOOT_TIMEOUT_MS
/* Frist, in der sich der RK3576 nach PMIC-Freigabe melden muss. TARGET. */
#define ONEX_PWR_HOST_BOOT_TIMEOUT_MS 15000u
#endif

#ifndef ONEX_PWR_BROWNOUT_MV
/* VSYS-Untergrenze. TARGET -- endgueltig nach Akku-/Charger-Charakterisierung
 * (2S: 7,2 V nominal, 8,4 V voll; sheet_01). */
#define ONEX_PWR_BROWNOUT_MV 6000u
#endif

typedef struct {
    /* Versorgung des Managers selbst. Ohne sie ist kein Bringup zulaessig. */
    bool     aon_ok;
    /* Power-Good je Rail (aus PG_*-Netzen). */
    bool     rail_pg[ONEX_RAIL_COUNT];
    /* Gemessene VSYS-Spannung fuer die Brown-out-Erkennung. */
    uint16_t vsys_mv;
    /* Der RK3576 lebt (z.B. Verkehr auf dem ONE-X-Link). */
    bool     host_alive;
    /* Harte Abschaltgruende aus battery/sensors. */
    bool     battery_critical;
    bool     thermal_critical;
} onex_power_inputs_t;

typedef struct {
    bool    rail_enable[ONEX_RAIL_COUNT];
    uint8_t state;            /* ONEX_STATE_* */
    bool    state_changed;
    uint8_t fault;            /* onex_power_fault_t */
} onex_power_output_t;

typedef struct {
    uint8_t  state;
    uint8_t  fault;
    bool     changed;

    uint8_t  seq_index;       /* aktueller Schritt der Rail-Sequenz */
    uint32_t step_started_ms;
    uint32_t host_wait_ms;
    bool     rail_on[ONEX_RAIL_COUNT];

    bool     want_suspend;
    bool     want_shutdown;
    bool     want_boot;
    bool     resume_req;

    uint32_t rail_timeout_ms;
    uint32_t host_timeout_ms;
    uint16_t brownout_mv;
} onex_power_t;

/* Startet in ONEX_STATE_OFF mit allen geschalteten Rails aus. */
void onex_power_init(onex_power_t *pw);

/* Zeit-/Schwellwerte ueberschreiben (Tests, Feldabstimmung). */
void onex_power_configure(onex_power_t *pw, uint32_t rail_timeout_ms,
                          uint32_t host_timeout_ms, uint16_t brownout_mv);

/* Anforderungen (Tasten, Host-Kommandos). Werden im naechsten tick bewertet. */
void onex_power_request_boot(onex_power_t *pw);
void onex_power_request_shutdown(onex_power_t *pw);
void onex_power_request_suspend(onex_power_t *pw);
void onex_power_request_resume(onex_power_t *pw);

/* Eskalation von aussen (watchdog, andere Module) -> FAULT. */
void onex_power_notify_fault(onex_power_t *pw, uint8_t fault_code);

/*
 * Verlaesst den gelatchten FAULT nach OFF -- bewusster Eingriff, nie
 * automatisch. Von FAULT wird nie direkt nach RUN zurueckgekehrt.
 */
void onex_power_clear_fault(onex_power_t *pw);

/* Superloop-Schritt. Schleifenfrei, < 200 us (Modul-Vertrag). */
void onex_power_tick(onex_power_t *pw, const onex_power_inputs_t *in,
                     uint32_t now_ms, onex_power_output_t *out);

uint8_t onex_power_state(const onex_power_t *pw);
/* true, wenn das System als gesund gilt (fuer den watchdog). */
bool onex_power_is_healthy(const onex_power_t *pw);

#ifdef __cplusplus
}
#endif
#endif /* ONEX_POWER_H */
