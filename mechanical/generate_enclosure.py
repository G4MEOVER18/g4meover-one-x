"""
G4MEOVER ONE-X - Gehaeuse-/Mechanik-Generator (CadQuery)
========================================================
Erzeugt STEP/STL-Referenzen: Gehaeuse, Boards, Akku, Thermik, Antennen-Rail.

Single Source of Truth: ../spec/G4MEOVER-ONE-X_MASTER_SPEC.json
Nichts hier darf der Master-Spec widersprechen. Jeder Mass-Parameter traegt
seinen Spec-Key und Status. Ausgabe = EVT-Referenz-/Kollisionsmodell, KEINE
Fertigungsfreigabe.

Querformat-Formsprache (vgl. docs/graphics/front_layout.svg):
  Touch-Ring links | 5"-Display mittig | D-Pad rechts | 5 Softkeys unten | 4x SMA oben.

Status-Legende:
  FIXED   Projektentscheidung (Aussengeometrie, Boards, Akku-Topologie)
  TARGET  Ziel, exaktes Bauteil kann sich aendern (Displaymodul, Zellmass)
  HOLD    NICHT produktionsbestaetigt behandeln:
            Thermik (Spreader/Fans/Kurven) -> Gate G10
            Akku-Pack-Compliance (UN38.3/BMS/NTC) -> Gate G11
            finaler Eckenradius/Wandstaerke/Stackup -> nach DFM (G06/G08)
"""

import cadquery as cq
from cadquery import exporters
from pathlib import Path

OUT_STEP = Path(__file__).resolve().parents[1] / "CAD_STEP"
OUT_STL  = Path(__file__).resolve().parents[1] / "STL"
OUT_STEP.mkdir(parents=True, exist_ok=True)
OUT_STL.mkdir(parents=True, exist_ok=True)

# === Aussengehaeuse === (FIXED: mechanical.device_envelope_mm = 230x110x64)
W, H, D = 230.0, 110.0, 64.0
FRONT_D = 14.0            # Fronttiefe (Design)
REAR_D = D - FRONT_D
WALL = 2.4               # Wandstaerke (TARGET, DFM)
CORNER = 9.0             # Eck-Chamfer (TARGET, Formsprache "rugged")

# === Display === (FIXED Fenster / TARGET Modul)
DISPLAY_MODULE_W = 135.65   # TARGET Modul-Aussenmass (ILI9881C-Klasse)
DISPLAY_MODULE_H = 78.56    # TARGET
DISPLAY_MODULE_T = 4.2      # TARGET
DISPLAY_WINDOW_W = 112.5    # FIXED: mechanical.visible_display_window_mm.x
DISPLAY_WINDOW_H = 64.5     # FIXED: mechanical.visible_display_window_mm.y
DISPLAY_Y = 4.0             # Y-Versatz (Design: Platz fuer Softkey-Reihe unten)

def chamfered_prism(w,h,d,c=8.0,z=0.0):
    pts=[
        (-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),
        (w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)
    ]
    return cq.Workplane("XY").polyline(pts).close().extrude(d).translate((0,0,z))

def rect_cut(x,y,w,h,z0=-2,d=24):
    return cq.Workplane("XY").rect(w,h).extrude(d).translate((x,y,z0))

def circle_cut(x,y,r,z0=-2,d=24):
    return cq.Workplane("XY").circle(r).extrude(d).translate((x,y,z0))

# Front face.
face = chamfered_prism(W,H,3.2,CORNER,0)
face = face.cut(rect_cut(0,DISPLAY_Y,DISPLAY_WINDOW_W,DISPLAY_WINDOW_H))

# D-Pad rechts (FIXED: mechanical.dpad_envelope_mm = 34x34), 5 Softkeys unten, SMA/Sensoren.
DPAD_X, DPAD_Y = 91.5, 5.0
face = face.cut(rect_cut(DPAD_X,DPAD_Y,34,9).union(rect_cut(DPAD_X,DPAD_Y,9,34)))
for x in [-28,-14,0,14,28]:
    face = face.cut(rect_cut(x,-48,10,5))
for x,y,w,h in [(-50,48,11,5),(-35,48,11,5),(111,8,7,18)]:
    face = face.cut(rect_cut(x,y,w,h))
for xx in [-103,-99,-95]:
    face = face.cut(circle_cut(xx,40,1.0))
