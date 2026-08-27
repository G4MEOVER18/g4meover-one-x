# G4MEOVER ONE-X — Architektur

## Systemübersicht

ONE-X kombiniert **vier voneinander getrennte Rechen-/Funkdomänen** auf modularen Boards, verbunden über definierte Board-to-Board-Interfaces. Die Trennung ist Absicht: sie erlaubt getrennte EVT-Iteration, EMI-Partitionierung und getrennte Zertifizierung.

### 1. Compute-Domäne (Mainboard, 210 × 92 mm, 12-Layer HDI)
- **RK3576** Application-SoC — Linux, UI, Netzwerk, USB, Storage, High-Level-RF-Software, Datenverarbeitung.
- **RK806S-5** PMIC (Rail-Map folgt Rockchip-Referenz — HOLD).
- **16 GB LPDDR5** (Kapazität FIXED, Topologie HOLD), **256 GB UFS** (Kapazität FIXED, MPN HOLD), **32 MB SPI-NOR** Recovery.
- High-Speed-I/O: 2× GbE (RTL8211F), Wi-Fi 6E + BT, USB-C PD/USB3/DP-Alt, 2. USB-C Host, USB-A 3.x, HDMI, microSD, M.2 B-Key (**PCIe 2.1 ×1** + USB).

### 2. Systemcontroller-Domäne (RP2350B, auf UI-Carrier)
Always-On, **unabhängig von Linux**. Übernimmt Power/Wake, D-Pad, 5 Softkeys, 40-mm-Touch-Ring, Haptik (DRV2605L + LRA), Status-LEDs, Sensorik, Lüftersteuerung, Watchdog, Akku-Telemetrie, Recovery, Debug und die **Überwachung des Hardware-TX-Kill**. Kommunikation zu RK3576 über I²C (Status/Control), UART (Debug/Recovery), optional SPI (schnelle Events). **Kein Framebuffer-Pfad** — das Display hängt direkt per MIPI-DSI am RK3576.

### 3. RF-Core-Domäne (92 × 66 mm)
Protokollorientierte Low-Power-Radios: **CC1101** (Sub-GHz), **SX1262** (LoRa/FSK), **CC2652P7** (Zigbee/Thread/BLE), **PN7160** (NFC/HF), 125-kHz-LF-RFID, **EFR32ZG23** (Z-Wave, TARGET), **Impinj E710** (UHF RAIN, TARGET), IR TX/RX, geschütztes 1-Wire/AUX. Physischer TX/RF-Kill-Pfad.

### 4. HyperRF-Domäne (136 × 72 mm)
Hochleistungs-Funk-Subsystem: **2× LMS7002M** (4RX/4TX coherent-capable, 100 kHz–3,8 GHz nativ, bis 6 GHz per Umsetzung), 2× RFFC5071A-Konverter, **FPGA** (PCIe-2.1-Endpoint, Channelizer, Decimation, Timestamping, DSP — MPN HOLD). Weiter: **5G Sub-6+mmWave** (Quectel RM530N-Klasse), **IoT-NTN** (BG95-S5), **GNSS L1/L5 raw** (NEO-F10N), **UWB** (DW3000), **60-GHz-FMCW-Radar** (IWRL6432W, eigenes RF-Fenster), LR1121.

> **Bandbreiten-Regel:** PCIe 2.1 ×1 kann **nicht** alle 4 RFIC-Kanäle bei Maximalrate gleichzeitig übertragen. Der FPGA *muss* channelisieren/dezimieren. Kein „DC-60 GHz SDR"-Claim — 60 GHz ist ein separater Radar-Sensor.

## Board-Partition

| Board | Maße (mm) | Inhalt |
|---|---|---|
| Mainboard | 210 × 92, 12L HDI | RK3576, PMIC, RAM, UFS, Ethernet, USB, HDMI, Wi-Fi, M.2, Power |
| UI-Carrier | 218 × 100 | RP2350B, Tasten, Touch-Ring, Sensoren, Audio, Haptik (Display-Keepout 138 × 81) |
| RF-Core | 92 × 66 | protokollorientierte Radios |
| HyperRF | 136 × 72 | SDR + FPGA + Mobilfunk/GNSS/UWB/Radar |
| M.2-Bridge | 30 × 52 | M.2-Host-Anbindung |
| Antenna-Rail | 150 × 18 | 4× SMA (oberes/hinteres Rail) |

## Antennen & Ergonomie
4 externe SMA nur auf dem oberen/hinteren Rail — **nicht** in den seitlichen Griffzonen. Interne/FPC-Antennen für Wi-Fi/BT, 5G, mmWave, GNSS, UWB, Radar. RF-Fenster in Gehäuse und Heatspreadern metallfrei halten.

## Kühlung
Getrennte Heatspreader (Mainboard / HyperRF, Vapor-Chamber-Ziel) + 2 flache Blower + Luftkanäle. Aktueller Stand: 2D-Precheck ~44,5 W modelliert, 30 °C Umgebung, ~74,3 °C Tmax → **PASS-PRELIM** (kein CFD, keine Zertifizierung). Final: reale Fan-P/Q-Kurven, 3D-CFD oder Mess-EVT (Gate G10).

## Software-Vision
Debian-/Linux mit systemd, NetworkManager, SSH, USB-Gadget/Host, Ethernet-Routing/Bridge/VLAN, SDR-Frameworks (SoapySDR/GNU Radio), GNSS-Services, lokaler API, Update/Recovery. **ONE-X-UI** verbindet Touch + Hardware-Controls; Bereiche: Dashboard · RF-Explorer · Spectrum/SDR · Network-Tools · Signal-Generator · NFC/RFID · LoRa/IoT · 5G/NTN · GNSS · Diagnostics · Files · Terminal · Settings.
