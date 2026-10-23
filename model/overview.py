"""A compact single line diagram of the whole battery system, drawn at a size
that reads on a web page.

PV-04 is the real drawing. It is A1, and an A1 sheet shrunk to the width of a web
panel puts its lettering under 3 px, so this is the same chain with short labels
on a small sheet. Every box sizes itself from its longest line so nothing spills.
"""
import design as D
from gen_dxf import Dxf

B = D.out["battery"]
A = D.out["array"]

W, H = 30000, 15000
HEAD, SUB, PAD = 430, 380, 520
ADV = 0.96

d = Dxf()


def width_of(lines):
    w = len(lines[0]) * ADV * HEAD
    for t in lines[1:]:
        w = max(w, len(t) * ADV * SUB)
    return w + 2 * PAD


def box(x, ymid, lines, layer="08-ELEC"):
    w = width_of(lines)
    h = HEAD + len(lines[1:]) * (SUB + 260) + 2 * PAD
    y = ymid - h / 2
    d.rect(layer, x, y, x + w, y + h)
    d.text("07-TEXT", x + PAD, y + h - PAD - HEAD, HEAD, lines[0])
    for i, t in enumerate(lines[1:]):
        d.text("07-TEXT", x + PAD, y + h - PAD - HEAD - 260 - (i + 1) * SUB - i * 260, SUB, t)
    return x + w


MID, GAP = 7600, 1300
x = 900
x = box(x, MID, ["BATTERY", "9 x CQ7", "63.18 kWh"], "11-BATTERY")
d.line("09-CABLE", x, MID, x + GAP, MID); x += GAP
x = box(x, MID, ["DC ISOLATOR", "125 A MCB"])
d.line("09-CABLE", x, MID, x + GAP, MID); x += GAP
inv_x = x
x = box(x, MID, ["INVERTER", "P3-80-Plus", "80 kW HYBRID", "3 BATT PORTS"])
inv_r = x

# PV arrives from above
pv_w = width_of(["PV ARRAY", "78.88 kWp"])
pv_x = inv_x + ((inv_r - inv_x) - pv_w) / 2
box(pv_x, MID + 3500, ["PV ARRAY", "78.88 kWp"])
d.line("09-CABLE", pv_x + pv_w / 2, MID + 2445, pv_x + pv_w / 2, MID + 1695)

# grid above, EPS below
d.line("09-CABLE", inv_r, MID + 900, inv_r + GAP, MID + 900)
gx = box(inv_r + GAP, MID + 900, ["AC ISOLATOR", "160 A MCCB"])
d.line("09-CABLE", gx, MID + 900, gx + GAP, MID + 900)
d.circle("08-ELEC", gx + GAP + 900, MID + 900, 900)
d.text("07-TEXT", gx + GAP + 170, MID + 710, 380, "GRID")

d.line("09-CABLE", inv_r, MID - 1900, inv_r + GAP, MID - 1900)
box(inv_r + GAP, MID - 1900, ["EPS BOARD", "15 kW BACKUP"])

# earth off the inverter
ex = inv_x + 1400
d.line("10-EARTH", ex, MID - 1800, ex, MID - 3400)
d.line("10-EARTH", ex - 560, MID - 3400, ex + 560, MID - 3400)
d.line("10-EARTH", ex - 340, MID - 3760, ex + 340, MID - 3760)
d.line("10-EARTH", ex - 140, MID - 4120, ex + 140, MID - 4120)

d.text("07-TEXT", 900, H - 1600, 600, "BATTERY SYSTEM, SINGLE LINE")
d.text("07-TEXT", 900, H - 2350, 400, "DWG PV-04, SHOWN IN FULL DETAIL ON A1")
d.text("07-TEXT", 900, 800, 360, "80 kW ROOFTOP PV WITH BATTERY STORAGE    DRAWN USAMA JAVED")

open("sld-overview.dxf", "w", encoding="latin1", newline="").write(d.dumps())
open("sld-overview.scr", "w", encoding="latin1", newline="").write(d.dumps_scr("Battery system single line, overview"))
print("overview written, %d entities" % len(d.e))