for xx in [96,100,104]:
    for yy in [38,42]:
        face = face.cut(circle_cut(xx,yy,0.8))

outer_rim = chamfered_prism(W,H,FRONT_D-3.2,CORNER,3.2)
inner_rim = chamfered_prism(W-2*WALL,H-2*WALL,FRONT_D-2.0,CORNER-2.0,3.0)
front_shell = face.union(outer_rim.cut(inner_rim)).clean()

# Rear body.
rear_outer = chamfered_prism(W,H,REAR_D,CORNER,-REAR_D)
rear_inner = chamfered_prism(W-2*WALL,H-2*WALL,REAR_D-WALL,CORNER-2.0,-REAR_D+WALL)
rear_shell = rear_outer.cut(rear_inner).clean()

backplate_w, backplate_h = 166.0, 82.0
rear_shell = rear_shell.cut(rect_cut(24,0,backplate_w,backplate_h,z0=-REAR_D-4,d=8))
backplate = chamfered_prism(backplate_w,backplate_h,3.0,6.0,-REAR_D-3.0).translate((24,0,0))
for y in [-25,-18,-11,-4,3,10,17,24]:
    for x in [10,18,26,34,42]:
        backplate = backplate.cut(rect_cut(x,y,5.5,1.8,z0=-REAR_D-5,d=8))
for x,y,w,h in [(72,24,24,12),(72,-24,24,12),(92,0,18,22),(45,-31,18,10)]:
    backplate = backplate.cut(rect_cut(x,y,w,h,z0=-REAR_D-5,d=8))

# Display and controls.
display_module = cq.Workplane("XY").box(DISPLAY_MODULE_W,DISPLAY_MODULE_H,DISPLAY_MODULE_T,centered=(True,True,False)).translate((0,DISPLAY_Y,3.4))
display_active = cq.Workplane("XY").box(110.4,62.1,0.8,centered=(True,True,False)).translate((0,DISPLAY_Y,2.8))  # TARGET aktive Flaeche
touch_ring = cq.Workplane("XY").circle(20).circle(16).extrude(2.0).translate((-91.0,4.0,0.8))  # FIXED Touch-Ring Oe40 (r=20), links
dpad = cq.Workplane("XY").rect(31,8).extrude(2.5).union(cq.Workplane("XY").rect(8,31).extrude(2.5)).union(cq.Workplane("XY").circle(5).extrude(2.5)).translate((DPAD_X,DPAD_Y,0.7))
softkey = cq.Workplane("XY").rect(9.5,4.5).extrude(2.4)

# Board dummies. (FIXED Outlines: pcb.*_outline_mm)
main_pcb = cq.Workplane("XY").box(210,92,1.2,centered=(True,True,False)).translate((0,0,-4.5))     # FIXED 210x92
ui_outer = cq.Workplane("XY").box(218,100,0.8,centered=(True,True,False)).translate((0,0,8.0))     # FIXED 218x100
ui_cut = cq.Workplane("XY").box(138,81,2.0,centered=(True,True,False)).translate((0,DISPLAY_Y,7.5)) # FIXED Recess 138x81
ui_carrier = ui_outer.cut(ui_cut)
rf_core = cq.Workplane("XY").box(92,66,0.8,centered=(True,True,False)).translate((54,10,-18))       # FIXED 92x66
hyperrf = cq.Workplane("XY").box(136,72,1.0,centered=(True,True,False)).translate((35,0,-29))       # FIXED 136x72
m2_bridge = cq.Workplane("XY").box(30,52,0.8,centered=(True,True,False)).translate((10,0,-16))      # FIXED 30x52

# Akku: 2S2P, 4x 21700 (FIXED Topologie: battery.topology). Zellmass TARGET.
# HOLD: Pack-Compliance (UN38.3 / BMS / Sicherung / NTC / mech. Schutz) -> Gate G11.
cell_d, cell_l = 21.55, 70.15   # TARGET 21700-Zellmass
cell_shapes=[]
for yy in [-33,-11,11,33]:
    wp = cq.Workplane("YZ").circle(cell_d/2).extrude(cell_l).translate((-85,yy,-32))
    cell_shapes.append(wp.val())
