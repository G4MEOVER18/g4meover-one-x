/* SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
 *
 * Host-Unit-Tests fuer den ONE-X-Link-v1-Codec (../src/onex_proto.c).
 *
 * Laeuft auf dem Entwicklungsrechner und in der CI mit dem System-Compiler
 * (kein arm-none-eabi noetig), weil der Codec bewusst frei von Hardware- und
 * Pin-Annahmen ist. Aufruf ueber tools/fw_test.py -> tools/check_all.py.
 *
 * Diese Tests sind die Regressionsschranke fuer das Wire-Format: sie frieren
 * die Bytes ein, die spaeter ueber den echten Link zwischen RK3576 und RP2350B
 * gehen. Aendert sich hier etwas ungewollt, faellt der Build.
 */
#include <stdio.h>
#include <string.h>

#include "onex_proto.h"

static int g_checks;
static int g_failures;

static void check(int cond, const char *what)
{
    ++g_checks;
    if (!cond) {
        ++g_failures;
        printf("  [FAIL] %s\n", what);
    }
}

static void check_eq_int(long got, long want, const char *what)
{
    ++g_checks;
    if (got != want) {
        ++g_failures;
        printf("  [FAIL] %s: got %ld, want %ld\n", what, got, want);
    }
}

/* ------------------------------------------------------------------ CRC */

/*
 * Normvektor CRC-16/CCITT-FALSE: "123456789" -> 0x29B1.
 * Haelt die Implementierung an die Norm gebunden, falls sie spaeter auf eine
 * Tabellenvariante umgestellt wird.
 */
static void test_crc_reference_vector(void)
{
    printf("test_crc_reference_vector\n");
    const uint8_t v[] = { '1','2','3','4','5','6','7','8','9' };
    check_eq_int(onex_crc16(v, sizeof v), 0x29B1, "CCITT-FALSE Normvektor");
    check_eq_int(onex_crc16(NULL, 0), 0xFFFF, "Init-Wert bei leerer Eingabe");
}

/* -------------------------------------------------------------- Encoder */

static void test_encode_wire_layout(void)
{
    printf("test_encode_wire_layout\n");
    uint8_t out[ONEX_MAX_FRAME];
    const uint8_t pl[] = { 0x01, 0x00 };   /* ACK: ack_seq=1, status=0 */

    const size_t n = onex_frame_encode(ONEX_ACK, 0x2A, pl, sizeof pl, out);

    check_eq_int((long)n, ONEX_HEADER_LEN + 2 + ONEX_CRC_LEN, "Gesamtlaenge");
    check_eq_int(out[0], ONEX_SOF0, "SOF0");
    check_eq_int(out[1], ONEX_SOF1, "SOF1");
    check_eq_int(out[2], ONEX_PROTO_VERSION, "VER");
    check_eq_int(out[3], ONEX_ACK, "TYPE");
    check_eq_int(out[4], 0x2A, "SEQ");
    check_eq_int(out[5], 2, "LEN");
    check_eq_int(out[6], 0x01, "PAYLOAD[0]");
    check_eq_int(out[7], 0x00, "PAYLOAD[1]");

    /* CRC deckt VER..PAYLOAD ab, NICHT die SOF-Bytes (PROTOCOL.md 1). */
    const uint16_t want = onex_crc16(&out[2], 4 + 2);
    check_eq_int(out[8], (want >> 8) & 0xFF, "CRC high (big-endian)");
    check_eq_int(out[9], want & 0xFF, "CRC low");
}

static void test_encode_rejects_bad_args(void)
{
    printf("test_encode_rejects_bad_args\n");
    uint8_t out[ONEX_MAX_FRAME];
    const uint8_t pl[] = { 0xAA };

    check_eq_int((long)onex_frame_encode(ONEX_CMD_PING, 0, pl, 1, NULL), 0,
                 "out == NULL wird abgelehnt");
    /* len > 0 ohne Payload: darf NICHT still Muell senden. */
    check_eq_int((long)onex_frame_encode(ONEX_CMD_PING, 0, NULL, 4, out), 0,
                 "len>0 ohne payload wird abgelehnt");
    /* len == 0 ohne Payload ist zulaessig (z.B. CMD_PING). */
    check_eq_int((long)onex_frame_encode(ONEX_CMD_PING, 7, NULL, 0, out),
                 ONEX_HEADER_LEN + ONEX_CRC_LEN, "len=0 ohne payload ist gueltig");
}

