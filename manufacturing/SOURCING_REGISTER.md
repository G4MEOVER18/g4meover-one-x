# Sourcing-Register — von der BOM zur Bestellung

> Erzeugt von `tools/gen_sourcing.py`. **Nicht von Hand bearbeiten** —
> Änderungen gehören in das Werkzeug, damit Beleg und Begründung
> zusammen mit dem Bauteil versioniert bleiben.

Eine Stückliste wird nicht dadurch bestellbar, dass eine Bauteilfamilie
dasteht. Erst ein konkreter Hersteller-MPN mit Package, Temperaturbereich
und Beleg lässt sich einkaufen. Dieses Register trennt deshalb drei
Zustände — und **rät nichts**.

| Zustand | Bedeutung | Positionen |
|---|---|---|
| **ENTSCHIEDEN** | konkreter, bestellbarer MPN + Beleg | 31 von 45 |
| **WAHL_OFFEN** | Familie steht, echte Entscheidung fehlt | 10 von 45 |
| **HOLD** | externe Herstellerdaten nötig (Gate) | 4 von 45 |

---

## Konkretisiert in dieser Runde

Jede Zeile stützt sich auf ein Hersteller-Datenblatt oder eine
Distributorseite. Zwei davon sind **inhaltliche Korrekturen**, keine
bloßen Ergänzungen:

### `U201` → **W25Q128JVSIQ**

- **Package:** SOIC-8 (208 mil) · **Temperatur:** -40..+85 C
- **Begründung:** 16 MB QSPI fuer den RP2350B (Spec: compute.control_mcu FIXED). Suffix SIQ = SOIC-8, Industrietemperatur, breit verfuegbar.
- **Beleg:** https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf | DigiKey 5803943

### `U221` → **MAX98357AETE+T**

- **Package:** TQFN-16 (3x3 mm) · **Temperatur:** -40..+85 C
- **Begründung:** I2S-Eingang (Variante A, nicht B = left-justified). TQFN statt WLP: auf einem EVT-Board loet- und nacharbeitbar.
- **Beleg:** https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf

### `U300` → **BQ25792RQMR**

- **Package:** QFN-29 (4x4 mm) · **Temperatur:** -40..+85 C
- **Begründung:** 2S-Pack (Spec: 2S2P 4x21700). BQ25792 deckt 1-4 Zellen, 5 A, USB-PD-3.0-OTG ab und passt zum TPS25751A-PD-Pfad (Sheet 01).
- **Beleg:** https://www.ti.com/product/BQ25792 | LCSC C2862876

### `U400/U401` → **RTL8211FI-CG**

- **Package:** QFN-40 · **Temperatur:** -40..+85 C
- **Begründung:** BEWUSSTE AENDERUNG gegenueber '-CG': Das Suffix I ist die Industrievariante (-40..+85 C); die Handelsvariante endet bei +70 C. Fuer ein Feld-/Aussengeraet ist das die richtige Wahl. Pin- und funktionskompatibel.
- **Beleg:** https://www.realtek.com/en/products/communications-network-ics/item/rtl8211f-i-cg

### `U623` → **NEO-F10N-00B-20**

- **Package:** LCC-Modul · **Temperatur:** siehe Datenblatt
- **Begründung:** Die Endung -20 ist NICHT beliebig: nur sie liefert Carrier-Phase-Rohdaten. Die Spec verlangt 'L1/L5 raw' -- die Variante -00 wuerde die Anforderung verfehlen.
- **Beleg:** https://content.u-blox.com/sites/default/files/documents/NEO-F10N_DataSheet_UBX-23002117.pdf

---

## Offene Bauteilentscheidungen

Hier fehlt **kein Herstellerdatum**, sondern eine Produktentscheidung.
Sie wird benannt statt vorweggenommen — ein plausibel klingender MPN wäre
hier genau die Sorte stiller Festlegung, die dieses Repo vermeidet.

> `U624` erscheint zusätzlich in der HOLD-Tabelle und **bleibt dort**.
> Die Varianten-Nomenklatur ist zwar geklärt, aber ein Gate schließt sich
> erst, wenn die Wahl getroffen und in der Master-Spec eingetragen ist —
> nicht dadurch, dass jemand die Auswahl verstanden hat.

