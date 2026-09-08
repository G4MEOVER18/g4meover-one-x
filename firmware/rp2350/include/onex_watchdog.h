/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X watchdog — Gesundheitswaechter des Superloops.
 * Modul ONEX_MOD_WATCHDOG (safety-critical, Prioritaet 2).
 *
 * Referenz: firmware/rp2350/ARCHITECTURE.md 4
 *   "watchdog.tick kickt den HW-Watchdog NUR, wenn alle safety-critical
 *    Module im letzten Zyklus OK meldeten."
 *
 * KERNGEDANKE — die Wirkung liegt im Unterlassen:
 * Dieses Modul kann nichts abschalten. Seine einzige Macht ist, den
 * Hardware-Watchdog NICHT mehr zu fuettern; der loest dann einen Reset aus,
 * und nach dem Reset startet die Firmware im sicheren Default (RF-Kill an,
 * Rails aus). Deshalb ist der gefaehrliche Fehler nicht "kickt zu selten",
 * sondern "kickt weiter, obwohl etwas kaputt ist".
 *
 * Daraus folgt die Grundregel: Im Zweifel NICHT kicken. Jeder unbekannte,
 * veraltete oder fehlende Zustand gilt als ungesund.
 *
 * Pin-/HAL-frei: Der eigentliche HW-Kick passiert beim Aufrufer, wenn dieses
 * Modul ihn erlaubt. Alle Pin-Zuordnungen bleiben HOLD bis Gate G07.
 */
#ifndef ONEX_WATCHDOG_H
#define ONEX_WATCHDOG_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>   /* NULL -- glibc zieht es nicht ueber <stdint.h> mit */

#include "onex_modules.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifndef ONEX_WD_REPORT_TIMEOUT_MS
/*
 * Frist, in der ein kritisches Modul sich gemeldet haben muss. Laeuft sie ab,
 * gilt das Modul als haengend -- gleichwertig zu einem Fault. Faengt genau den
 * Fall, den ein reiner Fehlerzaehler NICHT faengt: ein Modul, das gar nichts
 * mehr sagt. TARGET.
 */
#define ONEX_WD_REPORT_TIMEOUT_MS 250u
#endif

#ifndef ONEX_WD_STARTUP_GRACE_MS
/*
 * Startkarenz. Direkt nach dem Reset hat noch kein Modul gemeldet -- ohne
 * Karenz wuerde der Watchdog sofort erneut resetten und das Geraet kaeme nie
 * hoch (Reset-Schleife). Bewusst kurz und begrenzt: sie endet, sobald jedes
 * kritische Modul einmal gemeldet hat, spaetestens nach dieser Zeit. TARGET.
 */
#define ONEX_WD_STARTUP_GRACE_MS 2000u
#endif

typedef struct {
    /* true = der Aufrufer darf den HW-Watchdog jetzt fuettern. */
    bool     kick;
    /* true = mindestens ein kritisches Modul ist ungesund -> eskalieren. */
    bool     escalate;
    /* Erstes als ungesund erkanntes Modul (onex_module_id_t) -- Diagnose. */
    uint8_t  culprit;
    /* true, solange die Startkarenz laeuft (kick ohne vollstaendige Meldung). */
    bool     in_startup_grace;
} onex_watchdog_output_t;

typedef struct {
    uint8_t  health[ONEX_MOD_COUNT];      /* onex_health_t */
    uint32_t last_report_ms[ONEX_MOD_COUNT];
    bool     reported[ONEX_MOD_COUNT];

    uint32_t critical_mask;               /* Bit i = Modul i ist kritisch */
    uint32_t started_ms;
    uint32_t report_timeout_ms;
    uint32_t grace_ms;
    bool     latched_fault;               /* einmal ungesund -> bleibt es */
} onex_watchdog_t;

/*
 * Initialisierung. Kritisch sind per Vorgabe rf_kill, power und watchdog
 * selbst (ARCHITECTURE.md 2). Alle Module starten als "noch nicht gemeldet".
 */
void onex_watchdog_init(onex_watchdog_t *wd, uint32_t now_ms);

/* Kritische Module ueberschreiben (Bitmaske ueber onex_module_id_t). */
void onex_watchdog_set_critical(onex_watchdog_t *wd, uint32_t mask);

/* Fristen setzen (Tests, Abstimmung). */
void onex_watchdog_configure(onex_watchdog_t *wd, uint32_t report_timeout_ms,
                             uint32_t grace_ms);

/* Ein Modul meldet seine Gesundheit (Rueckgabe von module.tick). */
void onex_watchdog_report(onex_watchdog_t *wd, onex_module_id_t id,
                          onex_health_t health, uint32_t now_ms);

/*
 * Auswertung. Liefert, ob gekickt werden darf.
 * DEGRADED gilt als lauffaehig (kein Reset) -- so definiert in
 * onex_modules.h; nur FAULT und Schweigen fuehren zum Entzug des Kicks.
 */
void onex_watchdog_tick(onex_watchdog_t *wd, uint32_t now_ms,
                        onex_watchdog_output_t *out);

/* Nach behobener Ursache bewusst zuruecksetzen (nie automatisch). */
void onex_watchdog_clear(onex_watchdog_t *wd, uint32_t now_ms);

#ifdef __cplusplus
}
#endif
#endif /* ONEX_WATCHDOG_H */
