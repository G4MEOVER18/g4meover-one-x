# Sheet 11 — Wi-Fi 6E / Bluetooth

Wi-Fi-6E + BT-Combo (U410, MediaTek MT7921-Klasse / Gaoshengda-WXT2AM2101-Modul). Interface-Matrix: **FIXED** (antenna clearance). **Host-Bus modulabhängig** — bitte gegen die konkrete MPN bestätigen.

## Host-Interface (modulabhängig — 📄 bestätigen)

| Variante | Bus | Anmerkung |
|---|---|---|
| MT7921**AU**-Klasse | **USB2/USB3** | „AU"-Suffix = USB-Anbindung |
| MT7921**S**-Klasse | **SDIO** | SDIO-Anbindung |
| MT7921 (PCIe) | **PCIe** | PCIe-Anbindung |

> Sheet 03 listet die Wi-Fi-Anbindung als Beispiel `SDIO`; **finaler Bus richtet sich nach der gewählten MPN** (MT7921AUN ⇒ USB). Diese Auswahl hier einfrieren und Sheet-03-Fan-out entsprechend angleichen. Bis dahin `TBD 📄`.

## Netze (Beispiel USB-Variante)

| Netz | Funktion | Status |
|---|---|---|
| `WIFI_USB_D_P/N` (oder `SDIO_*` / `PCIE_*`) | Host-Datenbus | FIXED-Absicht, Bus TBD |
| `BT_UART_*` / `PCM_*` | BT-HCI/Audio (falls getrennt) | TARGET |
| `WIFI_RST_n`, `WIFI_WAKE`, `WL_INT` | Steuerung | FIXED |
| `WIFI_ANT_2G4`, `WIFI_ANT_5G6G` | Antennen-Pfade | FIXED |
| `WIFI_CLK_32K` | Sleep-Clock | TARGET |

## Versorgung
- Modul-Rails aus `+3V3_SYS` (+ ggf. 1V8), Entkopplung nach Modul-Referenz 📄.

## Kritische Design-Notizen
- **Antenne:** Wi-Fi-6E deckt 2,4 / 5 / **6 GHz** — Antennen-Clearance + Keep-out, RF-Fenster metallfrei; Koexistenz mit HyperRF/RF-Core beachten (Isolation).
- **BT-Koexistenz:** falls internes Combo-Coex, Pins nach Modul; sonst Coex-Leitungen vorsehen.
- **Bus-SI:** je nach Variante USB3 (100 Ω diff) / SDIO (Längenabgleich, 50 Ω) / PCIe (100 Ω diff).
- **EMI/Placement:** Modul + Antenne früh im Layout platzieren (bestimmt Gehäuse-RF-Fenster).
- **Testpunkte:** `WIFI_RST_n`, Host-Bus-Kernsignale (→ Sheet 18).

## ERC-Absicht
Host-Bus nach gewählter Variante konsistent; Modul-Rails als Power-Input; Antennenpfade als reguläre Netze zu den Antennen-Feeds. Ungenutzte Modul-Pins als No-Connect.

## HOLD / TBD
- **Host-Bus-Freeze** (USB vs. SDIO vs. PCIe) nach MPN 📄 — danach Sheet 03 angleichen.
- Antennen-Typ/-Platzierung (Gehäuse-RF-Fenster) → Mechanik/Layout.
