# ONE-X EVT6 — Gesamtkonzept und technische Projektübergabe

## 1. Idee

ONE-X ist ein eigenständig entwickelter, modularer Linux-Handheld für Elektronik, Netzwerktechnik, RF-Forschung, Automatisierung, Diagnose und technische Feldarbeit.

Das Gerät übernimmt bewusst die Idee eines kompakten, direkt bedienbaren Hardware-Multitools, geht technisch aber erheblich weiter:

- vollwertiges Linux statt reiner MCU-Oberfläche,
- RK3576 als Application Processor,
- großes Touchdisplay,
- sehr umfangreiche kabelgebundene I/O,
- mehrere voneinander getrennte Funkarchitekturen,
- ein leistungsfähiges HyperRF-Modul,
- große Batterie,
- modulare PCB-Struktur,
- hersteller- und fertigungsgerechter Entwicklungsprozess.

Die Formensprache ist **Flipper-One-inspiriert**, ONE-X ist jedoch kein mechanischer Clone.

---

## 2. Aktueller Revisionsstand

Revision: **EVT6**  
Stand: **27.08.2026**

EVT6 ist die erste Revision, in der Gehäuse, Display, Batterie, PCB-Abmessungen, Interfaces, BOM, RF-Architektur, Provider-Unterlagen und Grafikspezifikation auf eine gemeinsame Source of Truth synchronisiert wurden.

Die zentrale Datei lautet:

`project_data/01_SOURCE_OF_TRUTH/ONE-X_EVT6_MASTER_SPEC.json`

---

## 3. Physisches Gerät

### Abmessungen

**230 × 110 × 64 mm**

Zielgewicht:

**800–950 g**

Die Größe ist bewusst deutlich größer als klassische Flipper-Geräte, weil folgende Komponenten real Platz benötigen:

- 5"-Display,
- 4×21700,
- RK3576-Mainboard,
- RF Core,
- HyperRF,
- Kühlung,
- Netzwerk-/USB-/HDMI-Buchsen,
- ergonomische Griffzonen.

### Bedienkonzept

Vorderseite:

- 5.0" Touchdisplay
- 40-mm-Touch-Ring links
- D-Pad rechts
- 5 Softkeys unter dem Display
- zusätzliche App-/Power-/PTT-Bedienelemente
- Haptik
- Statusanzeigen

Die seitlichen Griffzonen sollen frei von großen HF-Steckern bleiben.

Die vier externen SMA-Anschlüsse befinden sich auf einem oberen/hinteren Antennen-Rail.

---

## 4. Display und Linux-UI

### Hauptdisplay

Festgelegt:

- 5.0" IPS
- kapazitiver Multi-Touch
- 720×1280 nativ
- im Gerät 1280×720 Landscape
- 4-Lane MIPI DSI
- direkt am RK3576

Touch:

- I²C + IRQ an RK3576/Linux

EVT-Referenz:

- Waveshare 5-DSI-TOUCH-B oder gleichwertige Klasse

Mechanische Referenz:

- aktive Fläche ca. 110.4×62.1 mm
- Modulklasse bis ca. 135.65×78.56 mm

Der RP2350B dient **nicht** als 720p-Framebuffer-Bridge.

### Geplante Linux-Nutzung

ONE-X soll nicht nur eine Launcher-Oberfläche anzeigen, sondern ein echtes Linux-System tragen können:

- Terminal
- SSH
- Browser/Web-UIs
- Netzwerktests
- Wireshark
- SDR-Oberflächen
- GNU Radio / SoapySDR-basierte Anwendungen
- GNSS/Karten
- Dateien/Logs
- Diagnosewerkzeuge
- Gerätekonfiguration
- Entwicklungs-/Debugwerkzeuge

---

## 5. Compute

### Haupt-SoC

**Rockchip RK3576**

Aufgaben:

- Linux
- UI
- Netzwerk
- USB
- Storage
- High-Level-RF-Software
- Datenverarbeitung
- Automatisierung
- lokale Dienste

### RAM

**16 GB LPDDR5** — Kapazität FIXED.

Noch offen/HOLD:

- konkreter Hersteller/MPN,
- Topologie,
- RK3576-validiertes Mapping,
- Training-/Reference-Design.

### Storage

**256 GB UFS** — Kapazität FIXED.

HOLD:

- konkrete UFS-Generation,
- konkretes MPN,
- RK3576-Host/Device-Validierung.

### Recovery

Ziel:

- 32 MB SPI-NOR für Recovery/Boot-Funktionen.

---

## 6. RP2350B-Systemcontroller

Ein separater **RP2350B + 16 MB QSPI** übernimmt Low-Level- und Always-On-Funktionen.

Aufgaben:

- Power/Wake
- D-Pad
- Softkeys
- Touch Ring
- Haptic
- Status-LEDs
- Sensorik
- Lüftersteuerung
- Watchdog
- Akku-/Power-Telemetrie
- Recovery
- Debug
- Kommunikation mit RK3576 über SPI/I²C/UART