/* ------------------------------------------------------- Roundtrip/Decode */

static void test_roundtrip_all_lengths(void)
{
    printf("test_roundtrip_all_lengths\n");
    uint8_t out[ONEX_MAX_FRAME];
    uint8_t pl[ONEX_MAX_PAYLOAD];

    for (unsigned i = 0; i < ONEX_MAX_PAYLOAD; ++i) {
        pl[i] = (uint8_t)(i * 7u + 3u);
    }

    int len_ok = 1, seq_ok = 1, data_ok = 1, ret_ok = 1;

    /* 0..255 deckt beide Grenzen ab: leerer Frame und maximaler Frame (263 B). */
    for (unsigned len = 0; len <= ONEX_MAX_PAYLOAD; ++len) {
        const size_t n = onex_frame_encode(ONEX_EVT_SENSOR, (uint8_t)len,
                                           pl, (uint8_t)len, out);
        if (n != (size_t)(ONEX_HEADER_LEN + len + ONEX_CRC_LEN)) { ret_ok = 0; }

        onex_hdr_t hdr;
        const uint8_t *got = NULL;
        const int r = onex_frame_decode(out, n, &hdr, &got);

        if (r != (int)n)                    { ret_ok = 0; }
        if (hdr.len != (uint8_t)len)        { len_ok = 0; }
        if (hdr.seq != (uint8_t)len)        { seq_ok = 0; }
        if (len > 0 && memcmp(got, pl, len)) { data_ok = 0; }
        if (len == 0 && got != NULL)        { data_ok = 0; }
    }

    check(ret_ok,  "Roundtrip 0..255: Laengen/Rueckgabewerte");
    check(len_ok,  "Roundtrip 0..255: LEN erhalten");
    check(seq_ok,  "Roundtrip 0..255: SEQ erhalten");
    check(data_ok, "Roundtrip 0..255: Payload identisch, len=0 -> NULL");

    /* Maximalframe passt exakt in ONEX_MAX_FRAME. */
    check_eq_int(ONEX_HEADER_LEN + ONEX_MAX_PAYLOAD + ONEX_CRC_LEN,
                 ONEX_MAX_FRAME, "ONEX_MAX_FRAME = 263");
}

static void test_decode_incomplete_returns_zero(void)
{
    printf("test_decode_incomplete_returns_zero\n");
    uint8_t out[ONEX_MAX_FRAME];
    const uint8_t pl[] = { 1, 2, 3, 4 };
    const size_t n = onex_frame_encode(ONEX_EVT_BATTERY, 5, pl, sizeof pl, out);

    int all_zero = 1;
    /* Jedes echte Praefix muss "warte auf mehr" sagen -- nie ein Fehler. */
    for (size_t cut = 0; cut < n; ++cut) {
        onex_hdr_t hdr;
        const uint8_t *p = NULL;
        if (onex_frame_decode(out, cut, &hdr, &p) != 0) { all_zero = 0; }
    }
    check(all_zero, "jedes Praefix -> 0 (unvollstaendig, kein Fehler)");

    onex_hdr_t hdr;
    const uint8_t *p = NULL;
    check_eq_int(onex_frame_decode(out, n, &hdr, &p), (int)n,
                 "vollstaendiger Frame -> Laenge");
}

static void test_decode_crc_error(void)
{
    printf("test_decode_crc_error\n");
    uint8_t out[ONEX_MAX_FRAME];
    const uint8_t pl[] = { 0x42, 0x43 };
    const size_t n = onex_frame_encode(ONEX_CMD_FAN, 9, pl, sizeof pl, out);

    out[7] ^= 0x01;   /* ein gekipptes Payload-Bit */

    onex_hdr_t hdr;
    const uint8_t *p = NULL;
    check_eq_int(onex_frame_decode(out, n, &hdr, &p), ONEX_DEC_ERR_CRC,
                 "gekipptes Bit -> ERR_CRC");
}

