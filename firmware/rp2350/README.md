# ONE-X — RP2350B System-Manager-Firmware (`firmware/rp2350/`)

Always-On-System-Manager auf **RP2350B + 16 MB QSPI** (beides **FIXED**, Master-Spec `compute.control_mcu`). Deckt **Phase 2** der [Roadmap](../../docs/ROADMAP.md) ab: die **Modul- und Protokoll-Architektur**.

## Rolle (FIXED — Master-Spec `compute.control_role`)

> „power/wake/buttons/sensors/haptics/fans/status/debug; **NOT main Linux framebuffer**"

Der RP2350B ist ein **zweiter, von Linux unabhängiger Rechner**. Er läuft weiter, wenn der RK3576/Linux hängt, und ist die **einzige** Instanz, die den physischen **RF-Kill** und das Power-Sequencing erzwingt.

```
        ┌────────────────────────── RP2350B (Always-On) ─────────────────────────┐
Tasten ▶│ buttons  touch_ring  haptic   sensors  battery  fan   power   watchdog │
IRQ    ▶│                                                                         │
        │   rf_kill (HW-erzwungen) ──▶ physischer TX-Disable-Pfad zum RF-Core     │
        │   rk3576_link (Protokoll) ◀──UART/SPI──▶  RK3576 · Linux                │
        │   recovery (DFU/BOOTSEL)                                                │
        └─────────────────────────────────────────────────────────────────────────┘
```

## Nicht-Ziele (bewusst)
- **Kein** Linux-Framebuffer/Display-Treiber (das macht der RK3576 direkt über MIPI-DSI, siehe [`../../linux/`](../../linux/)).
- **Keine** High-Level-RF-Protokolle (die laufen als Linux-SW auf dem RK3576 bzw. auf FPGA/RF-ICs).
- **Kein** Netzwerk/Storage.

## Statusdisziplin
- **FIXED:** MCU (RP2350B), QSPI (16 MB), Rolle, RF-Kill = physisch/softwareunabhängig, Modul-Set.
- **HOLD:** **alle** GPIO-/Pin-/Bus-Zuordnungen (hängen vom Mainboard-Schaltplan ab → Gate G07). Deshalb definiert diese Phase **pin-unabhängige** Verträge, keine Pinmaps.
- **TARGET:** konkrete Sensor-/Haptik-/Fan-Bauteile.

## Inhalt

| Datei | Inhalt |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Ausführungsmodell (kooperativ, Always-On), Zustandsmaschine, Modul-Landkarte |
| [`PROTOCOL.md`](PROTOCOL.md) | RK3576 ↔ RP2350-Link: Framing, CRC, Nachrichten-Set, RF-Kill-Semantik |
| [`include/onex_proto.h`](include/onex_proto.h) | C-Header: Frame-/Nachrichtendefinition (pin-unabhängig, implementierbar) |
| [`include/onex_modules.h`](include/onex_modules.h) | C-Header: Modul-Vertrag (`init`/`tick`/`event`) + Modul-Enum |
| [`src/onex_proto.c`](src/onex_proto.c) | **Implementierung** des Frame-Codecs (CRC-16, Encode, Decode, Resync) |
| [`test/test_onex_proto.c`](test/test_onex_proto.c) | Host-Unit-Tests — frieren das Wire-Format als Regressionsschranke ein |

## Was hier schon *verifiziert* ist

Die hardware-unabhängige Schicht wird **auf dem Host kompiliert und getestet** — lange bevor es EVT-Hardware gibt:

```
python tools/fw_test.py        # bauen + ausführen (Teil von tools/check_all.py)
```

Das geht, weil der Codec bewusst **frei von Pin-/HAL-Annahmen** ist (alle GPIO-Zuordnungen sind HOLD bis Gate G07). Übersetzt wird mit `-Wall -Wextra -Werror -Wconversion -Wshadow` — Warnungen sind Fehler, denn was auf dem Host warnt, warnt auf dem Cortex-M33 auch, nur bemerkt es dort niemand.

Abgedeckt: CCITT-FALSE-Normvektor, Wire-Layout byteweise, Roundtrip über **alle** Payload-Längen 0…255 (beide Grenzen), unvollständige Frames, CRC-Fehler, unbekannte Version, führender Leitungsmüll, Resync-Fortschrittsgarantie und ein Empfangsstrom, der sich nach einem zerstörten Frame nachweislich wieder fängt.

Zwei Eigenschaften sind **sicherheitsrelevant** und deshalb je durch einen eigenen Test festgenagelt:
1. **CRC wird vor der Version geprüft.** Nur so ist die SEQ, die ein `NACK(version)` zurückspiegelt, durch die Prüfsumme gedeckt ([`PROTOCOL.md` §5](PROTOCOL.md)).
2. **Resync springt hinter den defekten Anker**, nicht auf Byte 1 — sonst fände der Parser bei führendem Müll denselben kaputten Frame erneut und träte auf der Stelle.

## Build-Ziel (später)
Pico-SDK (RP2350, Cortex-M33). Die pin-abhängige HAL-Schicht kommt erst nach dem Mainboard-Schaltplan (Phase 5 / Gate G07). Alles hier ist so geschnitten, dass es **ohne** Pinmap kompiliert — Logik oben, Hardwarezugriff unten.