Vorteil:

Selbst wenn Linux hängt, bleibt ein unabhängiger Hardware-Controller verfügbar.

---

## 7. Sensorik und Audio

EVT6-BOM enthält wieder explizit:

- ICM-42688-P IMU
- LIS2MDL Magnetometer
- BMP390 Barometer
- SHT41 Temperatur/Luftfeuchte
- VEML7700 Umgebungslicht
- PDM-Mikrofon
- Audio-Codec
- Lautsprecherverstärker
- Lautsprecher
- Haptic Driver + LRA

Besondere Platzierungsanforderungen:

- Magnetometer weg von Lautsprecher, Haptik und Induktivitäten,
- SHT41 thermisch von CPU/PMIC trennen,
- Barometer benötigt atmosphärische Öffnung,
- Mikrofon/Speaker benötigen akustische Gehäuseauslegung.

---

## 8. Batterie

Topologie:

**2S2P / 4×21700**

Zielzelle:

**Molicel INR-21700-P50B**

Zellwerte:

- 3.6 V nominal
- 5 Ah

Pack-Ziel:

- 7.2 V nominal
- 8.4 V voll
- 10 Ah
- ca. 72 Wh

Power-/Pack-System:

- BQ25792-class Charger
- BQ28Z620 Gauge/Protection
- TPS25751A USB-C-PD
- Sicherung
- NTC
- Pack-Protection

Noch HOLD:

- finales Packdesign,
- Sicherheitsqualifikation,
- Transport-/UN38.3-Prozess,
- mechanische Isolierung und Crash/Short-Schutz.

---

## 9. Haupt-I/O

ONE-X soll ein echtes mobiles Techniksystem sein.

Fest vorgesehen:

- 2× Gigabit Ethernet
- Wi-Fi 6E
- Bluetooth
- USB-C PD + USB3 + DP Alt Mode
- zweiter USB-C Host/Service
- USB-A 3.x
- HDMI
- microSD
- Nano-SIM/eSIM
- M.2 B-Key

M.2-Host:

**PCIe 2.1 ×1 + USB3/USB2**

Nicht Gen3×4.

---

## 10. RF Core

RF Core ist für kleinere, protokollorientierte und Low-Power-Radios vorgesehen.

### Sub-GHz
- CC1101
- SX1262

### 2.4 GHz / Mesh
- CC2652P7
- Zigbee
- Thread
- BLE

### Z-Wave
- EFR32ZG23-Klasse
- Z-Wave / Z-Wave Long Range

### RFID / NFC
- PN7160 HF/NFC
- 125-kHz LF RFID
- Impinj E710-Klasse UHF RAIN RFID

### Sonstige
- IR TX/RX
- 1-Wire/AUX

Ein physischer TX/RF-Kill soll einen Hardwarepfad abschalten können, unabhängig von Linux.

---

## 11. HyperRF

HyperRF ist das Hochleistungs-Funkmodul.

### SDR

Ziel:

- 2× LMS7002M
- 4RX/4TX coherent-capable
- 2× RFFC5071A-Klasse für High-Band-Umsetzung
- 100 kHz–6 GHz Zielabdeckung

Native LMS7002M-Architektur:

ca. 100 kHz–3.8 GHz.

Oberhalb davon:

Frequenzumsetzung/Filterung.

### Wichtige Einschränkung

60 GHz ist **kein allgemeines SDR-Band**.

Der 57–64-GHz-Pfad ist ein eigener Radar-Sensor.

### FPGA

FPGA ist notwendig, aber exact MPN = HOLD.

Benötigt werden:

- PCIe 2.1 Endpoint
- LMS7002M-Digitalinterfaces
- Channelizer
- Decimation
- Interpolation
- Buffering
- Timestamping
- DSP
- Datenratenmanagement

Das ist zwingend, weil PCIe 2.1 ×1 nicht sämtliche maximalen Rohdaten von vier RF-Kanälen gleichzeitig transportieren kann.

### 5G

Quectel RM530N-GL-Klasse:

- Sub-6
- mmWave
- M.2-3052-Klasse

### NTN

Quectel BG95-S5-Klasse:

- 3GPP Release 17 IoT-NTN
- LTE-M/NB-IoT
- GNSS

### LoRa / Satellite

Semtech LR1121-Klasse:

- Sub-GHz
- 2.4 GHz
- L/S-Band
- LR-FHSS/LoRa

### GNSS

u-blox NEO-F10N-Klasse:

- L1/L5
- Raw Data
- PPS / Time Pulse

### UWB

Qorvo DW3000-Serie.

Exact suffix = HOLD.

### Radar

TI IWRL6432W-Klasse:

- 57–64 GHz FMCW
- eigenes RF-Fenster
- kein Metall vor der Antenne.

---

## 12. Antennen

Fest:

**4 externe SMA**

Position:

- oberes/hinteres Antennen-Rail
- keine SMA-Anschlüsse in den seitlichen Griffzonen

Interne / FPC-Antennen:

- Wi-Fi/BT
- 5G
- mmWave
- GNSS
- UWB
- Radar
- gegebenenfalls NTN/LR1121

RF-Fenster müssen im Gehäuse und in den Heatspreadern berücksichtigt werden.

---

## 13. PCB-Aufteilung

### Mainboard
**210 × 92 mm**  
**12-Layer HDI Target**

Enthält primär:

- RK3576
- PMIC
- RAM
- UFS
- Ethernet
- USB
- HDMI
- Wi-Fi
- M.2-Host
- Power
- Board-to-Board-Interfaces

### UI Carrier
**218 × 100 mm**

Display-Ausschnitt:

**138 × 81 mm**

Enthält:

- RP2350B
- Tasten
- Touch Ring
- Sensoren
- Audio
- Haptik

### RF Core
**92 × 66 mm**

### HyperRF
**136 × 72 mm**

### M.2 Bridge
**30 × 52 mm**

### Antenna Rail
**150 × 18 mm**
**4× SMA**

Aktuelle KiCad-Dateien sind **Floorplan only**.

---

## 14. Kühlung

Architektur:

- Mainboard-Heatspreader/Vapor-Chamber-Ziel
- HyperRF-Heatspreader
- zwei flache Blower
- Luftkanäle
- RF-Fenster ohne Metallblockade

Aktueller Gesamtgeräte-Precheck:

- modellierte Wärme: ca. 44.5 W
- Umgebung: 30 °C
- Tmax: ca. 74.3 °C
- Ergebnis: PASS-PRELIM

Nicht zu verwechseln mit:

- CFD,
- DVT,
- thermischer Zertifizierung.

Final nötig:

- reale Fan-P/Q-Kurven,
- 3D-Luftkanäle,
- Kontaktwiderstände,
- finale Verlustleistungen,
- 3D-CFD oder Mess-EVT.

---

## 15. Software-Vision

### Linux

Ziel:

Debian-/Linux-basierte Plattform mit:

- systemd
- NetworkManager
- SSH
- USB Gadget/Host-Funktionen
- Ethernet Routing/Bridge/VLAN
- SDR Frameworks
- GNSS Services
- lokale API
- Web UI oder native UI
- Update/Recovery-System

### ONE-X UI

Die Oberfläche soll Touch und Hardwarecontrols kombinieren.

Mögliche Hauptbereiche:

- Dashboard
- RF Explorer
- Spectrum / SDR
- Network Tools
- Signal Generator / RF tools
- NFC/RFID
- LoRa/IoT
- 5G/NTN
- GNSS
- Diagnostics
- Files
- Terminal
- Settings

### RP2350-Firmware

Muss unabhängig von Linux funktionieren.

Schwerpunkte:

- deterministic input
- power state machine
- safe shutdown
- watchdog
- fan failsafe
- battery telemetry
- recovery
- hardware TX kill monitoring

---

## 16. Fertigungsstrategie

Aktuell nicht fertigungstauglich ist das direkte RK3576-Mainboard.

Grund:

noch offene autoritative Details zu:

- LPDDR5
- UFS
- RK3576 Reference Design
- PMIC-Rails
- HDI-Stackup
- FPGA
- RF-Matching
- finales Thermaldesign

PCBWay soll deshalb zuerst für:

- HDI-DFM
- Stackup
- Microvia/Via-in-Pad
- Impedanz
- BGA-Escape
- X-Ray/Assembly

eingebunden werden.

Minewing ist als möglicher JDM-/Engineeringpartner interessant für:

- Schaltplanreview
- Layout
- SI/PI
- DFM
- Komponenten-Sourcing
- Mechanik
- Thermal
- EVT-Build

---

## 17. Aktuelle Validierung

EVT6:

- 14/14 Geometriechecks PASS
- STL-Meshes PASS
- Frontlayout PASS
- 4×21700 passen in die definierte Batteriearchitektur
- Board-Outlines passen in das Gehäuse
- alte widersprüchliche Claims wurden aus externen Providerdaten entfernt
- Thermal PASS-PRELIM
- Produktions-Elektrik bleibt korrekt HOLD

---

## 18. Entwicklungsprinzip

Dieses Projekt darf nicht durch „schön aussehende Vollständigkeit“ beschädigt werden.

Wenn eine Herstellerinformation fehlt:

**nicht raten.**

Stattdessen:

- HOLD markieren,
- benötigtes Dokument benennen,
- mögliche Optionen bewerten,
- erst nach Validierung freigeben.

Ziel ist nicht eine möglichst schnell erzeugte Gerber-Datei.

Ziel ist ein Gerät, das nach dem Aufbau eine realistische Chance hat, elektrisch, mechanisch und thermisch korrekt zu funktionieren.
