"""PV-01, the mechanical drawing: roof layout, row setting out, mounting section,
plant room. A1 at 1:100, details at the scales noted on each."""
import math
import design as D
from gen_dxf import Dxf, border, SHEET_W, SHEET_H

M = D.out["mech"]
A = D.out["array"]
B = D.out["battery"]

d = Dxf()
border(d, "PV-01", "80 kW ROOFTOP PV WITH 63 kWh BATTERY STORAGE",
       "MECHANICAL LAYOUT AND ARRAY SETTING OUT", "1:100 @ A1, DETAILS AS NOTED")


def dash(layer, x1, y1, x2, y2, seg=300, gap=200):
    """A dashed line that starts and ends on a dash."""
    L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    n = max(1, round((L + gap) / (seg + gap)))
    g = (L - n * seg) / (n - 1) if n > 1 else 0.0
    if n == 1:
        seg = L
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    for k in range(n):
        t = k * (seg + g)
        e = min(t + seg, L)
        d.line(layer, x1 + ux * t, y1 + uy * t, x1 + ux * e, y1 + uy * e)

# ------------------------------------------------------------------ roof plan
RX, RY = 6000, 31000
RW, RH = M["roof"]
PAR = 200
d.rect("01-ROOF", RX, RY, RX + RW, RY + RH)
d.rect("01-ROOF", RX + PAR, RY + PAR, RX + RW - PAR, RY + RH - PAR)

row_len = M["row_length"]
side = (RW - row_len) / 2.0
SOUTH = PAR + 3000.0                      # 3000 mm clear from the parapet inner face
AX, AY = RX + side, RY + SOUTH
mw, proj, gap = D.MOD["length"], M["projected_depth"], 20

for r in range(M["rows"]):
    y0 = AY + r * M["pitch_used"]
    for c in range(M["per_row"]):
        x0 = AX + c * (mw + gap)
        d.rect("03-PV-MODULE", x0, y0, x0 + mw, y0 + proj)
    d.line("02-MOUNT", AX - 300, y0, AX + row_len + 300, y0)
    d.line("02-MOUNT", AX - 300, y0 + proj, AX + row_len + 300, y0 + proj)
    d.text("07-TEXT", RX + RW + 700, y0 + proj / 2 - 120, 250, "STRING %d" % (r + 1))

tr_y = AY + (M["rows"] - 1) * M["pitch_used"] + proj + 1400
TX = AX + row_len + 300                    # riser trunking along the east row ends
d.line("09-CABLE", TX, AY + proj / 2, TX, tr_y)
d.line("09-CABLE", AX, tr_y, TX, tr_y)
d.text("07-TEXT", AX, tr_y + 320, 250, "DC TRUNKING, 8 STRING CIRCUITS, 16 x 1C 6 mm2 PV1-F")
CE = RY + RH - PAR - 800                     # sealed cable entry, in the roof field
d.line("09-CABLE", AX + row_len / 2, tr_y, AX + row_len / 2, CE - 260)
d.circle("09-CABLE", AX + row_len / 2, CE, 260)
d.text("07-TEXT", AX + row_len / 2 + 500, CE - 120, 250, "SEALED CABLE ENTRY")

d.text("07-TEXT", RX, RY + RH + 1500, 440,
       "ROOF PLAN   %d No. MODULES, %s kWp" % (A["modules"], A["kwp"]))
d.text("07-TEXT", RX, RY + RH + 800, 270,
       "%d ROWS OF %d, LANDSCAPE, %d deg FIXED TILT, DUE SOUTH.  SCALE 1:100"
       % (M["rows"], M["per_row"], int(M["tilt"])))

nx, ny = RX + RW - 2200, RY + RH + 600
d.line("07-TEXT", nx, ny, nx, ny + 1700)
d.line("07-TEXT", nx, ny + 1700, nx - 380, ny + 950)
d.line("07-TEXT", nx, ny + 1700, nx + 380, ny + 950)
d.text("07-TEXT", nx - 150, ny + 2050, 320, "N")

