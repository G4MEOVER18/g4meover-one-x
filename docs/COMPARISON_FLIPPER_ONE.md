# Einordnung: G4MEOVER ONE-X vs. Flipper One vs. Flipper Zero

## Ausgangslage

Der **Flipper One** wurde am 21.05.2026 von Flipper Devices angekündigt: ein RK3576-basierter Linux-Pocket-Computer mit ~350 $ Zielpreis. Auslieferung an Entwickler frühestens Sommer 2026, kommerzieller Launch ohne festes Datum. Er ist bewusst **kompakt** (2,4″-Display, 8 GB RAM) und primär ein Netzwerk-/Linux-Multitool — **kein SDR-Kraftpaket und kein Touch-Tablet.**

G4MEOVER ONE-X teilt nur die SoC-Klasse (RK3576) und die „Flipper-inspirierte" Formensprache. Ansonsten ist es eine **Kategorie darüber**: stationär-mobiles Feld-Techniksystem mit vollem RF-Stack.

## Direkter Vergleich

| Merkmal | **G4MEOVER ONE-X** | Flipper One (angek. 05/2026) | Flipper Zero |
|---|---|---|---|
| SoC | RK3576 | RK3576 | STM32WB55 (MCU) |
| RAM / Storage | 16 GB LPDDR5 / 256 GB UFS | 8 GB / — | 256 KB / SD |
| Co-Prozessor | RP2350B (Always-On) | RP2350 | — |
| Display | 5,0″ IPS **Multitouch** 1280×720 | 2,4″ 256×144, QSPI | 1,3″ 128×64 mono |
| NPU | (RK3576-integriert) | 6 TOPS | — |
| SDR | **2× LMS7002M, 4RX/4TX, 100 kHz–6 GHz** | — | — |
| Sub-GHz | CC1101 + SX1262 (LoRa/FSK) | CC1101-Klasse | CC1101 |
| NFC/HF | PN7160 | 13,56 MHz | 13,56 MHz |
| LF-RFID | 125 kHz AFE + Coil | — | 125 kHz |
| UHF-RFID | Impinj E710 (RAIN, TARGET) | — | — |
| Mesh/IoT | Zigbee/Thread/BLE (CC2652P7) + Z-Wave LR | teilw. | — |
| Mobilfunk | **5G Sub-6 + mmWave + IoT-NTN-Satellit** | — | — |
| GNSS | u-blox L1/L5 raw + PPS | — | — |
| UWB / Radar | DW3000 + 60-GHz-FMCW-Radar | — | — |
| Netzwerk | 2× GbE, Wi-Fi 6E, USB3, HDMI, M.2 | 2× GbE, Wi-Fi 6E, HDMI 2.1 | — |
| Akku | 4× 21700, 2S2P, ~72 Wh | intern (klein) | 2000 mAh |
| Maße | 230 × 110 × 64 mm, 800–950 g | Pocket | Pocket |

## Die Kernaussage

**Es existiert derzeit kein integriertes Consumer-/Prosumer-Gerät, das ein 5″-Touch-Linux-System, ein kohärentes 4RX/4TX-SDR bis 6 GHz, den vollen kurzreichweitigen RF-Zoo (Sub-GHz/NFC/LF/UHF/Zigbee/Z-Wave), 5G+NTN, GNSS-raw, UWB und 60-GHz-Radar in einem Handheld vereint.** Vergleichbare Fähigkeiten erfordern heute mehrere Geräte (Flipper Zero + HackRF/LimeSDR + Laptop + Modem + GNSS-Empfänger). ONE-X ist der Versuch, das in *einem* Gerät zu bündeln — daher „Overkill".

## Quellen

- CNX Software: Flipper One (RK3576) — https://www.cnx-software.com/2026/05/21/flipper-one-a-rockchip-rk3576-powered-portable-arm-linux-computer-and-networking-multi-tool/
- BigGo: Flipper One $350 Linux Pocket PC — https://finance.biggo.com/news/202605211521_Flipper-One-Open-Linux-Pocket-PC-350-Dollars
- Wikipedia: Flipper Zero — https://en.wikipedia.org/wiki/Flipper_Zero

> Hinweis: Flipper-One-Werte stammen aus öffentlichen Ankündigungen und können sich bis zum Launch ändern. Der Vergleich dient der technischen Einordnung, nicht als Marketingaussage gegen ein fremdes Produkt.
