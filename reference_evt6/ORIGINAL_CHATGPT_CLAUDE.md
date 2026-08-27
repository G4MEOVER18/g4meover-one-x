# CLAUDE.md — ONE-X EVT6

## 0. Role

You are working on **ONE-X EVT6**, a real hardware/product-engineering project.

Your job is to help turn the synchronized EVT6 concept into a manufacturable, testable Linux handheld while preserving revision consistency.

Treat this repository as an engineering project, not as a brainstorming session.

---

## 1. The one rule that overrides everything else

The authoritative project definition is:

`project_data/01_SOURCE_OF_TRUTH/ONE-X_EVT6_MASTER_SPEC.json`

This JSON is the **Single Source of Truth**.

No CAD, KiCad file, BOM, email, diagram, documentation, software configuration, generated graphic, manufacturing package, or code may contradict it.

If a requested change affects a FIXED/TARGET/HOLD value:

1. identify the affected source-of-truth keys;
2. explain the impact;
3. update the master spec first;
4. update all derived artifacts;
5. run the regression checks;
6. document the revision.

Never silently change the design.

---

## 2. Status semantics

Every technical assertion must respect these states:

- **FIXED** — project decision; do not alter without an explicit design change.
- **VALIDATED_ARCH** — architecture is supported by known component/interface capabilities, but implementation validation may remain.
- **TARGET** — desired implementation; exact part/value may still change.
- **HOLD** — NOT production-confirmed. Do not invent missing details.
- **DEFERRED** — intentionally not claimed/released in EVT6.

A HOLD must remain visibly a HOLD in code, docs, schematics, BOMs, diagrams and provider files.

---

## 3. Product concept

ONE-X is a **large modular Linux handheld for electronics, networking, RF research, automation and advanced diagnostics**.

Design language:
- strongly inspired by the wide, rugged, modular philosophy of Flipper One;
- NOT a dimensional clone;
- larger because it carries a real Linux display, high-performance SoC, large battery and multiple internal RF boards.

Authoritative outer envelope:

**230 × 110 × 64 mm**

Target mass:

**800–950 g**

No ingress-protection/IP rating is claimed in EVT6.

---

## 4. Human interface

### Main display

FIXED:
- 5.0-inch IPS capacitive multi-touch
- native 720 × 1280 portrait panel
- used as 1280 × 720 landscape
- 4-lane MIPI DSI direct from RK3576
- touch via I²C/IRQ to RK3576/Linux

Reference class:
- Waveshare 5-DSI-TOUCH-B or equivalent
- active-area reference ≈ 110.4 × 62.1 mm
- module reference up to ≈ 135.65 × 78.56 mm

HOLD:
- final production panel
- exact panel init sequence/device tree/Linux DRM bring-up

IMPORTANT:
RP2350B does **not** transport the main Linux framebuffer.

### Physical controls

FIXED:
- 40 mm capacitive touch ring
- 34 × 34 mm D-pad envelope
- five softkeys
- power/app/PTT controls
- haptic feedback target
- status/recovery functions

RP2350B handles:
- buttons
- touch ring
- haptic
- sensors
- wake/sleep
- fans
- watchdog
- power/system state
- low-level recovery/debug

---

## 5. Compute architecture

FIXED:
- Rockchip RK3576
- 16 GB LPDDR5 capacity
- 256 GB UFS capacity
- RP2350B + 16 MB QSPI system-management MCU
- 32 MB SPI NOR recovery target

HOLD:
- exact LPDDR5 MPN/topology
- exact UFS generation/MPN
- production RK3576/RK806S reference implementation

Never fabricate a DDR byte-lane map, memory topology, UFS pinout or PMIC rail map from generic assumptions.

Production memory/storage implementation requires the authoritative Rockchip/vendor reference package.

---

## 6. Battery and power

FIXED battery topology:

**2S2P / four 21700 cells**

Target cell:
- Molicel INR-21700-P50B
- 3.6 V nominal
- 5.0 Ah

Derived target pack:
- 7.2 V nominal
- 8.4 V full
- 10 Ah
- ~72 Wh

Power architecture targets:
- TPS25751A-class USB-C PD controller
- BQ25792-class 2S buck-boost charger
- BQ28Z620 gauge/protection
- fuse + NTC + pack protection
- high-current +5V system rail
- RK806S-5 SoC PMIC
- optional HyperRF AUX 5 V / 5 A target

HOLD:
- certified battery-pack implementation
- pack qualification / transport compliance
- final rail/current values

---

## 7. High-speed I/O

FIXED:
- 2 × native Gigabit Ethernet via RTL8211F-class PHYs
- Wi-Fi 6E + Bluetooth
- USB-C #1: PD + USB3 + DP Alt Mode target
- USB-C #2: host/service
- USB-A 3.x host
- HDMI output
- microSD
- SIM/eSIM path
- M.2 B-Key

M.2 host path:

**PCIe 2.1 ×1**, plus USB3/USB2 where routed.

Never write or draw PCIe Gen3 ×4 for EVT6.

---

## 8. RF Core

The low-power/protocol RF board contains or targets:

FIXED:
- CC1101 — Sub-GHz protocol/raw radio
- SX1262 — LoRa/FSK
- CC2652P7 — Zigbee/Thread/BLE
- PN7160-class — NFC/HF RFID
- 125 kHz LF RFID AFE + coil
- IR TX/RX
- protected 1-Wire/AUX

TARGET:
- EFR32ZG23-class Z-Wave/Z-Wave LR
- Impinj E710-class UHF RAIN RFID

The RF design must support a physical RF/TX kill path that software cannot override.

All transmit functionality must be implemented with regional regulatory profiles and safe lab-test modes.