DH = 260
d.dim_h(RY - 3300, RX, RX + RW, str(RW), h=DH)                                   # overall, outermost
d.dim_h(RY - 1500, AX, AX + row_len, str(int(row_len)), h=DH)                    # array, inside it
d.dim_v(RX - 3400, RY, RY + RH, str(RH), h=DH)
d.dim_v(RX - 1700, AY, AY + M["array_depth"], str(int(M["array_depth"])), h=DH)
d.dim_v(AX + 1500, RY + PAR, AY, str(int(AY - RY - PAR)), h=DH)                 # clear to the parapet
d.dim_v(AX - 1500, AY, AY + M["pitch_used"], str(int(M["pitch_used"])), h=DH)
d.dim_h(RY + 1400, RX, AX, str(int(side)), h=DH)
for x in (RX, RX + RW):                                                          # extension lines
    d.line("06-DIMS", x, RY - 150, x, RY - 3300 - 200)
for x in (AX, AX + row_len):
    d.line("06-DIMS", x, AY - 150, x, RY - 1500 - 200)
for y in (RY, RY + RH):
    d.line("06-DIMS", RX - 150, y, RX - 3400 - 200, y)
for y in (AY, AY + M["array_depth"]):
    d.line("06-DIMS", AX - 150, y, RX - 1700 - 200, y)
d.line("06-DIMS", AX - 300, AY + M["pitch_used"], AX - 1500 - 200, AY + M["pitch_used"])
d.line("06-DIMS", AX, AY - 150, AX, RY + 1400 - 200)

# ------------------------------------------------------------------ detail A, mounting section
SX, SY = 6000, 14000
S = 5.0                                   # 1:20 against a 1:100 sheet
pitch, rise, front, rear = M["pitch_used"], M["rise"], M["rail_front"], M["rail_rear"]
d.text("07-TEXT", SX, SY + 8200, 440, "DETAIL A   MOUNTING SECTION")
d.text("07-TEXT", SX, SY + 7500, 270, "SCALE 1:20, SOUTH ON THE LEFT")
d.line("01-ROOF", SX - 1200, SY, SX + 1.75 * pitch * S, SY)
for k in (0, 1):
    x = SX + k * pitch * S
    xb = x + proj * S
    d.rect("02-MOUNT", x - 250, SY, x + 250, SY + 900)            # front ballast block
    d.rect("02-MOUNT", xb - 250, SY, xb + 250, SY + 900)          # rear ballast block
    d.line("02-MOUNT", x, SY + 900, x, SY + front * S)
    d.line("02-MOUNT", xb, SY + 900, xb, SY + rear * S)
    d.line("03-PV-MODULE", x, SY + front * S, xb, SY + rear * S)
# the shading ray that set the pitch
x0, xb0 = SX, SX + proj * S
tip = SX + (proj + M["shadow"]) * S
dash("06-DIMS", xb0, SY + rear * S, tip, SY + front * S)
profile = math.degrees(math.atan(M["rise"] / M["shadow"]))
mx, my = (xb0 + tip) / 2, SY + (rear + front) / 2 * S
d.line("06-DIMS", mx, my + 80, mx, SY + rear * S + 1100)
d.text("06-DIMS", mx - 250, SY + rear * S + 1820, 250, "SHADING RAY, 21 DEC 09:00 SOLAR TIME")
d.text("06-DIMS", mx - 250, SY + rear * S + 1200, 250,
       "PROFILE ANGLE %.1f deg, SUN %.1f deg, %d mm IN HAND"
       % (profile, M["sun_elevation"], int(M["pitch_used"] - M["pitch_min"])))
d.text("07-TEXT", SX + 400, SY + front * S + 500, 260, "%d deg" % int(M["tilt"]))
d.dim_h(SY - 1600, SX, SX + pitch * S, "PITCH %d" % int(pitch), h=260)
d.dim_v(SX - 2200, SY, SY + front * S, str(int(front)), h=260)
d.dim_v(SX + pitch * S + proj * S + 1600, SY, SY + rear * S, str(int(rear)), h=260)

# ------------------------------------------------------------------ detail B, plant room
PX, PY = 30000, 14000
P = 2.0                                   # 1:50
RW2, RH2 = 6000, 4000
d.text("07-TEXT", PX, PY + 9800, 440, "DETAIL B   PLANT ROOM")
d.text("07-TEXT", PX, PY + 9100, 270, "SCALE 1:50")
DOOR, HINGE = 900, 5900                   # mm, a 900 door near the south east corner, opening in
d.line("01-ROOF", PX, PY, PX + (HINGE - DOOR) * P, PY)
d.line("01-ROOF", PX + HINGE * P, PY, PX + RW2 * P, PY)
d.line("01-ROOF", PX + RW2 * P, PY, PX + RW2 * P, PY + RH2 * P)
d.line("01-ROOF", PX + RW2 * P, PY + RH2 * P, PX, PY + RH2 * P)
d.line("01-ROOF", PX, PY + RH2 * P, PX, PY)
hx = PX + HINGE * P
d.line("01-ROOF", hx, PY, hx, PY + DOOR * P)                              # door leaf, open
for k in range(12):                                                       # its swing
    a0, a1 = math.pi / 2 + k * math.pi / 24, math.pi / 2 + (k + 1) * math.pi / 24
    d.line("06-DIMS", hx + DOOR * P * math.cos(a0), PY + DOOR * P * math.sin(a0),
           hx + DOOR * P * math.cos(a1), PY + DOOR * P * math.sin(a1))

