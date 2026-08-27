# Minewing — Antwort-Mail an Jenny (Overseas Sales)

**An:** jenny@minewing.com
**Betreff:** Re: found a great hardware project creator — let's explore a JDM fit (G4MEOVER ONE-X)
**Anhänge:** `ONE-X_Minewing_JDM_Brief.pdf`, `spec/BOM.csv`, Architektur-Grafik

---

Hi Jenny,

thank you for the kind message — you're right that I like building things that work in the real world, not just on screen. The **stm32-usb-fuzzer** you saw is one of several; the project I'd most like to explore with Minewing is a much bigger one, and it's fully open source:

**G4MEOVER ONE-X** — a modular Linux handheld for RF research, pentesting and networking. It's built around a **Rockchip RK3576**, a 5″ touch display, dual Gigabit Ethernet, a full short-range RF stack, and a modular high-performance SDR/HyperRF subsystem. Repository: **https://github.com/G4MEOVER18/g4meover-one-x**

The architecture (revision EVT6) is synchronized against a single source-of-truth spec, with a full BOM, mechanical CAD/STEP, KiCad floorplans and a thermal pre-check. What I'm looking for now is exactly the **one-stop JDM/engineering support** Minewing describes — 20+ years, CN+VN factories, no MOQ, NDA-ready. Specifically:

1. **Schematic + layout review** for the 12-layer HDI mainboard (RK3576, LPDDR5, UFS, PCIe 2.1 ×1).
2. **SI/PI + DFM** on the high-speed nets (RGMII ×2, PCIe, USB3, MIPI-DSI, LPDDR5).
3. **Component sourcing** for the open HOLD items (exact LPDDR5 topology, UFS device, HyperRF FPGA).
4. **Mechanical + thermal** support (enclosure, dual-spreader cooling, vapor-chamber option).
5. A small **EVT build (5–10 units)** with X-ray BGA, AOI and staged power-up.

I'd be glad to sign an **NDA** before sharing the production-level details. Could we start with a short call, and could you tell me:
- whether RK3576-class + LPDDR5/UFS designs fit your typical scope,
- your process for an NDA + an initial engineering/quotation review,
- and a rough idea of engineering-support vs. per-unit cost at prototype quantity?

Great to connect either way — it's good to know people on a similar wavelength.

Best regards,
Yanis Ameseder (**G4MEOVER18**)
g4me.over.18@gmail.com · github.com/G4MEOVER18

---

## Personalisierungs-Notizen
- Bezug auf **stm32-usb-fuzzer** = das Repo, das Jenny konkret erwähnt hat → zeigt, dass es keine Massen-Mail ist.
- Spiegelt Minewings eigene Sprache: „one-stop", „20+ years", „CN+VN", „no MOQ", „NDA" → Anschlussfähigkeit.
- 5 konkrete Arbeitspakete (matchen genau die HOLD-Gates) statt vager Anfrage.
- Klare, beantwortbare Rückfragen (Scope, NDA-Prozess, grobe Kosten) → senkt Antwortschwelle.
- NDA proaktiv angeboten = professionell, da Minewing Vertraulichkeit selbst betont.
