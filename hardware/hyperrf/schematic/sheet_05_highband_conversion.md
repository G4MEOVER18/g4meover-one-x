# HyperRF Sheet 05 — High-Band-Conversion (3,8 → 6 GHz)

Erweitert die native LMS7002M-Reichweite (~100 kHz–3,8 GHz, VALIDATED_ARCH) per Frequenz-Translation + Filterung auf das **Ziel** 100 kHz–6 GHz (`hyperrf.extended_sdr_target`, **TARGET**). Nur oberhalb ~3,8 GHz aktiv.

> **Statusehrlich:** Die 6-GHz-Reichweite ist **TARGET**, nicht nativ. Kein 6-GHz-Nativ-Claim, kein allgemeiner 60-GHz-SDR (Radar = separate Kachel, Sheet 07).

## Konzept

```
Antenne/Feed ── Vorfilter ──[ Mischer ]── ZF im LMS-Nativband (<3,8 GHz) ── LMS RX
                                │
LMS TX ── ZF ──[ Mischer ]── HB-Filter/PA ── Antenne/Feed   (TX, über RF-Kill)
                                │
                          LO (aus Sheet 02 / dedizierte PLL)
```

| Netz | Rolle | Status |
|---|---|---|
| `HB_LO_*` | Umsetz-LO (kohärenzfähig) | TARGET |
| `HB_RX_IN` / `HB_TX_OUT` | High-Band-Feeds | TARGET |
| `HB_EN` | Aktivierung nur >3,8 GHz | TARGET |

## Bauteile (Klassen, MPN TBD)
- **Mischer** (up/down), **High-Band-SAW/Filter**, ggf. **LNA/PA**, **LO-PLL**. Alle MPN/Werte = TBD 📄, Tuning auf realer HW (**G09**).
- Bandplan (welche Segmente translatiert, Image-Rejection-Strategie) = TBD 📄.

## Kritische Design-Notizen
- **Image-/Spurious-Management:** Filterung vor/nach Mischer; LO-Phasenrauschen (Sheet 02).
- **Umschaltung** nativ ↔ High-Band sauber (Schalter/Isolation), kein Pfad-Konflikt.
- **TX über RF-Kill** (RF-Core Sheet 01) — auch der High-Band-PA.

## ERC-Absicht
Umsetzpfade mit definierten Ein/Aus-Schaltern; `HB_LO_*` kohärenzfähig; PA-Enable über Kill-Gate.

## HOLD / TBD
Mischer/Filter/PA/PLL-MPNs 📄 · Bandplan + Image-Rejection 📄 · Matching (→ G09) · Umschalt-Konzept nativ/High-Band 📄.
