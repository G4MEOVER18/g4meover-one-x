# Sheet 02 — RK806S PMIC

Companion-PMIC (U101, Rockchip RK806S-5) erzeugt die RK3576-Rails aus `VSYS`/`+5V_SYS` (Sheet 01) und managt Sequencing/Reset. **Die exakte Rail-Map ist HOLD** — sie folgt der RK3576-Referenz (BOM: „Exact rail map must follow RK3576 reference"). Dieses Sheet legt Struktur + Anforderungen fest, ohne Rail-Werte zu erfinden.

## Rolle
- Multi-Rail-PMIC (mehrere Bucks + LDOs) — der für RK35xx vorgesehene Begleitbaustein.
- Erzeugt Core-/Logic-/GPU-/NPU-/DDR-/I-O-Rails für den RK3576 (Sheet 03).
- Steuerung/Telemetrie über `PMIC_*` (SPI oder I²C — nach Referenz 📄).
- Power-Sequencing + `PG`/Reset-Erzeugung → `RESET_n`/`NPOR` an RK3576.

## Eingänge (aus Sheet 01)

| Netz | Rolle |
|---|---|
| `VSYS` | Haupt-Eingang der Bucks |
| `+5V_SYS` | Hochstrom-Zweig (falls Referenz es nutzt) |
| `+3V3_AON` | Referenz/Enable-Ebene (Always-On) |

## Ausgänge (Rail-Map HOLD 📄 — Zuordnung folgt RK3576-Referenz)

| Rail (Platzhaltername) | Wahrscheinl. Verbraucher | Spannung | Sequenz | Status |
|---|---|---|---|---|
| `VDD_CPU_B` | A72-Cluster | 📄 | 📄 | HOLD |
| `VDD_CPU_L` | A53-Cluster | 📄 | 📄 | HOLD |
| `VDD_GPU` | GPU | 📄 | 📄 | HOLD |
| `VDD_NPU` | NPU | 📄 | 📄 | HOLD |
| `VDD_LOGIC` | Core/Logic | 📄 | 📄 | HOLD |
| `VDD_DDR` | LPDDR5-PHY | 📄 | 📄 | HOLD (→ G02) |
| `VCC_1V8` / `VCC_3V3` | I/O-Bänke | 📄 | 📄 | HOLD |

> Anzahl/Art (Buck vs. LDO), Spannungen und **Einschaltreihenfolge** exakt aus dem RK3576-Referenzdesign + RK806-Datenblatt. **Nicht raten** — bis dahin HOLD (blockiert Layout der Core-Region).

## Sequencing / Steuerung
- `PMIC_INT` (Interrupt), `PMIC_SLEEP`, `PMIC_SDA/SCL` bzw. `PMIC_SPI_*` — Zuordnung 📄.
- **Sequenz-Grundsatz:** I/O-/Logic-Rails vor Core-Release; alle `PG` gesammelt → `RESET_n` deassert.
- **Always-On-Bezug:** `+3V3_AON` (RP2350) ist **unabhängig** vom RK806S — der System-Manager bleibt an, auch wenn der PMIC/RK3576 aus ist (Sheet 01, [`../../../firmware/rp2350/`](../../../firmware/rp2350/)).

## Kritische Design-Notizen
- **Referenzdesign zwingend:** RK806S-Beschaltung (Feedback, Induktivitäten, Kondensatoren, Enable-Kette) nach Rockchip-Referenz übernehmen — der häufigste Fehlerpunkt bei RK35xx-Boards.
- **DDR-Rail** hängt an der LPDDR5-Topologie (G02) → Core-/DDR-Region nicht routen bis bestätigt.
- **Thermik:** PMIC-Verlustleistung in Bauraum/Spreader berücksichtigen (Gate G10).
- **Testpunkte** an jedem Rail (→ Sheet 18) für Bring-up.

## ERC-Absicht
Jede Rail als Power-Output an ihrer Quelle, Power-Input an den RK3576-Domänen (Sheet 03) — 1:1 konsistent. Enable-/PG-Netze als reguläre Signale mit definierten Pulls.

## HOLD (schließt mit)
- **G07-Umfeld / RK3576-Referenz:** komplette Rail-Map + Sequenz + Steuerbus.
- **G02:** `VDD_DDR`-Parameter (LPDDR5-Topologie).
