# RK3576 ↔ RP2350 Link-Protokoll (ONE-X-Link v1)

Framed, byteorientiert, bidirektional. Transport **UART** (primär, framed) oder **SPI** (optional) — die konkrete Busauswahl/Pins sind **HOLD** (Mainboard-Schaltplan, Gate G07). Das Protokoll selbst ist transport- und pin-unabhängig.

Referenz-Implementierung der Struktur: [`include/onex_proto.h`](include/onex_proto.h).

## 1. Frame

```
+------+------+------+------+------+---------- ... ----------+------+------+
| SOF0 | SOF1 | VER  | TYPE | SEQ  | LEN  |  PAYLOAD (LEN)   | CRCH | CRCL |
| 0xA5 | 0x5A | 0x01 |      |      |      |                  |      |      |
+------+------+------+------+------+------+------------------+------+------+
                     \___________ CRC-Abdeckung ___________/
```

- **SOF** = `0xA5 0x5A` (Frame-Start, Resync-Anker).
- **VER** = `0x01`.
- **TYPE** = Nachrichtentyp (siehe §3).
- **SEQ** = Sequenznummer (0–255, wrap). Kommandos werden per SEQ quittiert.
- **LEN** = Payload-Länge (0–255).
- **CRC** = CRC-16/CCITT-FALSE (Poly `0x1021`, Init `0xFFFF`) über **VER..PAYLOAD** (nicht über SOF), big-endian.

Max. Framegröße = 2+1+1+1+1+255+2 = **263 Byte**.

## 2. Zuverlässigkeit
- **Kommandos (Host→Mgr):** erwarten `ACK`/`NACK` mit gespiegelter SEQ. Timeout/Retry im Host (empfohlen 3× / 20 ms).
- **Events/Telemetrie (Mgr→Host):** fire-and-forget mit eigener SEQ; Host darf Lücken erkennen, muss aber nicht ACKen.
- **Resync:** Empfänger sucht bei CRC-Fehler das nächste `0xA5 0x5A`.

## 3. Nachrichtentypen

### Host → Manager (Kommandos)
| TYPE | Name | Payload | Wirkung |
|---|---|---|---|
| `0x01` | `CMD_PING` | – | Liveness; Mgr antwortet `ACK` |
| `0x02` | `CMD_POWER` | `u8 action` (0=shutdown,1=reboot,2=suspend,3=resume_ack) | Power-/Zustandswechsel |
| `0x03` | `CMD_RFKILL_SET` | `u8 engage` + `u8 token[8]` | `1`=sofort Kill; `0`=**Freigabe-Anfrage** (Policy-geprüft) |
| `0x04` | `CMD_FAN` | `u8 mode`,`u8 duty` | 0=auto,1=manuell(duty) |
| `0x05` | `CMD_HAPTIC` | `u8 effect`,`u8 intensity`,`u16 ms` | Haptik auslösen |
| `0x06` | `CMD_STATUS_LED` | `u8 pattern`,`u8 arg` | Status-LED/Anzeige |
| `0x07` | `CMD_RECOVERY` | `u8 mode` (0=DFU/BOOTSEL,1=fw-update-begin) | Recovery/Update |
| `0x08` | `CMD_GET` | `u8 what` | Telemetrie anfordern (Mgr sendet passendes EVT) |
| `0x09` | `CMD_TIME_SYNC` | `u64 unix_us` | Zeit setzen |

### Manager → Host (Events / Telemetrie)
| TYPE | Name | Payload | Bedeutung |
|---|---|---|---|
| `0x81` | `EVT_HEARTBEAT` | `u8 state`,`u8 flags`,`u32 uptime_s` | zyklisch (~1 Hz); `flags` bit0 = **RF-Kill aktiv** |
| `0x82` | `EVT_BUTTON` | `u8 id`,`u8 action` | down/up/short/long/combo |
| `0x83` | `EVT_TOUCHRING` | `u16 pos`,`u8 gesture` | Ring-Position/Geste |
| `0x84` | `EVT_BATTERY` | `u8 soc`,`u16 mV`,`i16 mA`,`i8 tempC`,`u8 flags` | 2S2P-Gauge |
| `0x85` | `EVT_SENSOR` | `u8 kind`,`u8 data[]` | IMU/Temp/ALS … |
| `0x86` | `EVT_FAULT` | `u8 code`,`u8 module` | Fehler → FAULT-Zustand |
| `0x87` | `EVT_RFKILL` | `u8 state`,`u8 reason` | Kill-Zustandswechsel |
| `0x88` | `EVT_WAKE` | `u8 source` | Wake-Ursache (Touch/Power/RTC) |

### Beide Richtungen
| TYPE | Name | Payload | Bedeutung |
|---|---|---|---|
| `0x40` | `ACK` | `u8 ack_seq`,`u8 status` | Kommando akzeptiert |
| `0x41` | `NACK` | `u8 ack_seq`,`u8 reason` | Kommando abgelehnt |

## 4. RF-Kill-Semantik (sicherheitskritisch)
- Der **Manager ist die Autorität**. `CMD_RFKILL_SET engage=1` wirkt **sofort und physisch** — ohne Token, ohne Profilprüfung, in jedem Zustand.
- `engage=0` ist nur eine **Freigabe-ANFRAGE**: Der Manager gibt frei **nur**, wenn (a) ein gültiges Regulierungsprofil aktiv ist und (b) das `token` eine bewusste Nutzerfreigabe belegt. Sonst `NACK(reason=policy)`.
- **`token` = One-Shot-Nonce nach physischer Geste** (Festlegung 2026-09-07). Der Manager erzeugt es *erst*, wenn am Gerät eine Taste/Ring-Geste erkannt wurde, und gibt es per `CMD_GET` heraus. Der Host spiegelt es zurück. Nach jeder Anfrage ist es verbraucht — **auch bei Ablehnung**, sonst wäre es im offenen Zeitfenster durch Wiederholung erratbar. Fenster: 10 s (TARGET).
- **Link-Verlust:** Bleiben Frames vom Host aus, greift der Kill nach einer Karenzzeit von 3 s (TARGET) mit `EVT_RFKILL(reason=LINK_LOSS)`. Kurze Aussetzer unterbrechen keine laufende autorisierte Messung, ein Absturz führt aber zuverlässig zum funkstillen Zustand.
- Zustandsautomat + Policy vollständig: [`include/onex_rfkill.h`](include/onex_rfkill.h), Umsetzung in [`src/onex_rfkill.c`](src/onex_rfkill.c).
- Nach **Boot/Reset/Fault** ist RF-Kill **aktiv** (Default-sicher). Linux allein kann den Kill **nie** softwareseitig umgehen.
- Jeder Kill-Zustandswechsel wird per `EVT_RFKILL` gemeldet; `EVT_HEARTBEAT.flags bit0` spiegelt den Live-Zustand.

## 5. Versionierung
`VER` inkrementiert bei inkompatibler Frame-/Typänderung. Empfänger verwerfen unbekannte `VER` und antworten `NACK(reason=version)`.
