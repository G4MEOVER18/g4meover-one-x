# Sheet 10 — Ethernet ×2

Zwei Gigabit-Ethernet-Ports (U400/U401, Realtek RTL8211F-CG-Klasse) an den RK3576-GMACs über **RGMII0/1**. Interface-Matrix: **FIXED** (reference RGMII/MDI layout).

## Struktur (je Port)

```
RK3576 GMAC ──RGMII──▶ RTL8211F-CG ──MDI──▶ Magnetics ──▶ RJ45 (mit LEDs)
             `MDIO/MDC`        `+3V3` / `+1V0` (intern)
```

## Netze (Port 0 / Port 1 analog)

| Netz | Funktion | Status |
|---|---|---|
| `RGMII0_TXD0..3`, `RGMII0_TX_CTL`, `RGMII0_TXC` | RGMII TX | FIXED |
| `RGMII0_RXD0..3`, `RGMII0_RX_CTL`, `RGMII0_RXC` | RGMII RX | FIXED |
| `MDIO`, `MDC` | Management (gemeinsam/adressiert) | FIXED |
| `ETH0_MDI0..3_P/N` | MDI-Paare → Magnetics/RJ45 | FIXED |
| `ETH0_RST_n`, `ETH0_INT_n` | Reset/Interrupt | FIXED |
| `ETH0_LED_*` | Link/Act-LEDs | — |

## Versorgung
- PHY-Rails aus `+3V3_SYS` (+ interner Core-Regler des PHY, je Datenblatt 📄).
- Magnetics-Center-Taps + Bob-Smith-Termination am RJ45.

## Kritische Design-Notizen
- **RGMII-Timing:** TX/RX-Clock-Delay-Modus definieren (PHY-intern vs. Board-Delay) — häufigster Ethernet-Bug. Referenz-Layout von Realtek 📄.
- **RGMII SI:** ~50 Ω SE, Längenabgleich innerhalb TXD/RXD-Gruppe, kurze Stichleitungen.
- **MDI:** 100 Ω diff bis Magnetics; ESD/Überspannung am Connector; galvanische Trennung durch Magnetics.
- **MDIO-Adressierung:** zwei PHYs → eindeutige PHY-Adressen per Strap.
- **EMI:** Ethernet-Paare von RF-Fenstern/Antennen fernhalten.
- **Testpunkte:** `MDC/MDIO`, `ETH*_RST_n` (→ Sheet 18).

## ERC-Absicht
RGMII-Busse pro Port eindeutig benannt; MDIO/MDC als Bus; PHY-Rails als Power-Input; LED/Reset als reguläre Signale mit Pulls.

## HOLD / TBD
- RGMII-Delay-Strategie + PHY-Strap-Adressen (Referenz-Layout) 📄.
- Integrierte Magnetics-RJ45 vs. diskret (Bauraum) 📄.