static void test_decode_version_error_keeps_seq(void)
{
    printf("test_decode_version_error_keeps_seq\n");
    uint8_t out[ONEX_MAX_FRAME];
    const uint8_t pl[] = { 0xFF };
    size_t n = onex_frame_encode(ONEX_CMD_GET, 0x77, pl, sizeof pl, out);

    /* Fremde Version simulieren -- CRC danach neu bilden, damit der Frame
     * "gueltig uebertragen, aber unbekannte Version" ist. */
    out[2] = 0x02;
    const uint16_t crc = onex_crc16(&out[2], 4 + 1);
    out[n - 2] = (uint8_t)(crc >> 8);
    out[n - 1] = (uint8_t)(crc & 0xFF);

    onex_hdr_t hdr;
    const uint8_t *p = NULL;
    const int r = onex_frame_decode(out, n, &hdr, &p);

    check_eq_int(r, ONEX_DEC_ERR_VERSION, "fremde VER -> ERR_VERSION");
    /* Entscheidend fuer PROTOCOL.md 5: NACK(version) spiegelt die SEQ zurueck,
     * also muss der Decoder sie trotz Fehler liefern -- CRC-gedeckt. */
    check_eq_int(hdr.seq, 0x77, "SEQ bleibt fuer NACK(version) verfuegbar");
    check_eq_int(hdr.ver, 0x02, "gemeldete VER");
}

static void test_decode_version_error_needs_valid_crc(void)
{
    printf("test_decode_version_error_needs_valid_crc\n");
    uint8_t out[ONEX_MAX_FRAME];
    const size_t n = onex_frame_encode(ONEX_CMD_PING, 0x33, NULL, 0, out);

    out[2] = 0x02;   /* VER faelschen, CRC NICHT nachziehen */

    onex_hdr_t hdr;
    const uint8_t *p = NULL;
    /* CRC vor Version: ein korrupter Frame darf nie als Versionsproblem
     * durchgehen, sonst spiegelte das NACK eine ungedeckte SEQ zurueck. */
    check_eq_int(onex_frame_decode(out, n, &hdr, &p), ONEX_DEC_ERR_CRC,
                 "kaputte VER ohne CRC-Fix -> ERR_CRC (nicht VERSION)");
}

static void test_decode_skips_leading_garbage(void)
{
    printf("test_decode_skips_leading_garbage\n");
    uint8_t buf[64];
    const uint8_t garbage[] = { 0x00, 0xFF, 0xA5, 0x11, 0x5A };  /* inkl. Teil-SOF */
    memcpy(buf, garbage, sizeof garbage);

    const uint8_t pl[] = { 0xDE, 0xAD };
    const size_t n = onex_frame_encode(ONEX_EVT_RFKILL, 3, pl, sizeof pl,
                                       &buf[sizeof garbage]);

    onex_hdr_t hdr;
    const uint8_t *p = NULL;
    const int r = onex_frame_decode(buf, sizeof garbage + n, &hdr, &p);

    /* Rueckgabe schliesst den Muell ein -> Aufrufer entfernt genau so viele Bytes. */
    check_eq_int(r, (int)(sizeof garbage + n), "Muell wird mitkonsumiert");
    check_eq_int(hdr.type, ONEX_EVT_RFKILL, "Frame dahinter korrekt gelesen");
    check(p != NULL && p[0] == 0xDE && p[1] == 0xAD, "Payload korrekt");
}

/* --------------------------------------------------------------- Resync */

