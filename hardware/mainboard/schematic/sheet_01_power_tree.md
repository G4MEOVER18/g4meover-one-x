# Sheet 01 — Power-Tree / Entry

Eingangs- und Verteilungsebene: USB-C-PD-Eingang, Akku-Ladepfad, System-Rails. Quelle: [`../../../spec/POWER_TREE.csv`](../../../spec/POWER_TREE.csv). Status der Rails wie dort (FIXED-Topologie / TARGET-Implementierung / HOLD-Rail-Map).

## Blockfluss

```
USB-C  ──VBUS_C──▶ TPS25751A (PD)          Molicel 21700 ×4 (2S2P)
        (5–20 V neg.)   │                        │ BAT_2S2P (7,2 V nom / 8,4 V full)
                        ▼                        ▼
                   BQ25792 (2S Buck-Boost-Charger, Power-Path) ──┬── Ladepfad ▶ BQ28Z620 (Gauge/Protection)
                        │                                        │
                        ▼ VSYS                                   ▼ (Zellmessung/Balancing)
        ┌───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼
   +5V_SYS Buck    +3V3_SYS Buck   +3V3_AON Buck    RK806S-5 PMIC
   (10 A trans.)   (5 A)           (<1 A, low-Iq)   (RK3576-Rails, Rail-Map HOLD)
        │               │               │               │
   USB/Fans/        Logik/Radios/    RP2350/RTC/     CPU/GPU/NPU/DDR
   HyperRF-AUX      M.2              Security        (dyn. rails)
```

## Netze (Sheet-Ausgänge)

| Netz | Nominal | Quelle | Verbraucher (Beispiele) | Status |
|---|---|---|---|---|
| `VBUS_C` | 5–20 V neg. | USB-C via TPS25751A | Charger-Eingang | TARGET |
| `BAT_2S2P` | 7,2 V / 8,4 V | 4× 21700 2S2P | Charger/Power-Path | FIXED (Topologie) |
| `VSYS` | Adapter/Akku | BQ25792 Power-Path | alle Bucks, RK806S | TARGET |
| `+5V_SYS` | 5,0 V | High-Current-Buck | RK806S, USB, Fans, HyperRF-AUX | TARGET (10 A transient) |
| `+3V3_SYS` | 3,3 V | System-Buck | Logik, Radios, M.2 | TARGET (5 A) |
| `+3V3_AON` | 3,3 V | Low-Iq-Buck | RP2350, RTC, Security (Always-On) | FIXED (Architektur) |
| `HYPERRF_AUX_5V` | 5,0 V | +5V_SYS (+ opt. ext. PD) | FPGA/SDR/5G/Fans | TARGET (5 A) |
| RK806S-Rails | dynamisch | RK806S-5 | RK3576 CPU/GPU/NPU/DDR | **HOLD (Rail-Map)** |

## Kern-Bauteile (aus BOM_EVT.csv)

| Ref | Bauteil | Rolle |
|---|---|---|
| U302 | TI TPS25751A | USB-C-PD-Controller (5–20 V, bis 5 A Controller-Fähigkeit) |
| U300 | TI BQ25792-Klasse | 2S Buck-Boost-Charger + Power-Path |
| U301 | TI BQ28Z620 | 2S Gauge + Schutz (Zell-Charakterisierung/Learn-Cycle) |
| U101 | Rockchip RK806S-5 | PMIC für RK3576-Rails (Rail-Map folgt RK3576-Referenz) |

## Kritische Design-Notizen
- **Power-Sequencing:** RK806S-Sequenz nach RK3576-Referenz (HOLD, bis Rail-Map bestätigt). `PG_*`/`PWR_EN_*`/`RESET_*n` sauber verketten; Power-Good vor Core-Release.
- **`+3V3_AON` immer zuerst / immer an:** speist den Always-On-RP2350B ([`../../../firmware/rp2350/`](../../../firmware/rp2350/)) — muss unabhängig von VSYS-Bringup stabil sein.
- **IR-Drop:** `+5V_SYS` für 10 A transient auslegen (Kupfer/Plane, Sense-Punkt am Verbraucher). SI/PI-Review Gate G08.
- **RF-Kill-Bezug:** `RF_KILL` (HW-erzwungen, Sheet 13/RF-Core) muss PA-Enables gaten, unabhängig von diesen Rails — Default nach Reset = Kill aktiv.
- **Schutz:** Verpolungs-/Überspannungsschutz am USB-C-Eingang; Akku-Sicherung/NTC im Pack (Gate G11, Minewing).
- **Messpunkte:** Testpunkte an VSYS, +5V_SYS, +3V3_SYS, +3V3_AON, BAT_2S2P (→ Sheet 18).

## ERC-Absicht
Rails als Power-Output-Flags an ihren Quellen, Power-Input an Verbrauchern; ein globales `GND`. Keine unversorgten Power-Netze. `HYPERRF_AUX_5V` als abgeleitetes Netz von `+5V_SYS` deklarieren (kein Doppel-Treiber).

## Offene HOLD-Punkte
- RK806S-**Rail-Map** (welche RK3576-Rails, Spannungen, Sequenz) → RK3576-Referenz nötig (Gate G07/G02-Umfeld).
- Genaue Buck-MPNs + Kompensation → nach Rail-Map.
