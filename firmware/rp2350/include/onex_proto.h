/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X-Link v1 — RK3576 <-> RP2350B Frame-/Nachrichtendefinition.
 * Pin-/transportunabhaengig. Siehe ../PROTOCOL.md.
 *
 * Bewusst frei von Hardware-/Pin-Annahmen (die sind HOLD bis Mainboard-Schaltplan).
 */
#ifndef ONEX_PROTO_H
#define ONEX_PROTO_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* --- Frame-Konstanten --- */
#define ONEX_SOF0            0xA5u
#define ONEX_SOF1            0x5Au
#define ONEX_PROTO_VERSION   0x01u
#define ONEX_MAX_PAYLOAD     255u
#define ONEX_HEADER_LEN      6u    /* SOF0 SOF1 VER TYPE SEQ LEN */
#define ONEX_CRC_LEN         2u
#define ONEX_MAX_FRAME       (ONEX_HEADER_LEN + ONEX_MAX_PAYLOAD + ONEX_CRC_LEN) /* 263 */

/* --- Nachrichtentypen (Host -> Manager) --- */
enum {
    ONEX_CMD_PING        = 0x01,
    ONEX_CMD_POWER       = 0x02,  /* u8 action: 0=shutdown 1=reboot 2=suspend 3=resume_ack */
    ONEX_CMD_RFKILL_SET  = 0x03,  /* u8 engage + u8 token[8] */
    ONEX_CMD_FAN         = 0x04,  /* u8 mode, u8 duty */
    ONEX_CMD_HAPTIC      = 0x05,  /* u8 effect, u8 intensity, u16 ms */
    ONEX_CMD_STATUS_LED  = 0x06,  /* u8 pattern, u8 arg */
    ONEX_CMD_RECOVERY    = 0x07,  /* u8 mode: 0=DFU 1=fw_update_begin */
    ONEX_CMD_GET         = 0x08,  /* u8 what */
    ONEX_CMD_TIME_SYNC   = 0x09,  /* u64 unix_us */
};

/* --- Nachrichtentypen (Manager -> Host) --- */
enum {
    ONEX_EVT_HEARTBEAT   = 0x81,  /* u8 state, u8 flags, u32 uptime_s */
    ONEX_EVT_BUTTON      = 0x82,  /* u8 id, u8 action */
    ONEX_EVT_TOUCHRING   = 0x83,  /* u16 pos, u8 gesture */
    ONEX_EVT_BATTERY     = 0x84,  /* u8 soc, u16 mV, i16 mA, i8 tempC, u8 flags */
    ONEX_EVT_SENSOR      = 0x85,  /* u8 kind, u8 data[] */
    ONEX_EVT_FAULT       = 0x86,  /* u8 code, u8 module */
    ONEX_EVT_RFKILL      = 0x87,  /* u8 state, u8 reason */
    ONEX_EVT_WAKE        = 0x88,  /* u8 source */
};

/* --- Beide Richtungen --- */
enum {
    ONEX_ACK   = 0x40,   /* u8 ack_seq, u8 status */
    ONEX_NACK  = 0x41,   /* u8 ack_seq, u8 reason */
};

/* NACK-Gruende */
enum {
    ONEX_NACK_OK       = 0x00,
    ONEX_NACK_CRC      = 0x01,
    ONEX_NACK_VERSION  = 0x02,
    ONEX_NACK_UNKNOWN  = 0x03,
    ONEX_NACK_POLICY   = 0x04,  /* z.B. RF-Kill-Freigabe ohne Regulierungsprofil/Token */
    ONEX_NACK_BUSY     = 0x05,
    ONEX_NACK_BADARG   = 0x06,
};

/* System-Zustaende (EVT_HEARTBEAT.state) — vgl. ARCHITECTURE.md */
enum {
    ONEX_STATE_OFF = 0, ONEX_STATE_BOOT, ONEX_STATE_RUN,
    ONEX_STATE_SUSPEND, ONEX_STATE_SHUTDOWN, ONEX_STATE_FAULT,
};

/* Heartbeat-Flags */
#define ONEX_HB_RFKILL_ACTIVE  (1u << 0)
#define ONEX_HB_CHARGING       (1u << 1)
#define ONEX_HB_FAULT_LATCHED  (1u << 2)

/* Frame-Kopf (ungepackt genutzt; Wire-Format wird byteweise serialisiert) */
typedef struct {
    uint8_t ver;
    uint8_t type;
    uint8_t seq;
    uint8_t len;
} onex_hdr_t;

/* CRC-16/CCITT-FALSE (Poly 0x1021, Init 0xFFFF) ueber ver..payload. */
uint16_t onex_crc16(const uint8_t *data, size_t len);

/*
 * Serialisiert einen Frame nach out (mind. ONEX_MAX_FRAME Bytes).
 * Gibt die Gesamtlaenge zurueck, oder 0 bei ungueltigen Argumenten.
 */
size_t onex_frame_encode(uint8_t type, uint8_t seq,
                         const uint8_t *payload, uint8_t len,
                         uint8_t *out);

/*
 * Versucht, aus einem Bytepuffer genau EINEN Frame zu dekodieren.
 * Rueckgabe: Anzahl konsumierter Bytes bei Erfolg (Header via *hdr,
 * Payload-Zeiger in *payload), 0 wenn (noch) kein vollstaendiger Frame,
 * negativ bei CRC-/Versionsfehler (Aufrufer resynct auf naechstes SOF).
 */
int onex_frame_decode(const uint8_t *buf, size_t buflen,
                      onex_hdr_t *hdr, const uint8_t **payload);

#ifdef __cplusplus
}
#endif
#endif /* ONEX_PROTO_H */
