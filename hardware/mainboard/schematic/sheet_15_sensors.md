# Sheet 15 — Sensoren

Sensor-Cluster am I²C (teils vom RP2350 überwacht — Spec: RP2350 macht „sensors"). Status: TARGET (Platzierung/Isolation).

## Bauteile (aus BOM_EVT.csv)

| Ref | Bauteil | Funktion | Bus |
|---|---|---|---|
| U230 | TDK ICM-42688-P | 6-Achs-IMU | I²C/SPI |
| U231 | ST LIS2MDL | Magnetometer | I²C |
| U232 | Bosch BMP390 | Barometer | I²C |
| U233 | Sensirion SHT41 | Temp/RH | I²C |
| U234 | Vishay VEML7700 | Umgebungslicht | I²C |

## Netze

| Netz | Funktion | Status |
|---|---|---|
| `SENS_I2C_SCL/SDA` | Sensor-Bus | TARGET |
| `IMU_INT1/2` | IMU-Interrupts (Wake/Motion) | TARGET |
| `SENS_3V3` | Versorgung | TARGET |

## Kritische Design-Notizen (Platzierung ist hier alles)
- **Magnetometer (U231):** **fern** von Lautsprecher, Haptik-LRA, Power-Induktivitäten (Hard-Iron-Störung).
- **Baro (U232):** definierter **Vent-Pfad** zum Gehäuse; **kein IP-Claim** (DEFERRED).
- **Temp/RH (U233):** von internen Wärmequellen (SoC/PMIC/HyperRF) isolieren, sonst Messfehler.
- **ALS (U234):** Lichtleiter/Fenster zur Front (Mechanik).
- **IMU:** vibrationsarm platzieren; INT-Leitungen für Wake nutzbar (RP2350).
- **Adress-Kollisionen** am I²C prüfen (ggf. zweiter Bus).
- **Testpunkte:** `SENS_I2C_*` (→ Sheet 18).

## ERC-Absicht
Ein I²C-Bus mit Pull-Ups; Sensor-Rails Power-Input; Interrupts als Signale. Eindeutige I²C-Adressen (sonst Split).

## HOLD / TBD
- IMU-Bus (I²C vs. SPI) + zweiter I²C-Bus bei Adresskonflikt 📄.
- Finale Platzierung ⇒ Layout/Mechanik-Review.
