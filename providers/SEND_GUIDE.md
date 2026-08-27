# Versand-Anleitung — Sponsor-/Partner-Mails

> Die Mails werden **von dir** versendet (nicht automatisch). Diese Anleitung macht den Versand idiotensicher.

## Vor dem Versand (einmalig)
1. Repo öffentlich sichtbar? → https://github.com/G4MEOVER18/g4meover-one-x muss erreichbar sein.
2. README zeigt Sponsoren-Sektion + Vergleich? (ja, siehe README).
3. Optional: Aus `DATA_PACKAGE.md` je Partner ein PDF exportieren (Betreff-Anhänge). Falls kein PDF: den Markdown-Inhalt direkt in die Mail kopieren oder Repo-Link genügt.

## Reihenfolge & Timing
| Schritt | Partner | Wann | Warum |
|---|---|---|---|
| 1 | **PCBWay (Liam)** | zuerst | Konkretes, sofort einlösbares Angebot (freies PCB). Schnellster Win = Gate G06. |
| 2 | **Minewing (Jenny)** | 1–2 Tage später | Größeres Commitment (JDM). Parallel ok, aber PCBWay-Zusage stärkt die Minewing-Story. |

**Bester Zeitpunkt:** Dienstag–Donnerstag, vormittags China-Zeit (CST, UTC+8) → morgens früh MEZ. Vermeide Freitag/Wochenende.

## PCBWay — Liam
- **An:** liam@pcbway.com · **CC optional:** sponsor@pcbway.com
- **Betreff:** `Re: USB Army Penetrator Sponsorship — new open-source project: G4MEOVER ONE-X (12-layer HDI handheld)`
- **Body:** Inhalt aus `pcbway/EMAIL_REPLY.md`.
- **Anhänge:** One-Pager (`pcbway/DATA_PACKAGE.md` → PDF), BOM-Auszug Mainboard, 1 Konzept-Grafik.
- **WhatsApp-Fallback:** 86-15961700899 (nur wenn nach ~1 Woche keine Antwort).

## Minewing — Jenny
- **An:** jenny@minewing.com
- **Betreff:** `Re: found a great hardware project creator — let's explore a JDM fit (G4MEOVER ONE-X)`
- **Body:** Inhalt aus `minewing/EMAIL_REPLY.md`.
- **Anhänge:** JDM-Brief (`minewing/DATA_PACKAGE.md` → PDF), BOM, Architektur-Grafik.
- **WeChat/WhatsApp-Fallback:** +86 17776192691.
- **Hinweis:** NDA proaktiv anbieten (steht in der Mail). Produktions-Details erst nach NDA.

## Nachfassen (Follow-up)
- Keine Antwort nach **5–7 Tagen** → kurze, freundliche Erinnerung (2–3 Sätze), gleiche Betreffzeile.
- Nach **2. Follow-up** ohne Antwort → WhatsApp/WeChat-Kanal probieren.
- Antwort erhalten → passendes „AFTER_REPLY"-Technikpaket nachreichen (siehe `reference_evt6/`-Handoff-Struktur bzw. das jeweilige `DATA_PACKAGE.md`).

## Do / Don't
- ✅ Ehrlich bleiben: KiCad-Dateien sind Floorplans; zuerst DFM/Review, nicht sofort Serienfertigung.
- ✅ Konkrete Fragen stellen (senkt Antwortschwelle).
- ❌ Keine übertriebenen Claims (der Validator hält sie aus dem Repo — die Mail sollte konsistent sein).
- ❌ Keine Produktions-Gerber versprechen, solange HOLD-Gates offen sind.
