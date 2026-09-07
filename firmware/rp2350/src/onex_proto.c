/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * ONE-X-Link v1 — Referenz-Implementierung des Frame-Codecs.
 * Vertrag: ../include/onex_proto.h · Wire-Format: ../PROTOCOL.md
 *
 * Bewusste Eigenschaften:
 *  - Freistehend: nur <stdint.h>/<stddef.h>, kein malloc, keine libc-Strings,
 *    keine Hardware-/Pin-Annahme (Pinmap ist HOLD bis Gate G07).
 *  - Zero-Copy beim Dekodieren: *payload zeigt in den Eingabepuffer.
 *  - Keine Rekursion, kein unbeschraenktes Schleifenwachstum -> Superloop-tauglich
 *    (Modul-Vertrag: tick() < 200 us, siehe ../include/onex_modules.h).
 *
 * Identisch nutzbar auf RP2350B (Cortex-M33) und auf dem Host im Test
 * (tools/fw_test.py) — deshalb keine Endianness-Annahme: alle Mehrbyte-Felder
 * werden explizit byteweise big-endian gelesen/geschrieben.
 */
#include "onex_proto.h"

/* --- CRC-16/CCITT-FALSE: Poly 0x1021, Init 0xFFFF, kein Reflect, kein XorOut --- */
/*
 * Bitweise statt Tabelle: 263 Byte * 8 Bit ~ 2.1k Iterationen sind auf dem
 * RP2350B unkritisch, sparen aber 512 Byte Flash-Tabelle und sind direkt
 * gegen die Normdefinition prueflesbar. Bei Bedarf spaeter ersetzbar --
 * der Testvektor in test/ friert das Ergebnis fest.
 */
uint16_t onex_crc16(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFFu;

    if (data == NULL) {
        return crc;
    }

    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)((uint16_t)data[i] << 8);
        for (unsigned bit = 0; bit < 8u; ++bit) {
            if (crc & 0x8000u) {
                crc = (uint16_t)((uint16_t)(crc << 1) ^ 0x1021u);
            } else {
                crc = (uint16_t)(crc << 1);
            }
        }
    }
    return crc;
}

size_t onex_frame_encode(uint8_t type, uint8_t seq,
                         const uint8_t *payload, uint8_t len,
                         uint8_t *out)
{
    if (out == NULL) {
        return 0u;
    }
    /* len > 0 ohne Payload waere ein stiller Fehler -> ablehnen, nicht raten. */
    if (len > 0u && payload == NULL) {
        return 0u;
    }

    out[0] = ONEX_SOF0;
    out[1] = ONEX_SOF1;
    out[2] = ONEX_PROTO_VERSION;
    out[3] = type;
    out[4] = seq;
    out[5] = len;

    for (uint8_t i = 0; i < len; ++i) {
        out[ONEX_HEADER_LEN + i] = payload[i];
    }

    /* CRC deckt VER..PAYLOAD ab (nicht die SOF-Bytes) — PROTOCOL.md 1. */
    const size_t crc_span = (size_t)(ONEX_HEADER_LEN - 2u) + (size_t)len;
    const uint16_t crc = onex_crc16(&out[2], crc_span);

    out[ONEX_HEADER_LEN + len]      = (uint8_t)(crc >> 8);   /* big-endian */
    out[ONEX_HEADER_LEN + len + 1u] = (uint8_t)(crc & 0xFFu);

    return (size_t)ONEX_HEADER_LEN + (size_t)len + (size_t)ONEX_CRC_LEN;
}

/* Offset des naechsten SOF-Paares ab start, oder (size_t)-1 wenn keins. */
static size_t find_sof(const uint8_t *buf, size_t buflen, size_t start)
{
    if (buflen < 2u) {
        return (size_t)-1;
    }
    for (size_t i = start; i + 1u < buflen; ++i) {
        if (buf[i] == ONEX_SOF0 && buf[i + 1u] == ONEX_SOF1) {
            return i;
        }
    }
    return (size_t)-1;
}

size_t onex_frame_resync(const uint8_t *buf, size_t buflen)
{
    if (buf == NULL || buflen == 0u) {
        return 0u;
    }

    /*
     * Fortschrittsgarantie: die Suche startet HINTER dem aktuellen Anker,
     * nicht bei Index 1. Stuende Leitungsmuell vor dem defekten Frame, faende
     * eine Suche ab Index 1 erneut genau denselben Anker -> der Parser traete
     * auf der Stelle.
     */
    const size_t first = find_sof(buf, buflen, 0u);
    if (first != (size_t)-1) {
        const size_t next = find_sof(buf, buflen, first + 2u);
        if (next != (size_t)-1) {
            return next;
        }
    }

    /*
     * Kein weiterer Anker. Alles verwerfen -- ausser einem abschliessenden
     * 0xA5: das kann die erste Haelfte eines noch nicht vollstaendig
     * empfangenen SOF sein und darf nicht verloren gehen.
     */
    if (buf[buflen - 1u] == ONEX_SOF0) {
        return buflen - 1u;
    }
    return buflen;
}

int onex_frame_decode(const uint8_t *buf, size_t buflen,
                      onex_hdr_t *hdr, const uint8_t **payload)
{
    if (buf == NULL || hdr == NULL || payload == NULL) {
        return 0;
    }

    /* 1. Auf den Frame-Start ausrichten. Muell davor zaehlt als konsumiert. */
    const size_t sof = find_sof(buf, buflen, 0u);
    if (sof == (size_t)-1) {
        return 0;   /* noch kein Anker -> warten (Aufrufer darf resync nutzen) */
    }

    const uint8_t *f = &buf[sof];
    const size_t   avail = buflen - sof;

    /* 2. Header vollstaendig? */
    if (avail < (size_t)ONEX_HEADER_LEN) {
        return 0;
    }

    const uint8_t len = f[5];
    const size_t framelen = (size_t)ONEX_HEADER_LEN + (size_t)len + (size_t)ONEX_CRC_LEN;

    /* 3. Frame vollstaendig? (LEN ist hier noch ungeprueft -> nur als Laengenhinweis) */
    if (avail < framelen) {
        return 0;
    }

    /* 4. CRC ZUERST — erst danach darf irgendein Header-Feld geglaubt werden. */
    const size_t   crc_span = (size_t)(ONEX_HEADER_LEN - 2u) + (size_t)len;
    const uint16_t want = onex_crc16(&f[2], crc_span);
    const uint16_t got  = (uint16_t)(((uint16_t)f[ONEX_HEADER_LEN + len] << 8) |
                                     (uint16_t)f[ONEX_HEADER_LEN + len + 1u]);
    if (want != got) {
        return ONEX_DEC_ERR_CRC;
    }

    /* Ab hier sind VER/TYPE/SEQ/LEN durch die Pruefsumme gedeckt. */
    hdr->ver = f[2];
    hdr->type = f[3];
    hdr->seq = f[4];
    hdr->len = len;
    *payload = (len > 0u) ? &f[ONEX_HEADER_LEN] : NULL;

    /* 5. Version — hdr bleibt gefuellt, damit NACK(version) die SEQ spiegeln kann. */
    if (hdr->ver != ONEX_PROTO_VERSION) {
        return ONEX_DEC_ERR_VERSION;
    }

    return (int)(sof + framelen);
}