static void test_resync_makes_progress(void)
{
    printf("test_resync_makes_progress\n");

    /* Zwei Anker: der erste defekt, der zweite echt. */
    uint8_t buf[64];
    size_t i = 0;
    buf[i++] = ONEX_SOF0; buf[i++] = ONEX_SOF1;   /* defekter Anker bei 0 */
    buf[i++] = 0x01; buf[i++] = 0x02; buf[i++] = 0x03; buf[i++] = 0x00;
    buf[i++] = 0x00; buf[i++] = 0x00;             /* falsches CRC */
    const size_t second = i;
    onex_frame_encode(ONEX_CMD_PING, 1, NULL, 0, &buf[second]);

    check_eq_int((long)onex_frame_resync(buf, second + 8), (long)second,
                 "springt auf den naechsten Anker");

    /* Kritischer Fall: Muell VOR dem defekten Anker. Eine Suche ab Index 1
     * faende denselben Anker erneut -> Endlosschleife. */
    uint8_t buf2[64];
    buf2[0] = 0x77; buf2[1] = 0x88;
    memcpy(&buf2[2], buf, second + 8);
    const size_t r2 = onex_frame_resync(buf2, second + 10);
    check(r2 > 2, "ueberspringt den defekten Anker, nicht nur den Muell");
    check_eq_int((long)r2, (long)(second + 2), "landet exakt auf dem zweiten Anker");

    /* Fortschrittsgarantie: nie 0, solange mehr als ein Byte da ist. */
    const uint8_t junk[] = { 0x01, 0x02, 0x03 };
    check_eq_int((long)onex_frame_resync(junk, sizeof junk), 3,
                 "reiner Muell wird komplett verworfen");

    /* Ein abschliessendes 0xA5 kann die erste SOF-Haelfte sein -> behalten. */
    const uint8_t tail[] = { 0x01, 0x02, ONEX_SOF0 };
    check_eq_int((long)onex_frame_resync(tail, sizeof tail), 2,
                 "abschliessendes 0xA5 bleibt erhalten");
}

static void test_stream_recovers_after_corruption(void)
{
    printf("test_stream_recovers_after_corruption\n");

    /* Realistischer Strom: guter Frame, korrupter Frame, guter Frame. */
    uint8_t stream[ONEX_MAX_FRAME * 3];
    size_t w = 0;
    const uint8_t a[] = { 0x01 };
    const uint8_t b[] = { 0x02, 0x03 };

    w += onex_frame_encode(ONEX_EVT_BUTTON, 1, a, sizeof a, &stream[w]);
    const size_t bad_at = w;
    w += onex_frame_encode(ONEX_EVT_BUTTON, 2, b, sizeof b, &stream[w]);
    stream[bad_at + 6] ^= 0xFF;   /* mittleren Frame zerstoeren */
    w += onex_frame_encode(ONEX_EVT_BUTTON, 3, a, sizeof a, &stream[w]);

    /* Empfaengerschleife wie im rk3576_link-Modul. */
    size_t pos = 0;
    uint8_t seqs[8];
    unsigned got = 0, errs = 0, guard = 0;

    while (pos < w && guard++ < 1000u) {
        onex_hdr_t hdr;
        const uint8_t *p = NULL;
        const int r = onex_frame_decode(&stream[pos], w - pos, &hdr, &p);

        if (r > 0) {
            if (got < sizeof seqs) { seqs[got] = hdr.seq; }
            ++got;
            pos += (size_t)r;
        } else if (r < 0) {
            ++errs;
            pos += onex_frame_resync(&stream[pos], w - pos);
        } else {
            break;   /* unvollstaendig -> auf mehr Bytes warten */
        }
    }

    check(guard < 1000u, "Empfaengerschleife terminiert (kein Haenger)");
    check_eq_int((long)errs, 1, "genau ein CRC-Fehler gemeldet");
    check_eq_int((long)got, 2, "beide intakten Frames zugestellt");
    check(got >= 2 && seqs[0] == 1 && seqs[1] == 3,
          "SEQ 1 und 3 kommen an, 2 geht verloren");
}

/* ----------------------------------------------------------------- main */

int main(void)
{
    printf("ONE-X-Link v1 -- Codec-Tests (firmware/rp2350)\n\n");

    test_crc_reference_vector();
    test_encode_wire_layout();
    test_encode_rejects_bad_args();
    test_roundtrip_all_lengths();
    test_decode_incomplete_returns_zero();
    test_decode_crc_error();
    test_decode_version_error_keeps_seq();
    test_decode_version_error_needs_valid_crc();
    test_decode_skips_leading_garbage();
    test_resync_makes_progress();
    test_stream_recovers_after_corruption();

    printf("\n%d Pruefungen, %d Fehler\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
