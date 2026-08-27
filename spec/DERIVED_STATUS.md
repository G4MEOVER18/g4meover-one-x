# G4MEOVER ONE-X — Abgeleiteter Status

> Automatisch erzeugt aus `G4MEOVER-ONE-X_MASTER_SPEC.json` durch `tools/spec_validator.py`. **Nicht von Hand editieren.**

Projekt: **G4MEOVER ONE-X** · Revision: **EVT6** · Stand: 2026-08-27

## FIXED (47)

- **mechanical.device_envelope_mm** — {"x": 230.0, "y": 110.0, "z": 64.0}
- **mechanical.design_language** — Flipper-One-inspired wide handheld; larger, rugged, modular; not a dimensional clone
- **mechanical.front_display_recess_mm** — {"x": 138.0, "y": 81.0}
- **mechanical.visible_display_window_mm** — {"x": 112.5, "y": 64.5}
- **mechanical.touch_ring_outer_diameter_mm** — 40.0
- **mechanical.dpad_envelope_mm** — {"x": 34.0, "y": 34.0}
- **mechanical.softkeys** — {"count": 5}
- **mechanical.external_sma_ports** — {"count": 4}
- **display.class** — 5.0-inch IPS capacitive touch
- **display.resolution_native** — 720x1280 portrait; used 1280x720 landscape by software rotation
- **display.host_interface** — 4-lane MIPI DSI direct from RK3576
- **display.touch_interface** — I2C to RK3576/Linux input path; RP2350 may monitor wake IRQ only
- **compute.soc** — Rockchip RK3576
- **compute.ram_capacity** — 16 GB LPDDR5
- **compute.storage_capacity** — 256 GB UFS
- **compute.control_mcu** — RP2350B + 16 MB QSPI
- **compute.control_role** — power/wake/buttons/sensors/haptics/fans/status/debug; NOT main Linux framebuffer
- **battery.topology** — 2S2P, four 21700 cells
- **battery.nominal_pack_voltage_v** — 7.2
- **battery.full_charge_voltage_v** — 8.4
- **battery.pack_protection** — 2S pack protection + fuse + NTC + BQ28Z620 gauge/protector + certified EVT pack practice
- **network_io.ethernet** — 2x native Gigabit Ethernet via RTL8211F-class PHY
- **network_io.wifi_bt** — Wi-Fi 6E + Bluetooth onboard module
- **network_io.usb_c_1** — USB-C PD + USB3 + DP Alt Mode target
- **network_io.usb_c_2** — USB-C host/service
- **network_io.usb_a** — USB-A 3.x host
- **network_io.hdmi** — HDMI output
- **network_io.microsd** — microSD
- **network_io.sim** — Nano-SIM/eSIM path for modem
- **network_io.m2_host** — M.2 B-Key; host high-speed path PCIe 2.1 x1 plus USB3/USB2 where routed
- **rf_core.cc1101** — Sub-GHz protocol/raw low-power radio
- **rf_core.sx1262** — LoRa/FSK Sub-GHz
- **rf_core.cc2652p7** — Zigbee/Thread/BLE
- **rf_core.nfc** — PN7160-class 13.56MHz NFC/HF
- **rf_core.lf_rfid** — 125kHz LF RFID AFE + coil
- **rf_core.ir_1wire** — IR TX/RX + protected 1-Wire/AUX
- **hyperrf.not_claimed** — No general-purpose 60GHz SDR claim
- **hyperrf.host_limit** — PCIe 2.1 x1; raw 4-channel maximum RFIC bandwidth cannot be streamed continuously; FPGA decimation/channelization required
- **pcb.mainboard_layers** — 12
- **pcb.mainboard_outline_mm** — {"x": 210.0, "y": 92.0}
- **pcb.ui_carrier_outline_mm** — {"x": 218.0, "y": 100.0}
- **pcb.rf_core_outline_mm** — {"x": 92.0, "y": 66.0}
- **pcb.hyperrf_outline_mm** — {"x": 136.0, "y": 72.0}
- **pcb.m2_bridge_mm** — {"x": 30.0, "y": 52.0}
- **pcb.antenna_rail_mm** — {"x": 150.0, "y": 18.0}
- **pcb.current_files_status** — EVT6 includes current FLOORPLAN-ONLY KiCad boards; no final production schematic/Gerber until HOLD gates close
- **thermal.architecture** — separate main/HyperRF heat spreaders or vapor chamber targets + dual low-profile blowers; RF windows kept metal-free

## VALIDATED_ARCH (1)

- **hyperrf.native_sdr_range** — ~100kHz-3.8GHz LMS7002M native

## TARGET (17)

- **mechanical.mass_target_g** — {"min": 800, "max": 950}
- **display.evt_reference** — Waveshare 5-DSI-TOUCH-B / equivalent 5-inch 720x1280 DSI
- **display.production_reference_class** — 4-lane MIPI DSI, ILI9881C-class + GT911-class, active area approx. 110.4x62.1 mm
- **compute.recovery_flash** — 32 MB SPI NOR target
- **battery.cell_target** — Molicel INR-21700-P50B, 5.0Ah 3.6V
- **battery.nominal_capacity_ah** — 10.0
- **battery.nominal_energy_wh** — 72.0
- **rf_core.zwave** — EFR32ZG23-class Z-Wave/Z-Wave LR
- **rf_core.uhf_rfid** — Impinj E710-class 860-930MHz RAIN RFID
- **hyperrf.sdr** — 2x LMS7002M coherent-capable 4RX/4TX architecture
- **hyperrf.extended_sdr_target** — 100kHz-6GHz using high-band translation/filtering
- **hyperrf.fiveg** — Quectel RM530N-GL-class 5G Sub-6 + mmWave module bay
- **hyperrf.ntn** — Quectel BG95-S5-class 3GPP Rel-17 IoT-NTN
- **hyperrf.lora_sat** — Semtech LR1121-class sub-GHz/2.4/L/S radio
- **hyperrf.gnss** — u-blox NEO-F10N-00B-20-class L1/L5 raw GNSS + time pulse
- **hyperrf.radar** — TI IWRL6432W-class 57-64GHz radar, separate RF window/tile
- **hyperrf.timing** — 10MHz reference + GNSS time pulse + FPGA timestamping

## HOLD (8)

- **display.driver_gate** — Panel init/device-tree/Linux DRM validation on RK3576 required
- **compute.ram_exact_mpn_topology** — TBD after Rockchip-supported 16GB topology confirmation
- **compute.storage_generation_mpn** — TBD; must be validated against RK3576 UFS host
- **battery.transport_certification** — UN38.3 / pack compliance required before shipment/productization
- **hyperrf.fpga** — FPGA required for PCIe endpoint/DSP/channelization; exact MPN not frozen
- **hyperrf.uwb** — Qorvo DW3000-series; exact suffix not frozen
- **pcb.mainboard_process** — HDI target, final stackup/microvia/via-in-pad only after PCBWay DFM
- **thermal.analysis_status** — EVT6 full-system 2D precheck only; final 3D CFD/measured EVT required

## DEFERRED (1)

- **mechanical.environmental_rating** — NO IP RATING CLAIM IN EVT6

