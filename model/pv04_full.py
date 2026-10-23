"""PV-04, the issued single line diagram for the 80 kW PV and 63 kWh battery.

This is the sheet as it would go out: frame and title block, revision table,
legend, device tags, surge protection on both sides, current transformers and
metering, interface protection with its settings, the existing LV board and the
point of connection, and the earthing arrangement.

Drawn on A1. A key diagram in the bottom left carries the whole chain for anyone
reading it quickly; the schedules sit beside it.
"""
import design as D
import dispatch as X
from gen_dxf import Dxf, SHEET_W, SHEET_H

B, A, S, AC = D.out["battery"], D.out["array"], D.out["string"], D.out["ac"]

ADV = 0.96
H_SEC, H_DEV, H_RAT, H_TAB, H_TH = 400, 300, 240, 240, 270
M = 1000                                   # sheet margin
d = Dxf()


def tw(t, h):
    return len(str(t)) * ADV * h


def ctr(layer, cx, y, h, t):
    d.text(layer, cx - tw(t, h) / 2, y, h, t)


def rt(layer, rx, y, h, t):
    d.text(layer, rx - tw(t, h), y, h, t)


def dash(layer, x1, y1, x2, y2, seg=450, gap=300):
    """Control and signal wiring, drawn as dashes so it reads apart from power."""
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** 0.5
    if L == 0:
        return
    # fit the pattern to the run so it starts and ends on a dash and both ends
    # actually touch what they connect to
    n = max(1, round((L + gap) / (seg + gap)))
    if n == 1:
        seg, gap = L, 0.0
    else:
        gap = (L - n * seg) / (n - 1)
        while n > 1 and gap < 150:
            n -= 1
            gap = (L - n * seg) / (n - 1) if n > 1 else 0.0
        if n == 1:
            seg, gap = L, 0.0
    ux, uy = dx / L, dy / L
    for k in range(n):
        t = k * (seg + gap)
        e = min(t + seg, L)
        d.line(layer, x1 + ux * t, y1 + uy * t, x1 + ux * e, y1 + uy * e)


def dash_rect(layer, x1, y1, x2, y2):
    dash(layer, x1, y1, x2, y1); dash(layer, x2, y1, x2, y2)
    dash(layer, x2, y2, x1, y2); dash(layer, x1, y2, x1, y1)


def run(y, *xs):
    for i in range(len(xs) - 1):
        d.line("09-CABLE", xs[i], y, xs[i + 1], y)


def vrun(x, *ys):
    for i in range(len(ys) - 1):
        d.line("09-CABLE", x, ys[i], x, ys[i + 1])


# ===================================================================== symbols
def s_switch(cx, cy, s=1.0, brk=False, vert=False):
    """Switch disconnector, or a circuit breaker when brk is set."""
    t, b, h = 900 * s, 780 * s, 1200 * s
    def P(a, c):
        return (cx + c, cy + a) if vert else (cx + a, cy + c)
    for a in (-t, t):
        p = P(a, 0); d.circle("08-ELEC", p[0], p[1], 120 * s)
    p1, p2 = P(-t, 0), P(b, h)
    d.line("08-ELEC", p1[0], p1[1], p2[0], p2[1])
    if brk:
        for k in (1, -1):
            q1, q2 = P(-330 * s, (340 + 460 * (k > 0)) * s), P(330 * s, (340 + 460 * (k < 0)) * s)
            d.line("08-ELEC", q1[0], q1[1], q2[0], q2[1])
    return (cy - t, cy + t) if vert else (cx - t, cx + t)


def s_spd(cx, cy, s=1.0):
    """Surge arrester teed off the line: a varistor block with an arrow to earth."""
    w, h = 1100 * s, 1500 * s
    d.line("09-CABLE", cx, cy, cx, cy - 900 * s)
    y0 = cy - 900 * s - h
    d.rect("08-ELEC", cx - w / 2, y0, cx + w / 2, y0 + h)
    d.line("08-ELEC", cx - w / 2, y0, cx + w / 2, y0 + h)       # the varistor slash
    d.line("08-ELEC", cx + w / 2, y0 + h, cx + w / 2 - 420 * s, y0 + h - 120 * s)
    d.line("08-ELEC", cx + w / 2, y0 + h, cx + w / 2 - 120 * s, y0 + h - 420 * s)
    return cx, y0