items = [                                 # tag, x from the west wall, width, depth, layer, off the wall
    (1, 600, 730, 305, "08-ELEC", 0),       # wall mounted
    (2, 2000, 660, 360, "11-BATTERY", 200), # floor standing, 200 mm off the wall
    (3, 3300, 600, 300, "08-ELEC", 0),
    (4, 4400, 600, 300, "08-ELEC", 0),
]
front = min(PY + RH2 * P - off * P - h * P for n, xo, w, h, layer, off in items)
dash("06-DIMS", PX + 600 * P, front, PX + 5000 * P, front)               # working space in front of them
dash("06-DIMS", PX + 600 * P, front - 1000 * P, PX + 5000 * P, front - 1000 * P)
d.dim_v(PX + 5100 * P, front - 1000 * P, front, "1000", h=260)
for n, xo, w, h, layer, off in items:
    x = PX + xo * P
    y = PY + RH2 * P - off * P - h * P
    d.rect(layer, x, y, x + w * P, y + h * P)
    d.text("07-TEXT", x + w * P / 2 - 70, y + h * P / 2 - 110, 240, str(n))
d.text("07-TEXT", PX + 700 * P, front - 600 * P, 250, "1000 mm MIN. CLEAR WORKING SPACE")
d.dim_h(PY - 1600, PX, PX + RW2 * P, str(RW2), h=260)
d.dim_v(PX - 1800, PY, PY + RH2 * P, str(RH2), h=260)

legend = [
    "1  FOXESS P3-80-Plus HYBRID INVERTER, 730 x 305, WALL MOUNTED",
    "2  FOXESS CQ7 BATTERY, %d MODULES, 660 x 360 FOOTPRINT" % B["modules"],
    "3  AC PANEL WITH 160 A 4 POLE MCCB",
    "4  EPS BOARD, ESSENTIAL LOADS",
    "DOOR 900 mm, OPENING IN, AT THE SOUTH EAST CORNER",
]
for i, s in enumerate(legend):
    d.text("07-TEXT", PX + 300, PY - 2400 - i * 620, 250, s)

# ------------------------------------------------------------------ notes
NX, NY = 56000, 53600
d.text("07-TEXT", NX, NY, 440, "MECHANICAL NOTES")
notes = [
    "1. ARRAY %d No. JINKO JKM580N-72HL4-V, 2278 x 1134 x 30 mm, LANDSCAPE," % A["modules"],
    "   %d deg FIXED TILT, DUE SOUTH, IN %d ROWS OF %d." % (int(M["tilt"]), M["rows"], M["per_row"]),
    "   ONE ROW IS ONE STRING AND FEEDS ONE MPP TRACKER OF ITS OWN.",
    "2. ROW PITCH IS SET BY THE SHADING CASE, NOT BY A RULE OF THUMB.",
    "   ON 21 DECEMBER AT 09:00 THE SUN IS AT %.1f deg ELEVATION AND" % M["sun_elevation"],
    "   %.1f deg AZIMUTH. THE %d mm BACK EDGE THEN CASTS A %d mm SHADOW." % (
        M["sun_azimuth"], M["rise"], M["shadow"]),
    "   ON TOP OF THE %d mm PROJECTED MODULE DEPTH THAT GIVES %d mm" % (
        M["projected_depth"], M["pitch_min"]),
    "   MINIMUM, ROUNDED UP TO THE %d mm PITCH DRAWN." % int(M["pitch_used"]),
    "3. GROUND COVER RATIO %.2f. ARRAY FOOTPRINT %d x %d mm," % (
        M["ground_cover_ratio"], int(M["row_length"]), int(M["array_depth"])),
    "   WHICH IS %.1f m2 ON A %.0f m2 ROOF, SO THE ARRAY ENVELOPE TAKES %.1f %% OF IT." % (
        M["array_area"], M["roof_area"], M["coverage_pct"]),
    "4. MOUNTING IS BALLASTED. NO ROOF PENETRATION FOR THE FRAME.",
    "   FRONT RAIL %d mm AND REAR RAIL %d mm ABOVE THE MEMBRANE." % (
        int(M["rail_front"]), int(M["rail_rear"])),
    "5. 3000 mm CLEAR TO THE SOUTH PARAPET AND A CLEAR WALKWAY ON THE",
    "   NORTH SIDE FOR ACCESS AND FOR THE DC TRUNKING RUN.",
    "6. THE ONLY ROOF PENETRATION IS THE SEALED CABLE ENTRY SHOWN.",
    "7. BALLAST MASS, UPLIFT AND THE ADDED DEAD LOAD ON THE ROOF ARE TO BE",
    "   CONFIRMED BY A SITE WIND LOAD AND STRUCTURAL ASSESSMENT BEFORE",
    "   INSTALLATION. THE FIGURES ON THIS SHEET ARE DESIGN FIGURES.",
]
for i, s in enumerate(notes):
    d.text("07-TEXT", NX, NY - 900 - i * 620, 250, s)

