/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X RP2350B System-Manager — Modul-Vertrag.
 * Einheitliche Schnittstelle fuer alle Superloop-Module (siehe ARCHITECTURE.md).
 * Pin-/HAL-unabhaengig: Hardwarezugriffe kapselt spaeter eine HAL (nach Gate G07).
 */
#ifndef ONEX_MODULES_H
#define ONEX_MODULES_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Modul-IDs = Superloop-Reihenfolge = Sicherheitsprioritaet (0 zuerst). */
typedef enum {
    ONEX_MOD_RF_KILL = 0,   /* safety-critical */
    ONEX_MOD_POWER,         /* safety-critical */
    ONEX_MOD_WATCHDOG,      /* safety-critical */
    ONEX_MOD_BATTERY,
    ONEX_MOD_FAN,
    ONEX_MOD_SENSORS,
    ONEX_MOD_BUTTONS,
    ONEX_MOD_TOUCH_RING,
    ONEX_MOD_HAPTIC,
    ONEX_MOD_RK3576_LINK,
    ONEX_MOD_RECOVERY,
    ONEX_MOD_PROTOCOL,
    ONEX_MOD_COUNT
} onex_module_id_t;

/* Modul-Gesundheit — von watchdog ausgewertet. */
typedef enum {
    ONEX_HEALTH_OK = 0,
    ONEX_HEALTH_DEGRADED,   /* laeuft, aber eingeschraenkt (kein Reset) */
    ONEX_HEALTH_FAULT,      /* -> System nach FAULT eskalieren */
} onex_health_t;

/* Interne Event-Weitergabe (z.B. buttons -> haptic, power -> rf_kill). */
typedef struct {
    uint8_t  source;   /* onex_module_id_t */
    uint8_t  kind;     /* modul-definiert */
    uint16_t a;
    uint32_t b;
} onex_event_t;

/*
 * Modul-Vertrag. Jedes Modul stellt eine statische Instanz bereit.
 *  init : einmalig beim Start; false => Modul deaktiviert/Fault.
 *  tick : jeder Superloop-Durchlauf; MUSS < 200 us bleiben, nie blockieren.
 *         Rueckgabe = aktuelle Gesundheit.
 *  event: optionale Behandlung interner Events (darf NULL sein).
 *  is_safety_critical: watchdog kickt nur, wenn alle kritischen Module OK sind.
 */
typedef struct {
    onex_module_id_t id;
    const char      *name;
    bool             is_safety_critical;

    bool          (*init)(void);
    onex_health_t (*tick)(uint64_t now_us);
    void          (*event)(const onex_event_t *ev);
} onex_module_t;

/* Vom Scheduler bereitgestellt: Event an ein Modul / broadcast. */
void onex_post_event(const onex_event_t *ev);

/* Registrierungstabelle (in Superloop-Reihenfolge), vom Scheduler genutzt. */
extern const onex_module_t *const onex_modules[ONEX_MOD_COUNT];

#ifdef __cplusplus
}
#endif
#endif /* ONEX_MODULES_H */