---

## 9. HyperRF

Purpose:
A high-performance modular RF subsystem for SDR, cellular, satellite/NTN, GNSS, UWB and separate mmWave radar.

### SDR

TARGET:
- 2 × LMS7002M
- coherent-capable 4RX/4TX architecture
- 2 × RFFC5071A-class high-band conversion stages

VALIDATED architecture:
- LMS7002M native range ≈ 100 kHz–3.8 GHz

TARGET extended range:
- **100 kHz–6 GHz**
- achieved via translation/filtering where required

Never claim general-purpose 60 GHz SDR.

### FPGA

HOLD:
- exact FPGA MPN

Required functions:
- PCIe 2.1 endpoint
- LMS digital interfaces
- channelization
- decimation/interpolation
- buffering
- timestamping
- DSP/stream management

Critical bandwidth rule:
PCIe 2.1 ×1 cannot carry all possible raw maximum-rate 4-channel RFIC data simultaneously.
The FPGA must reduce/channelize/decimate data for host transfer.

### Additional HyperRF targets

- Quectel RM530N-GL-class 5G Sub-6 + mmWave
- Quectel BG95-S5-class 3GPP Rel-17 IoT NTN
- Semtech LR1121
- u-blox NEO-F10N-class L1/L5 raw GNSS + PPS
- Qorvo DW3000-series UWB — exact suffix HOLD
- TI IWRL6432W-class 57–64 GHz FMCW radar

57–64 GHz is a **separate radar subsystem**.

---

## 10. Antennas and ergonomics

FIXED:
- four external SMA connectors
- antenna rail target: 150 × 18 mm
- connectors belong on the rear/top antenna rail area

Do not place protruding SMA connectors on the left/right grip surfaces.

5G/mmWave, GNSS, UWB and radar may use dedicated internal/FPC/module antennas and RF-transparent windows.

Ergonomics must preserve both hand-grip zones.

---

## 11. PCB partition

Current board envelopes:

- Mainboard: **210 × 92 mm**
- UI carrier: **218 × 100 mm**
- RF Core: **92 × 66 mm**
- HyperRF: **136 × 72 mm**
- M.2 bridge: **30 × 52 mm**
- Antenna rail: **150 × 18 mm**

Mainboard target:
- **12-layer HDI**

Current KiCad files are:

**FLOORPLAN ONLY — NOT FOR FABRICATION**

They synchronize mechanical placement and architecture.
They are not production netlists or production routing.

---

## 12. Production release gates

Do NOT generate or authorize production Gerber/CPL for the direct-RK3576 mainboard until all relevant gates are closed.

Mandatory gates include:
1. 5-inch display Linux/DSI bring-up
2. exact 16 GB LPDDR5 topology
3. exact 256 GB UFS part
4. FPGA MPN freeze
5. exact DW3000 suffix
6. PCBWay final 12-layer HDI stackup
7. production schematic ERC clean
8. production layout DRC/SI/PI complete
9. RF EVT tuning
10. final thermal validation
11. battery pack compliance

---

## 13. Existing validation

Current synchronized EVT6 results:

- front/mechanical/battery/board fit: PASS
- 14/14 geometry checks: PASS
- generated STL topology/watertight checks: PASS
- stale-claim regression scan: PASS
- provider-package crosscheck: PASS
- full-device 2D thermal precheck:
  - ~44.5 W modeled heat
  - 30 °C ambient
  - ~74.3 °C Tmax
  - PASS-PRELIM

The thermal result is NOT CFD and NOT product certification.

---

## 14. Files you must know

Start with:

- `project_data/00_START_HERE/README_FIRST.md`
- `project_data/01_SOURCE_OF_TRUTH/ONE-X_EVT6_MASTER_SPEC.json`
- `project_data/01_SOURCE_OF_TRUTH/MASTER_SPEC_README.md`
- `project_data/01_SOURCE_OF_TRUTH/CHANGE_CONTROL.md`
- `project_data/02_ARCHITECTURE/DISPLAY_ARCHITECTURE.md`
- `project_data/02_ARCHITECTURE/INTERFACE_MATRIX.csv`
- `project_data/02_ARCHITECTURE/POWER_TREE.csv`
- `project_data/03_BOM/ONE-X_EVT6_BOM.csv`
- `project_data/04_MECHANICAL/SOURCE/generate_evt6_enclosure.py`
- `project_data/05_PCB_FLOORPLAN_ONLY/`
- `project_data/07_VALIDATION/`
- `project_data/09_REFERENCES/OFFICIAL_SOURCES.csv`

---

## 15. Engineering workflow

For every substantial change:

1. Read the master spec.
2. Identify affected FIXED/TARGET/HOLD values.
3. Do not guess unresolved vendor data.
4. Make one coherent change.
5. Update source-of-truth first if the architecture changes.
6. Update derived files.
7. Run validation/regression checks.
8. Report:
   - what changed;
   - why;
   - affected files;
   - newly introduced risks;
   - remaining HOLDs.

Prefer small, reviewable engineering steps over giant unverified rewrites.

---

## 16. Code/file editing rules

When fixing a source file:
- return/write the complete corrected file, not isolated fragments.
- keep generated files reproducible from source.
- add comments explaining engineering assumptions.
- never silently replace a target component with a different one.
- never convert a HOLD into a factual claim.

Generated artifacts should include provenance/version headers where practical.

---

## 17. Immediate recommended work

Read `docs/NEXT_WORK.md`.

The primary near-term objective is NOT cosmetic rendering.

It is to move ONE-X from synchronized EVT6 architecture toward a real engineering EVT by closing the high-risk gates in the right order.

