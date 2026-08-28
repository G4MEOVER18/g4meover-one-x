# Sheet 05 — UFS ⛔ BLOCKIERT (Gate G03)

256 GB UFS-Speicher am RK3576-UFS-Host. **Kapazität FIXED (256 GB)**, aber **Generation/MPN HOLD** — dieses Sheet wird **nicht finalisiert**, bis G03 mit einem für den RK3576-Host validierten Device geschlossen ist.

> Interface-Matrix: „RK3576 public host spec UFS2.0; choose validated device." Forbidden Claim: „256GB UFS 3.1 production-confirmed".

## Warum blockiert
Der RK3576-UFS-Host unterstützt öffentlich **UFS 2.0**. Ein konkretes UFS-Device (Generation, M-PHY-Gear, MPN) muss **gegen diesen Host validiert** sein — sonst Boot-/Link-Up-Risiko. Keine „UFS 3.1 bestätigt"-Aussage ohne Validierung.

## Anforderungen

| Punkt | Wert/Status |
|---|---|
| Kapazität | 256 GB — **FIXED** |
| Schnittstelle | UFS M-PHY — **FIXED** |
| Host-Spec | RK3576 public: **UFS 2.0** |
| Device-Generation/MPN | **HOLD (G03)** 📄 |
| M-PHY-Gear/Lanes | nach Device + Host-Validierung 📄 |

## Was zum Schließen von G03 gebraucht wird
1. Für RK3576-UFS-Host **validiertes** UFS-Device (Generation + MPN), 256 GB.
2. Referenz-Layout/-Impedanz (M-PHY-Paare, 100 Ω diff).
3. Boot-Reihenfolge-Bestätigung (UFS als Primär-Boot vs. SPI-NOR/SD).

## Nach G03 (dann erst)
Vollständiges Sheet: `UFS_TX_P/N`, `UFS_RX_P/N`, `REF_CLK`, `RESET_n`, Versorgungen (`VCC`/`VCCQ`/`VCCQ2`), Entkopplung — plus Layout-Constraints (Sheet 08).

**Status: ⛔ nicht finalisieren, nicht als produktionsbestätigt darstellen.**
