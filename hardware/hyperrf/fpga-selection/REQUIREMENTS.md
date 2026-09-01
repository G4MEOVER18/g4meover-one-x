# HyperRF-FPGA — Anforderungen (abgeleitet aus Master-Spec)

Jede Zeile nennt ihre **Herkunft**. „Abgeleitet" = logische Folge aus einem FIXED/VALIDATED_ARCH-Spec-Punkt, **nicht** ein geratener Herstellerwert. Konkrete Zahlen, die erst ein Datenblatt liefert, stehen als `TBD 📄`.

## Hard-Anforderungen (Knockout — Verletzung = Kandidat raus)

| ID | Anforderung | Warum / Herkunft |
|---|---|---|
| **K1 — PCIe-Endpoint** | Muss einen **PCIe-2.1-x1-Endpoint** bereitstellen (Hard-IP bevorzugt; Soft-PCIe nur, wenn LUT-/Power-Budget es trägt). **Kein** Gen3 x4. | `hyperrf.host_limit` (FIXED); Forbidden-Claim „PCIe Gen3 x4 host" |
| **K2 — LMS7002M-Interface** | Muss die digitale IQ-Schnittstelle für **2× LMS7002M** treiben (LMS „LML"-Parallel-LVDS, DDR). Lane-/Pin-Zahl je Modus (SISO/MIMO, SDR/DDR) = `TBD 📄`; FPGA muss genug **LVDS-fähige I/O** + Taktressourcen haben. | `hyperrf.sdr` (2× LMS7002M 4RX/4TX) |
| **K3 — DSP/Speicher für Channelization** | Muss die 4-Kanal-Dezimation/Channelization vor PCIe x1 leisten: ausreichende **DSP-Slices + BRAM** für Filterketten/FIFOs. Konkreter Bedarf (Taps, Kanäle, Fs) = `TBD 📄` nach DSP-Dimensionierung. | `hyperrf.host_limit` (FIXED: „FPGA decimation/channelization required") |
| **K4 — Power-Deckel** | Gesamt-FPGA-Leistung (Core+I/O+Transceiver) muss ins **Handheld-Thermik-/Akku-Budget** passen (Dual-Low-Profile-Blower, getrennte HyperRF-Wärmeableitung). Zielobergrenze `TBD 📄` (kommt aus Thermik-Budget G10). | `thermal.architecture` (FIXED); `power`-Domäne Handheld |
| **K5 — Verfügbarkeit/Lifecycle** | Muss **aktiv beschaffbar** sein (kein NRND/EOL) für Klein-/Mittelserie, mit realer Distributor-Verfügbarkeit. | Produkt-Direktive „später vermarkten"; EVT→DVT braucht Nachkaufbarkeit |

## Soft-Anforderungen (fließen gewichtet in den Score)

| ID | Achse | Warum wichtig |
|---|---|---|
| **S1** | **Timestamping/Timing-Fähigkeit** — genug Takt-/PLL-Ressourcen für 10 MHz-Ref + GNSS-PPS + Sample-Timestamping | `hyperrf.timing` (TARGET) |
| **S2** | **Kohärenz-Support** — Taktverteilung/Sync für 2× LMS7002M *kohärent* (gemeinsame LO/Sampling) | `hyperrf.sdr` „coherent-capable" |
| **S3** | **Package/Thermik** — Ball-Pitch/Package für 12-Layer-HDI machbar, thermisch anbindbar | `pcb.mainboard_process` (HDI), `thermal` |
| **S4** | **Toolchain-Offenheit** — Open-Source-Toolflow (Yosys/nextpnr o.ä.) oder frei nutzbare Vendor-Tools; wichtig für ein **Open-Source-Gerät** (Hackbarkeit, Reproduzierbarkeit der Builds) | Repo ist Open-Source (CERN-OHL-S) |
| **S5** | **DSP-Headroom** — Reserve über K3 hinaus für spätere Features (mehr Kanäle, mmWave-/NTN-Vorverarbeitung) | HyperRF-Roadmap (5G/NTN/Radar TARGET) |
| **S6** | **I/O-Headroom** — Reserve-LVDS/GPIO für Filterbank, Converters, Radar-Tile, Clock-Domäne | Phase 9 HyperRF-HW |
| **S7** | **Kosten** — Stückpreis in EVT-/Kleinserien-Menge | Vermarktungsziel |
| **S8** | **Ökosystem/Referenzdesigns** — LMS7002M-/LimeSDR-nahe Referenz-Gateware, PCIe-EP-IP-Reife, Community | Reduziert Bring-up-Risiko |

## Ausdrücklich **nicht** gefordert / verboten (Guard)

- **Kein** allgemeiner 60-GHz-SDR-Anspruch (Radar ist separate IWRL6432W-Klasse-Kachel). → `hyperrf.not_claimed` (FIXED)
- **Kein** Gen3 x4 Host, **kein** 6-Layer-Mainboard. → Forbidden-Claims
- **Kein** vorab gesetzter MPN (auch nicht Zynq UltraScale+) bis G04 mit realen Werten geschlossen ist.

## Was zum Schließen von G04 gebraucht wird

1. Für jeden Kandidaten die `TBD 📄`-Zellen der Matrix mit **Datenblatt-** und **Verfügbarkeitswerten** belegen.
2. K4-Obergrenze aus dem Thermik-/Akku-Budget (Kopplung an G10/G11) festlegen.
3. K2/K3-Konkretisierung aus der **DSP-Dimensionierung** (Kanalzahl × Fs × Taps) und dem gewählten LMS-Interface-Modus.
4. `score.py` liefert Rangfolge → Gewinner + Begründung → `hyperrf.fpga`: HOLD → FIXED.