# ------------------------------------------------------------------ equipment schedule
EX, EY = 56000, 40000
d.text("07-TEXT", EX, EY, 440, "EQUIPMENT SCHEDULE")
cols = [0, 1900, 14500, 18200]
rows = [
    ["No.", "EQUIPMENT", "QTY", "NOTE"],
    ["1", "JINKO JKM580N-72HL4-V 580 W", str(A["modules"]), "2278 x 1134 x 30"],
    ["2", "FOXESS P3-80-Plus INVERTER", "1", "80 kW, 8 MPPT"],
    ["3", "FOXESS CQ7 BATTERY MODULE", str(B["modules"]), "%s kWh TOTAL" % B["kwh_nominal"]],
    ["4", "BALLASTED TILT FRAME 15 deg", "8 ROWS", "FRONT 300, REAR 594"],
    ["5", "DC TRUNKING AND CABLE ENTRY", "1 RUN", "SEALED, SURFACE RUN"],
]
TW = 26000
d.line("08-ELEC", EX, EY - 500, EX + TW, EY - 500)
for r, row in enumerate(rows):
    y = EY - 1200 - r * 620
    for c, cell in enumerate(row):
        d.text("07-TEXT", EX + cols[c], y, 250, cell)
    d.line("08-ELEC", EX, y - 170, EX + TW, y - 170)

# ------------------------------------------------------------------ design summary
GX, GY = 56000, 31000
d.text("07-TEXT", GX, GY, 440, "DESIGN SUMMARY")
summary = [
    ["ARRAY", "%d x 580 W = %s kWp" % (A["modules"], A["kwp"])],
    ["STRINGS", "%d STRINGS OF %d, ONE PER MPP TRACKER" % (A["strings"], A["per_string"])],
    ["TILT AND PITCH", "%d deg, %d mm, GCR %.2f" % (int(M["tilt"]), int(M["pitch_used"]), M["ground_cover_ratio"])],
    ["INVERTER", "FOXESS P3-80-Plus, 80 kW, DC/AC %.2f" % A["dc_ac_ratio"]],
    ["BATTERY", "%s kWh, %s kW CONTINUOUS, %s V NOMINAL" % (B["kwh_nominal"], B["kw_continuous"], B["v_nominal"])],
    ["ARRAY ENVELOPE", "%.1f m2 OF %.0f m2, %.1f %%" % (M["array_area"], M["roof_area"], M["coverage_pct"])],
]
d.line("08-ELEC", GX, GY - 500, GX + TW, GY - 500)
for r, (k, v) in enumerate(summary):
    y = GY - 1200 - r * 620
    d.text("07-TEXT", GX, y, 250, k)
    d.text("07-TEXT", GX + 8000, y, 250, v)
    d.line("08-ELEC", GX, y - 170, GX + TW, y - 170)

open("PV-01 Mechanical Layout.dxf", "w", encoding="latin1", newline="").write(d.dumps())
open("PV-01 Mechanical Layout.scr", "w", encoding="latin1", newline="").write(d.dumps_scr("PV-01 Mechanical Layout"))
print("PV-01 written, %d entities" % len(d.e))
