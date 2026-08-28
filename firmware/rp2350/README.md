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

## Build-Ziel (später)
Pico-SDK (RP2350, Cortex-M33). Der Firmware-Code ist in dieser Phase **Architektur + Verträge**; die pin-abhängige HAL-Schicht kommt erst nach dem Mainboard-Schaltplan (Phase 5). Header hier sind so gehalten, dass sie **ohne** Pinmap kompilierbar sind.
