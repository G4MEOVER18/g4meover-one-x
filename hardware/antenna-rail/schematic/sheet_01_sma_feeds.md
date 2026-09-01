# Antenna-Rail Sheet 01 — SMA-Feeds / Matching / ESD

Die 4 externen SMA-Ports mit impedanzkontrollierten Feeds, vorbereiteten Filter-/Matching-Plätzen, ESD und Masse-Rückführung. Feeds kommen über `J_ANT` von RF-Core/HyperRF.

## Ports (4× FIXED, 50 Ω)

| Port | Netz | Vorgesehener Feed (Design-Platzhalter) | Status |
|---|---|---|---|
| SMA1 | `ANT_1` | z. B. Sub-GHz (CC1101/SX1262) | Zuordnung TBD 📄 |
| SMA2 | `ANT_2` | z. B. 2,4 GHz (CC2652P7) | Zuordnung TBD 📄 |
| SMA3 | `ANT_3` | z. B. HyperRF-SDR-Feed | Zuordnung TBD 📄 |
| SMA4 | `ANT_4` | z. B. UHF-RAIN / Ersatz | Zuordnung TBD 📄 |

> Die Zeile „vorgesehener Feed" ist ein **Platzhalter zur Orientierung**, keine eingefrorene Zuordnung. Welcher Radio auf welchem SMA landet, wird mit dem Antennen-/Matching-Konzept festgelegt (G09).

## Matching / Filter (vorbereitet, Werte TBD)
- Je Feed ein **Pi-/L-Matching-Footprint** (2–3 Plätze) + optional **SAW/Filter-Footprint** — bestückt/getunt **auf realer HW (G09)**. Startwerte = TBD 📄.
- Bei TX-fähigen Feeds: Leistungsfestigkeit der Bauteile beachten (PA-Ausgang).

## ESD / Schutz
- **ESD-Diode** (low-C, RF-tauglich) je SMA gegen statische Entladung am externen Port; Kapazität klein genug, um das Band nicht zu bedämpfen (Wert TBD 📄 je Frequenz).
- Ableitung auf durchgehende Masse.

## Masse / Rückführung
- **50-Ω-kontrollierte** Feeds mit durchgehender Referenz-/Masse-Lage; SMA-Massekragen großflächig angebunden.
- Isolation zwischen benachbarten Feeds (Crosstalk gering); Abstände auf der 18-mm-Rail definieren.

## Kritische Design-Notizen
- **RF-Kill-Bezug:** Sende-Freigabe liegt **vor** dem Feed (RF-Core `sheet_01_supervisor_rfkill.md` / HyperRF-PA-Gate) — die Rail selbst hat keine TX-Autorität.
- **Metallfreie RF-Fenster / Gehäuse:** Feed-Führung mit Mechanik abstimmen (Thermik-Constraint „RF windows kept metal-free").
- **Steckerhöhe/-lage** der SMA gegen Gehäuse-Oberkante (Mechanik).

## ERC-Absicht
Jeder `ANT_n` als 50-Ω-Netz mit genau einer Quelle (Feed von `J_ANT`); Matching-/ESD-Bauteile als bestückungsoptional (DNP bis G09); Masse als Power-Flag.

## HOLD / TBD
Band-/Radio-Zuordnung je SMA 📄 · Matching-/Filter-Werte (→ G09, HW-Tuning) · ESD-Dioden-Kapazität je Band 📄.