battery_cells = cq.Compound.makeCompound(cell_shapes)
battery_tray_outer = cq.Workplane("XY").box(76,92,24,centered=(True,True,False)).translate((-50,0,-43))
battery_tray_inner = cq.Workplane("XY").box(72,88,22,centered=(True,True,False)).translate((-50,0,-42))
battery_tray = battery_tray_outer.cut(battery_tray_inner)

# Thermal. HOLD: reale Fan-P/Q-Kurven + 3D-CFD/Mess-EVT ersetzen diese Platzhalter -> Gate G10.
# Spreader/Fans hier sind Kollisions-/Bauraum-Referenzen, KEINE thermisch validierten Bauteile.
main_spreader = cq.Workplane("XY").box(150,82,2.0,centered=(True,True,False)).translate((25,0,-9))
hyper_spreader = cq.Workplane("XY").box(142,78,2.0,centered=(True,True,False)).translate((35,0,-35))
for x,y,w,h in [(72,24,26,14),(72,-24,26,14),(92,0,20,24)]:
    hyper_spreader = hyper_spreader.cut(cq.Workplane("XY").box(w,h,5,centered=(True,True,False)).translate((x,y,-36)))
fan1 = cq.Workplane("XY").box(30,30,5,centered=(True,True,False)).translate((10,22,-41))
fan2 = cq.Workplane("XY").box(30,30,5,centered=(True,True,False)).translate((10,-22,-41))

# Antenna rail. (FIXED: pcb.antenna_rail_mm = 150x18; external_sma_ports = 4)
rail = cq.Workplane("XY").box(150,18,10,centered=(True,True,False)).translate((28,46,-52))
for x in [-40,-13,14,41]:
    hole = cq.Workplane("XZ").circle(3.2).extrude(24).translate((28+x,35,-47))
    rail = rail.cut(hole)

parts={
    "front_shell":front_shell,
    "rear_shell":rear_shell,
    "service_backplate":backplate,
    "display_module_reference":display_module,
    "display_active_area_reference":display_active,
    "touch_ring":touch_ring,
    "dpad":dpad,
    "softkey":softkey,
    "main_pcb_dummy":main_pcb,
    "ui_carrier_dummy":ui_carrier,
    "rf_core_dummy":rf_core,
    "hyperrf_dummy":hyperrf,
    "m2_bridge_dummy":m2_bridge,
    "battery_tray_4x21700":battery_tray,
    "battery_cells_4x21700_dummy":battery_cells,
    "main_spreader":main_spreader,
    "hyperrf_spreader":hyper_spreader,
    "fan_30x30x5_dummy_1":fan1,   # dual low-profile blowers (Spec) — beide exportieren
    "fan_30x30x5_dummy_2":fan2,
    "antenna_rail_4sma":rail,
}
for name,shape in parts.items():
    exporters.export(shape,str(OUT_STEP/f"{name}.step"))
    exporters.export(shape,str(OUT_STL/f"{name}.stl"))

assembly_shapes = [
    front_shell.val(), rear_shell.val(), backplate.val(),
    display_module.val(), touch_ring.val(), dpad.val(),
    main_pcb.val(), ui_carrier.val(), rf_core.val(), hyperrf.val(),
    battery_tray.val(), battery_cells, main_spreader.val(),
    hyper_spreader.val(), fan1.val(), fan2.val(), rail.val()
]
assembly = cq.Compound.makeCompound(assembly_shapes)
exporters.export(assembly,str(OUT_STEP/"ONE-X_EVT6_ASSEMBLY_REFERENCE.step"))

# --- Zusammenfassung / Bauraum-Plausibilitaet -------------------------------
bb = assembly.BoundingBox()
print(f"[ONE-X] {len(parts)} Teile exportiert nach {OUT_STEP} und {OUT_STL}")
print(f"[ONE-X] Assembly-Bounding-Box: "
      f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm "
      f"(FIXED-Envelope 230 x 110 x 64)")
if bb.xlen > W + 0.5 or bb.ylen > H + 0.5 or bb.zlen > D + 0.5:
    print("[ONE-X] WARNUNG: Bounding-Box ueberschreitet das FIXED-Envelope — pruefen!")
print("[ONE-X] HOLD-Erinnerung: Thermik (G10) und Akku-Pack-Compliance (G11) sind "
      "NICHT validiert; Ausgabe ist EVT-Referenz, keine Fertigungsfreigabe.")