### `U624` — Qorvo DW3000-Serie (Gate G05)

**Frage:** Welche der vier Varianten? Die Nomenklatur ist DW3<Package><Ports>0: DW31x0 = WLCSP, DW32x0 = uQFN; DWx1x0 = 1 Antennenport, DWx2x0 = 2 Ports (PDoA/Winkelmessung).

**Abwägung:** uQFN gibt ~2 dB weniger TX-Leistung als WLCSP, ist aber auf einem HDI-EVT deutlich besser zu bestuecken und nachzuarbeiten. PDoA kostet nochmals ~1 dB, ermoeglicht aber Winkelmessung.

**Empfehlung:** DW3220 (uQFN, 2 Ports), falls Winkelmessung gewuenscht ist; sonst DW3210. Die Master-Spec fordert nur 'DW3000-series' -- PDoA ist damit eine Produktentscheidung, keine Vorgabe.

**Beleg:** https://www.qorvo.com/products/p/DW3210 | https://forum.qorvo.com/t/dw3000-series-options/13450

### `U503` — Silicon Labs Z-Wave 800 (Gate G09)

**Frage:** SoC (EFR32ZG23, QFN40 5x5 oder QFN48 6x6) oder vorzertifiziertes Modul (ZGM230S, 6,5x6,5 mm)?

**Abwägung:** Der SoC ist kleiner und guenstiger, verlangt aber eigene Funkzulassung. Das Modul bringt die Zulassung mit -- bei einem Geraet mit dieser Zahl an Funkstrecken ein erheblicher Unterschied in Aufwand und Risiko.

**Empfehlung:** ZGM230S, solange die Stueckzahl klein ist. Erst bei Serienvolumen lohnt der SoC-Weg.

**Beleg:** https://www.silabs.com/wireless/z-wave/800-series-modem-soc

---

## Weiterhin ohne konkreten MPN

Diese Positionen tragen noch eine Familien- oder Klassenangabe. Sie sind
**nicht** durch fehlende Herstellerdaten blockiert — es fehlt schlicht die
Auswahlrunde. Sie sind der nächste sinnvolle Arbeitsschritt.

| Ref | Subsystem | Familie | Gate |
|---|---|---|---|
| `LCD1` | Display | 5-DSI-TOUCH-B reference class | G01 |
| `U210` | UI | IQS550-class | G07 |
| `U220` | Audio | NAU8822 class | G07 |
| `U410` | Wireless | MT7921AUN / WXT2AM2101 class | G07 |
| `U506` | RF Core | E710 class | G09 |
| `U602/U603` | HyperRF | RFFC5071A class | G09 |
| `J620` | HyperRF | RM530N-GL class | G09 |
| `U621` | HyperRF | BG95-S5 class | G09 |
| `U630` | Radar | IWRL6432W class | G09 |

## HOLD — nur mit externen Daten lösbar

| Ref | Was fehlt | Von wem | Gate |
|---|---|---|---|
| `U102` | Exakte LPDDR5-Topologie und qualifiziertes Teil | Rockchip (Referenzdesign) | G02 |
| `U103` | Für RK3576 validiertes 256-GB-UFS-Teil | Rockchip / UFS-Hersteller | G03 |
| `U610` | FPGA-MPN mit PCIe-2.1-Endpoint + DSP/BRAM | Auswahlverfahren `hardware/hyperrf/fpga-selection/` | G04 |
| `U624` | Variantenwahl (siehe oben) | Produktentscheidung | G05 |

---

## Was das für die Produktionsfreigabe heißt

Solange Positionen in **HOLD** oder **WAHL_OFFEN** stehen, gibt es keine
vollständige Bestell-BOM und damit auch keine Produktionsfreigabe. Das ist
kein Formalismus: Ein Board, dessen Speicher-Topologie nicht feststeht,
lässt sich weder routen noch bestücken.

Der ehrliche Übergabestand an einen Fertiger ist deshalb weiterhin ein
**DFM-/RFQ-Paket** (siehe [`DFM_RFQ_PCBWAY.md`](DFM_RFQ_PCBWAY.md) und
[`ENGINEERING_HANDOFF_MINEWING.md`](ENGINEERING_HANDOFF_MINEWING.md)) —
keine Gerber-Freigabe.