def s_ct(cx, cy, s=1.0):
    """Current transformer: a core around the conductor, secondary out below."""
    d.circle("08-ELEC", cx, cy, 650 * s)
    d.line("12-CONTROL", cx, cy - 650 * s, cx, cy - 1300 * s)
    return cx, cy - 1300 * s


def s_meter(cx, cy, s=1.0, label="kWh"):
    d.circle("08-ELEC", cx, cy, 1150 * s)
    ctr("08-ELEC", cx, cy - 170 * s, 340 * s, label)
    return cx, cy - 1150 * s


def s_relay(cx, cy, s=1.0, lines=("27/59", "81/ROCOF")):
    w, h = 3400 * s, 1500 * s + len(lines) * 420 * s
    d.rect("08-ELEC", cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    for i, t in enumerate(lines):
        ctr("08-ELEC", cx, cy + h / 2 - 500 * s - i * 420 * s, 300 * s, t)
    return cx, cy - h / 2


def s_tx(cx, cy, s=1.0):
    """Two coupled windings, the incoming distribution transformer."""
    d.circle("08-ELEC", cx, cy + 520 * s, 1000 * s)
    d.circle("08-ELEC", cx, cy - 520 * s, 1000 * s)
    return cy - 1520 * s, cy + 1520 * s


def s_battery(cx, cy, s=1.0):
    for i in range(3):
        x = cx - 1950 * s + i * 1300 * s
        d.line("11-BATTERY", x, cy - 1150 * s, x, cy + 1150 * s)
        d.line("11-BATTERY", x + 650 * s, cy - 560 * s, x + 650 * s, cy + 560 * s)
    return cx - 1950 * s, cx + 1300 * s


def s_pv(x, y, w, h):
    d.rect("03-PV-MODULE", x, y, x + w, y + h)
    d.line("03-PV-MODULE", x, y, x + w, y + h)
    return x, x + w


def s_grid(cx, cy, s=1.0):
    import math as _m
    d.circle("08-ELEC", cx, cy, 1150 * s)
    pts = [(cx - 580 * s + i * 116 * s, cy + 320 * s * _m.sin(i / 10.0 * _m.pi * 2)) for i in range(11)]
    for i in range(10):
        d.line("08-ELEC", pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
    return cx - 1150 * s, cx + 1150 * s


def s_earth(cx, top, s=1.0):
    d.line("10-EARTH", cx, top, cx, top - 1100 * s)
    for i, half in enumerate((1000 * s, 620 * s, 270 * s)):
        y = top - 1100 * s - i * 330 * s
        d.line("10-EARTH", cx - half, y, cx + half, y)


def cores(cx, cy, label, s=1.0):
    """The slash across a conductor that carries its core count."""
    d.line("06-DIMS", cx - 420 * s, cy - 500 * s, cx + 420 * s, cy + 500 * s)
    d.text("06-DIMS", cx + 350 * s, cy + 560 * s, H_RAT * s, label)


def dev(cx, cy, tag, name=None, rating=None, up=True, s=1.0, dy=1700):
    """Tag above a device, name and rating on the other side of the line."""
    ctr("13-TAG", cx, cy + dy * s if up else cy - (dy + 240) * s, H_RAT * s, tag)
    y = cy - (dy + 260) * s if up else cy + dy * s
    for i, (t, h) in enumerate([(name, H_DEV * s), (rating, H_RAT * s)]):
        if t:
            ctr("07-TEXT" if i == 0 else "06-DIMS", cx, y - i * 480 * s, h, t)


# ================================================================ sheet layout
d.rect("00-BORDER", M, M, SHEET_W - M, SHEET_H - M)
d.rect("00-BORDER", M + 300, M + 300, SHEET_W - M - 300, SHEET_H - M - 300)
for i, z in enumerate("FEDCBA"):                      # zone references, A at the top
    y = M + 300 + (i + 0.5) * (SHEET_H - 2 * M - 600) / 6
    ctr("00-BORDER", M + 150, y - 100, 200, z)
    ctr("00-BORDER", SHEET_W - M - 150, y - 100, 200, z)
for i in range(8):
    x = M + 300 + (i + 0.5) * (SHEET_W - 2 * M - 600) / 8
    ctr("00-BORDER", x, M + 50, 200, str(i + 1))
    ctr("00-BORDER", x, SHEET_H - M - 250, 200, str(i + 1))

DRAW_Y0 = 20500
d.line("00-BORDER", M + 300, DRAW_Y0 - 400, SHEET_W - M - 300, DRAW_Y0 - 400)

EBAR = 23000                                          # main earth bar

# ------------------------------------------------------------------ PV array
d.text("07-TEXT", 3200, 57400, H_SEC, "PHOTOVOLTAIC ARRAY")
for k, sy in enumerate((55500, 53000, 50500)):
    s_pv(3200, sy - 800, 4200, 1600)
    d.text("06-DIMS", 3350, sy + 350, H_RAT, "STRING %d" % (k + 1))
    run(sy, 7400, 9600)
    d.line("09-CABLE", 9600, sy, 11400, 52000)        # each string merges into the group, no common node
for x in (3400, 3900, 4400):                          # break mark, strings 4 to 8
    d.line("06-DIMS", x, 48900, x + 200, 49300)
d.text("06-DIMS", 5200, 48900, H_RAT, "STRINGS 4 TO 8 AS ABOVE")
run(52000, 11400, 37500)                              # eight circuits drawn as one line
d.text("06-DIMS", 11800, 53500, H_RAT, "8 SEPARATE STRING CIRCUITS, 1 PER MPPT")
d.text("06-DIMS", 11800, 52900, H_RAT, "NOT PARALLELED, DC SWITCH INTEGRAL TO -TC1")
d.text("13-TAG", 3200, 56700, H_RAT, "-GP1")
for i, t in enumerate(["%d No. JINKO JKM580N 580 W" % A["modules"],
                       "%s kWp, %d STRINGS OF %d IN SERIES" % (A["kwp"], A["strings"], A["per_string"]),
                       "Voc %d V AT -5 C, Isc %s A PER STRING" % (S["voc_cold_string"], A["mppt_isc"])]):
    d.text("06-DIMS", 3200, 47900 - i * 560, H_RAT, t)

_, fv1_e = s_spd(15000, 52000)                        # earth terminal at the foot of the SPD
d.text("13-TAG", 15900, 51200, H_RAT, "-FV1")
d.text("07-TEXT", 15900, 50600, H_DEV, "DC SPD")
d.text("06-DIMS", 15900, 50000, H_RAT, "TYPE 2, 1000 V, 1 PER MPPT, ARRAY END")
d.line("10-EARTH", 15000, fv1_e, 15000, 47500)        # SPD earth, kept clear of -QS2
d.line("10-EARTH", 15000, 47500, 12700, 47500)
d.line("10-EARTH", 12700, 47500, 12700, EBAR)
cores(28000, 52000, "8 CIRCUITS")
d.text("13-TAG", 31400, 52600, H_RAT, "-W1")

# ------------------------------------------------------------------- battery
d.text("07-TEXT", 3200, 38600, H_SEC, "BATTERY SYSTEM")
d.rect("11-BATTERY", 3200, 31200, 11400, 37400)
s_battery(7300, 34600)
d.text("13-TAG", 3500, 36700, H_RAT, "-GB1")
for i, t in enumerate(["%d No. FOXESS CQ7, LFP" % B["modules"],
                       "%s kWh, %s V, %s kW" % (B["kwh_nominal"], B["v_nominal"], B["kw_continuous"]),
                       "%s kWh USABLE, 0.66 C" % B["kwh_usable"]]):
    d.text("06-DIMS", 3500, 32900 - i * 560, H_RAT, t)
d.rect("08-ELEC", 3200, 27600, 11400, 30300)
d.text("13-TAG", 3500, 29500, H_RAT, "-KB1")
d.text("07-TEXT", 3500, 28800, H_DEV, "BMS AND EPO LOOP")
d.text("06-DIMS", 3500, 28100, H_RAT, "CAN TO -TC1, EPO AT DOOR")
dash("12-CONTROL", 11400, 28950, 22600, 28950)
dash("12-CONTROL", 22600, 28950, 22600, 31500)
dash("12-CONTROL", 22600, 31500, 32000, 31500)
d.text("12-CONTROL", 13300, 29300, H_RAT, "CAN BUS, CHARGE LIMITS")

run(34600, 11400, 32000)
s_switch(15500, 34600)
dev(15500, 34600, "-QS2", "BATTERY ISOLATOR", "1000 V, 125 A", up=True)
s_switch(21500, 34600, brk=True)
dev(21500, 34600, "-QF1", "BATTERY MCB", "125 A, 2 POLE, 1000 V DC", up=True)
cores(27500, 34600, "2 x 1C")
d.text("13-TAG", 30900, 35200, H_RAT, "-W2")
d.line("10-EARTH", 7300, 27600, 7300, EBAR)
d.text("10-EARTH", 7500, 24200, H_RAT, "16 mm2 PE")

# ------------------------------------------------------------------ inverter
IX0, IX1, IY0, IY1 = 32000, 43000, 30000, 48000
d.rect("08-ELEC", IX0, IY0, IX1, IY1)
d.line("08-ELEC", IX0, IY0, IX1, IY1)
ctr("08-ELEC", IX0 + 2900, IY0 + 11600, 800, "=")
ctr("08-ELEC", IX0 + 8100, IY0 + 4800, 800, "~")
d.text("13-TAG", IX0 + 400, IY1 - 900, H_RAT, "-TC1")
d.text("07-TEXT", IX0 + 400, IY1 - 1600, H_DEV, "FOXESS P3-80-Plus")
d.text("06-DIMS", IX0 + 400, IY1 - 2200, H_RAT, "80 kW HYBRID, 400 V 3PH")
d.rect("06-DIMS", 24200, 24600, 32000, 29400)
d.text("13-TAG", 24500, 28700, H_RAT, "-TC1")
d.text("07-TEXT", 25600, 28700, H_DEV, "INTEGRAL FUNCTIONS")
for i, t in enumerate(["8 MPP TRACKERS, 1 STRING EACH", "INTEGRAL DC SWITCH",
                       "RCMU TYPE B", "ANTI ISLANDING TO IEC 62116",
                       "3 BATTERY PORTS, 1 IN USE", "DC AND AC SPD, TYPE 2"]):
    d.text("06-DIMS", 24500, 27900 - i * 560, H_RAT, t)
vrun(37500, IY1, 52000)
d.line("10-EARTH", 37500, IY0, 37500, EBAR)
d.text("10-EARTH", 37700, 24200, H_RAT, "25 mm2 PE")

# ------------------------------------------------------- ac side to the board
d.text("07-TEXT", 44500, 57400, H_SEC, "AC CONNECTION AND METERING")
ACY = 45000
run(ACY, IX1, 63500)
s_switch(46500, ACY)
dev(46500, ACY, "-QS3", "AC ISOLATOR", AC["isolator"].upper(), up=True)
_, fv2_e = s_spd(50500, ACY)
d.text("13-TAG", 51400, 44200, H_RAT, "-FV2")
d.text("07-TEXT", 51400, 43600, H_DEV, "AC SPD")
d.text("06-DIMS", 51400, 43000, H_RAT, "TYPE 2, 4 POLE")
d.line("10-EARTH", 50500, fv2_e, 50500, EBAR)
s_ct(55000, ACY)
rt("13-TAG", 54200, ACY + 800, H_RAT, "-TA1")
rt("06-DIMS", 54200, ACY + 200, H_RAT, "200/5 A")
s_meter(55000, 50200)
d.text("13-TAG", 53000, 52300, H_RAT, "-P1")
d.text("07-TEXT", 51400, 51700, H_DEV, "GENERATION METER")
dash("12-CONTROL", 55000, 43700, 57200, 43700)
dash("12-CONTROL", 57200, 43700, 57200, 50200)
dash("12-CONTROL", 57200, 50200, 56150, 50200)
_, kf1_b = s_relay(59800, 50200, lines=("27 / 59", "81 / ROCOF"))
d.text("13-TAG", 57000, 52900, H_RAT, "-KF1")
d.text("07-TEXT", 57000, 52300, H_DEV, "INTERFACE PROTECTION")
dash("12-CONTROL", 59800, kf1_b, 59800, ACY)
dash("12-CONTROL", 61500, 50600, 65800, 50600)       # -KF1 trip output to the shunt trip on -QF2
dash("12-CONTROL", 65800, 50600, 65800, 42600)
dash("12-CONTROL", 65800, 42600, 66600, 42600)
d.line("12-CONTROL", 66600, 42600, 66360, 42440)
d.line("12-CONTROL", 66600, 42600, 66360, 42760)
d.text("12-CONTROL", 66000, 48200, H_RAT, "TRIP TO -QF2")
cores(60500, ACY, "4 CORE")                  # clear of the board outline
d.text("13-TAG", 61500, 46400, H_RAT, "-W3")

# ------------------------------------------------- existing lv board and grid
dash_rect("06-DIMS", 63500, 24000, 82500, 53600)
d.text("07-TEXT", 63800, 54000, H_SEC, "EXISTING MAIN LV BOARD")
BUS = 40000
for k in range(3):                                     # busbar drawn as a triple line
    d.line("08-ELEC", 65000, BUS + k * 160, 81200, BUS + k * 160)
d.text("06-DIMS", 67400, BUS + 700, H_RAT, "400 V 3PH + N BUSBAR, 630 A, 25 kA")

run(ACY, 63500, 67000)
vrun(67000, BUS, ACY)
s_switch(67000, 42600, brk=True, vert=True)
d.text("13-TAG", 68700, 43400, H_RAT, "-QF2")
d.text("07-TEXT", 68700, 42800, H_DEV, "NEW WAY")
d.text("06-DIMS", 68700, 42200, H_RAT, AC["mccb"].upper() + ", SHUNT TRIP")

tb, tt = s_tx(78000, 55600)                           # utility transformer, outside the board
rt("13-TAG", 76600, 56500, H_RAT, "-T1")
rt("07-TEXT", 76600, 55900, H_DEV, "UTILITY TRANSFORMER, BY OTHERS")
rt("06-DIMS", 76600, 55300, H_RAT, "11 kV / 400 V")
vrun(78000, BUS, tb)
rt("06-DIMS", 77700, 53000, H_RAT, "POINT OF SUPPLY")
d.circle("08-ELEC", 78000, 48600, 650)               # -TA2 on the incomer, secondary led off to the left
rt("13-TAG", 77000, 50400, H_RAT, "-TA2")
rt("06-DIMS", 77000, 49800, H_RAT, "800/5 A, EXPORT LIMIT")
dash("12-CONTROL", 77350, 48600, 75500, 48600)
dash("12-CONTROL", 75500, 48600, 75500, 47300)
dash("12-CONTROL", 75500, 47300, 74650, 47300)       # to the edge of the -P2 meter
s_meter(73500, 47300)
d.text("13-TAG", 71000, 49600, H_RAT, "-P2")
d.text("07-TEXT", 69500, 49000, H_DEV, "IMPORT EXPORT METER")
dash("12-CONTROL", 73500, 46150, 73500, 44600)
d.line("12-CONTROL", 73500, 44600, 73260, 45000)
d.line("12-CONTROL", 73500, 44600, 73740, 45000)
d.text("12-CONTROL", 69200, 44000, H_RAT, "EXPORT SIGNAL TO -TC1")
s_switch(78000, 44200, brk=True, vert=True)
rt("13-TAG", 77300, 44800, H_RAT, "-QF0")
rt("06-DIMS", 77300, 44200, H_RAT, "630 A INCOMER")

for i, x in enumerate((69300, 72700)):
    vrun(x, 32500, BUS)
    s_switch(x, 37000, brk=True, vert=True)
    d.text("13-TAG", x + 1500, 37400, H_RAT, "-QF%d" % (5 + i))
d.rect("08-ELEC", 67300, 30000, 74700, 32500)
ctr("07-TEXT", 71000, 31500, H_DEV, "EXISTING SITE LOAD")
ctr("06-DIMS", 71000, 30700, H_RAT, "%d kW PEAK, ASSUMED PROFILE" % max(X.WEEKDAY))
d.line("10-EARTH", 74500, 26000, 77500, 26000)        # main earthing terminal in the board
rt("10-EARTH", 77500, 26300, H_RAT, "MET AND N-E LINK")
d.line("10-EARTH", 76000, 26000, 76000, EBAR)
rt("10-EARTH", 75800, 23200, H_RAT, "MAIN EARTHING CONDUCTOR 50 mm2")
rt("13-TAG", 75800, 23600, H_RAT, "-W5")

# ------------------------------------------------------------------ eps board
EPSY = 32000
run(EPSY, IX1, 51000)
s_switch(47000, EPSY, brk=True)
dev(47000, EPSY, "-QF4", "EPS MCB", "63 A, 4 POLE", up=True)
d.text("13-TAG", 49000, EPSY + 600, H_RAT, "-W4")
d.rect("08-ELEC", 51000, 27000, 61500, 33500)
d.text("13-TAG", 51400, 32700, H_RAT, "-EPS1")
d.text("07-TEXT", 51400, 32000, H_DEV, "ESSENTIAL SERVICES BOARD")
for i, t in enumerate(["4 OUTGOING WAYS, 15 kW TOTAL", "FED AT ALL TIMES FROM -TC1",
                       "TRANSFER INTERNAL, UNDER 10 ms", "NO LINK TO THE LV BOARD"]):
    d.text("06-DIMS", 51400, 31100 - i * 560, H_RAT, t)
d.line("10-EARTH", 56000, 27000, 56000, EBAR)

# --------------------------------------------------------------- earthing bar
d.line("10-EARTH", 2000, EBAR, 80000, EBAR)
d.line("10-EARTH", 2000, EBAR - 160, 80000, EBAR - 160)
d.text("07-TEXT", 2000, EBAR + 350, H_DEV, "MAIN EARTH BAR")
d.line("10-EARTH", 2000, 50500, 2000, EBAR)
d.line("10-EARTH", 2000, 50500, 3200, 50500)
d.text("10-EARTH", 2200, 44000, H_RAT, "ARRAY FRAME BOND 16 mm2")
s_earth(30000, EBAR - 160)
d.text("10-EARTH", 31400, EBAR - 1400, H_RAT, "ELECTRODE RESISTANCE UNDER 10 OHM, TN-S")

# ====================================================== key diagram, bottom left
d.rect("00-BORDER", 1300, 1300, 28000, 19200)
d.text("07-TEXT", 1700, 18400, H_SEC, "KEY DIAGRAM")
ks, KY, KT = 0.95, 10800, 380
KX0, KX1, KY0, KY1 = 11000, 16200, 12600, 17400          # the inverter block

s_pv(2200, 15200, 3400, 1500)
d.text("06-DIMS", 2200, 14500, KT, "-GP1  78.88 kWp")
run(15950, 5600, KX0)

s_battery(3600, KY, ks)
d.text("06-DIMS", 2200, 8300, KT, "-GB1  63.18 kWh")
run(KY, 4835, 5545)
s_switch(6400, KY, ks)
run(KY, 7255, 7745)
s_switch(8600, KY, brk=True, s=ks)
run(KY, 9455, 10200)
vrun(10200, KY, 13400)
run(13400, 10200, KX0)
d.text("06-DIMS", 5100, 12900, KT, "-QS2   -QF1")

d.rect("08-ELEC", KX0, KY0, KX1, KY1)
d.line("08-ELEC", KX0, KY0, KX1, KY1)
d.text("06-DIMS", KX0 + 300, KY1 - 900, KT, "-TC1  80 kW")
s_earth(13600, KY0, 0.8)

run(16000, KX1, 19345)
s_switch(20200, 16000, ks)
run(16000, 21055, 22145)
s_switch(23000, 16000, brk=True, s=ks)
run(16000, 23855, 24808)
s_grid(25900, 16000, ks)
d.text("06-DIMS", 19200, 17500, KT, "-QS3   -QF2")
ctr("07-TEXT", 25900, 17400, KT, "GRID")

run(13600, KX1, 19845)
s_switch(20700, 13600, brk=True, s=ks)
run(13600, 21555, 22400)
d.rect("08-ELEC", 22400, 12700, 26800, 14500)
ctr("07-TEXT", 24600, 13450, KT, "-EPS1")
d.text("06-DIMS", 17400, 12700, KT, "-QF4")

# ========================================================= legend, bottom strip
LX0, LX1 = 29000, 41500
d.rect("00-BORDER", LX0, 1300, LX1, 19200)
d.text("07-TEXT", LX0 + 400, 18400, H_SEC, "LEGEND")
leg_y = 17400
rows = [
    ("SWITCH DISCONNECTOR", 1400, lambda c, y: (d.line("09-CABLE", c - 1400, y, c + 1400, y), s_switch(c, y, 0.55))),
    ("CIRCUIT BREAKER", 1400, lambda c, y: (d.line("09-CABLE", c - 1400, y, c + 1400, y), s_switch(c, y, 0.55, brk=True))),
    ("SURGE ARRESTER, TYPE 2", 1650, lambda c, y: (d.line("09-CABLE", c - 1400, y, c + 1400, y), s_spd(c, y, 0.5))),
    ("CURRENT TRANSFORMER", 1400, lambda c, y: (d.line("09-CABLE", c - 1400, y, c + 1400, y), s_ct(c, y, 0.55))),
    ("ENERGY METER", 1500, lambda c, y: s_meter(c, y, 0.6)),
    ("PROTECTION RELAY", 1400, lambda c, y: s_relay(c, y, 0.6, lines=("27/59",))),
    ("DISTRIBUTION TRANSFORMER", 1800, lambda c, y: s_tx(c, y, 0.5)),
    ("BATTERY, SERIES STRING", 1450, lambda c, y: s_battery(c, y, 0.55)),
    ("PHOTOVOLTAIC STRING", 1500, lambda c, y: s_pv(c - 1300, y - 600, 2600, 1200)),
    ("UTILITY SUPPLY", 1450, lambda c, y: s_grid(c, y, 0.5)),
    ("PROTECTIVE EARTH", 1450, lambda c, y: s_earth(c, y + 600, 0.5)),
]
for label, pitch, draw in rows:
    draw(LX0 + 1900, leg_y)
    d.text("07-TEXT", LX0 + 4200, leg_y - 140, 280, label)
    leg_y -= pitch

# ============================================= protection settings and schedule
def table(x0, x1, ytop, ybot, title, cols, rows):
    d.rect("00-BORDER", x0, ybot, x1, ytop)
    d.line("00-BORDER", x0, ytop - 900, x1, ytop - 900)
    d.text("07-TEXT", x0 + 300, ytop - 700, H_TH, title)
    d.line("00-BORDER", x0, ytop - 1800, x1, ytop - 1800)
    for c, t in zip(cols, rows[0]):
        d.text("07-TEXT", x0 + c, ytop - 1600, H_TAB, t)
    for r, cells in enumerate(rows[1:]):
        for c, t in zip(cols, cells):
            d.text("06-DIMS", x0 + c, ytop - 2500 - r * 700, H_TAB, t)


table(42500, 58500, 19200, 10300, "CABLE SCHEDULE", (300, 1800, 7000, 11600),
      [("TAG", "CABLE", "LENGTH", "PROTECTION"),
       ("-W1", "16 x 1C 6 mm2 PV1-F", "45 m", "NONE, 1 PER MPPT"),
       ("-W2", "2 x 1C 35 mm2 Cu XLPE", "8 m", "-QF1 125 A DC"),
       ("-W3", "4C 95 mm2 Cu SWA", "32 m", "-QF2 160 A"),
       ("-W4", "4C 35 mm2 Cu", "12 m", "-QF4 63 A"),
       ("-W5", "1C 50 mm2 G/Y", "20 m", "EARTHING"),
       ("", "SIZES AND VOLT DROP TO BE CONFIRMED ON ROUTE", "", "")])

table(42500, 58500, 9500, 1300, "INTERFACE PROTECTION SETTINGS, TO BE CONFIRMED BY IESCO", (300, 5000, 10200),
      [("FUNCTION", "SETTING", "TRIP TIME"),
       ("27  UNDER VOLTAGE", "0.80 Un", "2.5 s"),
       ("27  STAGE 2", "0.50 Un", "0.5 s"),
       ("59  OVER VOLTAGE", "1.15 Un", "1.0 s"),
       ("81  UNDER FREQUENCY", "47.5 Hz", "0.5 s"),
       ("81  OVER FREQUENCY", "51.5 Hz", "0.5 s"),
       ("ROCOF", "1.0 Hz/s", "0.5 s"),
       ("RECONNECT DELAY", "", "180 s")])

# ======================================================== notes, revision, title
NX0, NX1 = 59500, SHEET_W - M - 300
d.rect("00-BORDER", NX0, 14000, NX1, 19200)
d.text("07-TEXT", NX0 + 300, 18500, H_TH, "NOTES")
for i, t in enumerate([
        "1  NO STRING FUSES. ONE STRING PER MPP TRACKER, SO NO PARALLEL FAULT PATH EXISTS.",
        "2  BATTERY MODULES IN SERIES ONLY. NO PARALLEL STRINGS, ONE CURRENT PATH.",
        "3  -QF1 IS ABOVE THE 110 A SIXTY SECOND PEAK AND BELOW THE 35 mm2 CABLE RATING.",
        "4  SoC HELD BETWEEN 10 AND 100 %. 56.86 kWh USABLE, 3.79 h BACKUP FROM FULL.",
        "5  -EPS1 IS FED ONLY FROM THE -TC1 EPS PORT. ITS GRID BYPASS IS INTERNAL TO -TC1.",
        "6  EARTHING TN-S. ARRAY FRAME, BATTERY ENCLOSURE AND -TC1 BONDED TO THE EARTH BAR.",
        "7  EXPORT LIMITED BY SIGNAL FROM -TA2. CHECK SETTING AT COMMISSIONING."]):
    d.text("06-DIMS", NX0 + 300, 17600 - i * 560, H_RAT, t)

d.rect("00-BORDER", NX0, 9000, NX1, 13500)
d.line("00-BORDER", NX0, 12600, NX1, 12600)
for c, t in zip((300, 1800, 9600, 14600, 18400), ("REV", "DESCRIPTION", "DATE", "BY", "CHK")):
    d.text("07-TEXT", NX0 + c, 12800, H_TAB, t)
for r, cells in enumerate([("P1", "FIRST ISSUE FOR COMMENT", "12.09.2026", "UJ", "--"),
                           ("P2", "SPD AND METERING ADDED", "28.09.2026", "UJ", "--"),
                           ("P3", "ISSUED FOR COMMENT", "08.10.2026", "UJ", "--")]):
    for c, t in zip((300, 1800, 9600, 14600, 18400), cells):
        d.text("06-DIMS", NX0 + c, 11800 - r * 800, H_TAB, t)

d.rect("00-BORDER", NX0, 1300, NX1, 8500)
d.line("00-BORDER", NX0, 6100, NX1, 6100)
d.line("00-BORDER", NX0, 3700, NX1, 3700)
d.line("00-BORDER", NX0, 2500, NX1, 2500)
d.line("00-BORDER", NX0 + 13500, 1300, NX0 + 13500, 3700)
d.text("07-TEXT", NX0 + 300, 7700, 300, "CLIENT")
d.text("07-TEXT", NX0 + 300, 6900, 460, "SAMPLE COMMERCIAL CLIENT")
d.text("07-TEXT", NX0 + 300, 5400, 300, "PROJECT")
d.text("07-TEXT", NX0 + 300, 4700, 400, "80 kW ROOFTOP PV WITH 63 kWh BATTERY STORAGE")
d.text("07-TEXT", NX0 + 300, 4000, 300, "I-10 INDUSTRIAL AREA, ISLAMABAD")
d.text("07-TEXT", NX0 + 300, 3320, 240, "DRAWING TITLE")
d.text("07-TEXT", NX0 + 300, 2650, 420, "SINGLE LINE DIAGRAM")
d.text("07-TEXT", NX0 + 300, 1750, 280, "DRAWN  USAMA JAVED    CHK  --    APP  --")
d.text("07-TEXT", NX0 + 13800, 3320, 240, "DRAWING No.")
d.text("07-TEXT", NX0 + 13800, 2650, 420, "PV-04")
d.text("07-TEXT", NX0 + 13800, 1750, 280, "SCALE  NTS @ A1    REV  P3")

# -------------------------------------------------------------- overlap check
boxes = [(p[0], p[1] - 0.22 * p[2], p[0] + tw(p[3], p[2]), p[1] + p[2], p[3])
         for kind, layer, p in d.e if kind == "TEXT" and str(p[3]).strip()]
bad = 0
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        a, b = boxes[i], boxes[j]
        if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
            print("  overlap: %-40r %r" % (a[4], b[4])); bad += 1
off = [b[4] for b in boxes if len(str(b[4])) > 1 and
       (b[0] < M or b[2] > SHEET_W - M or b[1] < M or b[3] > SHEET_H - M)]
for t in off:
    print("  off sheet: %r" % t)

open("PV-04 Single Line Diagram.dxf", "w", encoding="latin1", newline="").write(d.dumps())
open("PV-04 Single Line Diagram.scr", "w", encoding="latin1", newline="").write(
    d.dumps_scr("PV-04 single line diagram, 80 kW PV with 63 kWh battery"))
print("PV-04 written, %d entities, %d overlaps, %d off sheet" % (len(d.e), bad, len(off)))
