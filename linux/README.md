# ONE-X — Linux-Plattform (`linux/`)

Linux-Bringup, Device-Tree und ONE-X-UI für den RK3576-Host. Dieser Ordner deckt **Phase 1 / Gate G01** der [Roadmap](../docs/ROADMAP.md) ab: den **5″-DSI-Display-Bringup**.

> **Status-Disziplin:** Das Display ist als _Fähigkeit_ **FIXED** (5,0″ IPS, 720×1280 nativ / 1280×720 Landscape, 4-lane MIPI-DSI direkt vom RK3576, Touch über I²C).
> Der **Treiber/Bringup** ist jedoch **HOLD** (`display.driver_gate` in der [Master-Spec](../spec/G4MEOVER-ONE-X_MASTER_SPEC.json)): Panel-Init, Device-Tree und DRM/KMS-Validierung müssen **auf echter RK3576-Hardware** nachgewiesen werden. Nichts in diesem Ordner ist „produktionsfertig", bevor G01 real geschlossen ist.

---

## Was hier FIXED ist (aus der Master-Spec)

| Parameter | Wert | Status |
|---|---|---|
| Panel-Klasse | 5,0″ IPS kapazitiver Touch | FIXED |
| Auflösung | 720×1280 nativ, 1280×720 Landscape (SW-Rotation) | FIXED |
| Host-Interface | 4-lane MIPI-DSI direkt vom RK3576 | FIXED |
| Touch-Interface | I²C in den RK3576/Linux-Input-Pfad (RP2350 nur Wake-IRQ) | FIXED |
| SoC | Rockchip RK3576 | FIXED |

## Was TARGET / HOLD ist (nicht als gesetzt behandeln)

| Punkt | Status | Blocker |
|---|---|---|
| EVT-Referenzpanel (Waveshare 5-DSI-TOUCH-B / äquiv.) | TARGET | genaue MPN kann sich ändern |
| Produktions-Panel-Klasse (ILI9881C-Klasse + GT911-Klasse) | TARGET | Bauteilauswahl offen |
| Panel-Init-Sequenz, DSI-PHY-Timings | HOLD | aus Panel-Datenblatt + reale DRM-Validierung |
| GPIO-/I²C-Pin-Zuordnung final | HOLD | erst nach Mainboard-Schaltplan (Phase 5, Gate G07) |
| RK3576-DT-Node-Labels (`&dsi*`, `&vop*`, `&mipidcphy*`) | HOLD | gegen tatsächliches RK3576-BSP/DTSI verifizieren |

---

## Bringup-Strategie (G01)

G01 wird **auf einem RK3576-Devboard** validiert, _bevor_ das ONE-X-Mainboard existiert — so wird das Display-Risiko früh und unabhängig vom Custom-Layout geschlossen.

```
RK3576-Devboard ──4-lane DSI──▶ 5" 720×1280 Panel (ILI9881C-Klasse)
        │  └─I²C──▶ Touch-Controller (GT911-Klasse)  ─IRQ─▶ (später RP2350 Wake)
        └─ DRM/KMS ▶ Wayland/Weston ▶ ONE-X-UI (Landscape via SW-Rotation)
```

Reihenfolge in [`BRINGUP_CHECKLIST_G01.md`](BRINGUP_CHECKLIST_G01.md).

## Ordnerinhalt

| Pfad | Inhalt |
|---|---|
| `BRINGUP_CHECKLIST_G01.md` | Schritt-für-Schritt-Checkliste (Panel-Power → DSI → DRM → Touch → Suspend/Resume) |
| `device-tree/rk3576-one-x-panel5.dtso` | **Device-Tree-Overlay-Skelett** (Panel + Touch), mit markierten Verify-/HOLD-Stellen |
| `device-tree/Makefile` | Overlay mit `dtc` bauen |
| `panel/PANEL_CANDIDATE.md` | Panel-/Touch-Kandidat, Datenblatt-Datenpunkte, Offene Fragen |

## Bauen (Overlay)

```sh
cd device-tree
make            # erzeugt rk3576-one-x-panel5.dtbo (Kernel-Header-Pfad ggf. anpassen)
```

> Das Overlay ist ein **Skelett**: Es kompiliert strukturell, aber Node-Labels, Pin-Nummern und Panel-Init sind mit `/* VERIFY */` bzw. `/* HOLD */` markiert und müssen vor jedem realen Flash gegen das RK3576-BSP und das Panel-Datenblatt gesetzt werden.
