"""PV-04, the battery single line diagram: stack build up, BMS and CAN, DC
protection, the three inverter battery ports, the EPS transfer and earthing.

PV-02 is the system single line. This sheet opens up the storage side of it.
"""
import design as D
from gen_dxf import Dxf, border, SHEET_W, SHEET_H

B = D.out["battery"]
A = D.out["array"]
MOD_KWH = D.BAT["kwh_module"]
MOD_V = D.BAT["v_module"]
N = B["modules"]

d = Dxf()
border(d, "PV-04", "80 kW ROOFTOP PV WITH BATTERY STORAGE",
       "BATTERY SYSTEM SINGLE LINE DIAGRAM", "NTS @ A1")

# ------------------------------------------------------------------ battery stack
SX, SY = 4000, 40000
BW, BH, GAP = 7600, 1250, 330
d.text("07-TEXT", SX, SY + N * (BH + GAP) + 1700, 320, "BATTERY STACK")
d.text("07-TEXT", SX, SY + N * (BH + GAP) + 1050, 215,
       "%d No. FOXESS CQ7 IN SERIES, LFP, 1 MASTER AND %d SLAVES" % (N, N - 1))

for k in range(N):
    y = SY + k * (BH + GAP)
    master = (k == 0)
    d.rect("11-BATTERY", SX, y, SX + BW, y + BH)
    d.text("07-TEXT", SX + 250, y + BH - 520, 215,
           ("CQ7-M  MASTER" if master else "CQ7-S  SLAVE %d" % k))
    d.text("07-TEXT", SX + 250, y + 230, 190,
           "%s kWh   %s V" % (MOD_KWH, MOD_V))
    # series link to the module above
    if k < N - 1:
        d.line("09-CABLE", SX + BW / 2, y + BH, SX + BW / 2, y + BH + GAP)
    # cumulative voltage down the right hand side
    d.text("06-DIMS", SX - 1900, y + BH / 2 - 95, 190,
           "%.1f V" % ((k + 1) * MOD_V))

d.text("07-TEXT", SX + BW + 400, SY - 900, 215, "STACK %s V NOMINAL" % B["v_nominal"])
d.text("07-TEXT", SX, SY - 900, 215, "%s kWh NOMINAL" % B["kwh_nominal"])
d.text("07-TEXT", SX, SY - 1550, 215, "%s kWh USABLE AT %d %% DOD" % (B["kwh_usable"], D.BAT["dod"] * 100))

# the master carries the BMU, the controller and the integral switchgear
MX = SX + BW + 3200
d.rect("08-ELEC", MX, SY - 300, MX + 6400, SY + BH + 300)
d.text("07-TEXT", MX + 250, SY + BH - 250, 240, "BMU AND SWITCHGEAR")
d.text("07-TEXT", MX + 250, SY + 100, 190, "IN THE MASTER MODULE")
d.line("09-CABLE", SX + BW, SY + BH / 2, MX, SY + BH / 2)

# ------------------------------------------------------------------ DC protection run
PX = MX + 6400
ACY = SY + BH / 2


def box(x, y, w, h, label, sub=None, layer="08-ELEC"):
    d.rect(layer, x, y, x + w, y + h)
    d.text("07-TEXT", x + 250, y + h - 850, 250, label)
    if sub:
        d.text("07-TEXT", x + 250, y + h - 1480, 190, sub)
    return x + w


x = PX
d.line("09-CABLE", x, ACY, x + 1400, ACY)
x += 1400
x = box(x, ACY - 1100, 4600, 2200, "DC ISOLATOR", "1000 V, 125 A, 2P")
d.line("09-CABLE", x, ACY, x + 1400, ACY)
x += 1400
x = box(x, ACY - 1100, 4600, 2200, "DC MCB", "125 A, CURVE C")
d.line("09-CABLE", x, ACY, x + 2200, ACY)
d.text("07-TEXT", PX + 1600, ACY + 1500, 190, "2 x 35 mm2 CU, + AND -")

# ------------------------------------------------------------------ inverter
IX = x + 2200
IW, IH = 15000, 14200
IY = ACY - 2400
d.rect("08-ELEC", IX, IY, IX + IW, IY + IH)
d.text("07-TEXT", IX + 350, IY + IH - 1100, 300, "INVERTER")
for i, t in enumerate([
        "FOXESS P3-80-Plus",
        "80 kW THREE PHASE HYBRID",
        "BATTERY WINDOW %d to %d V" % (D.INV["bat_lo"], D.INV["bat_hi"]),
        "240 A OVER 3 PORTS, 80 A EACH",
        "8 MPP TRACKERS ON THE PV SIDE",
        "EPS OUTPUT, TRANSFER <10 ms"]):
    d.text("07-TEXT", IX + 350, IY + IH - 1900 - i * 620, 200, t)

# the three battery ports, drawn so the spare capacity is obvious
for p in range(3):
    py = IY + 1200 + p * 2000
    d.rect("11-BATTERY", IX + 350, py, IX + 4200, py + 1400)
    d.text("07-TEXT", IX + 500, py + 480, 200, "BATT PORT %d" % (p + 1))
    if p == 0:
        d.line("09-CABLE", IX, py + 700, IX + 350, py + 700)
        d.text("07-TEXT", IX + 4500, py + 480, 190, "IN USE, %s kWh" % B["kwh_nominal"])
    else:
        d.text("07-TEXT", IX + 4500, py + 480, 190, "SPARE, UP TO 98.28 kWh")

# PV side arriving at the top
d.line("09-CABLE", IX - 3400, IY + IH - 1400, IX, IY + IH - 1400)
d.text("07-TEXT", IX - 10200, IY + IH - 1500, 215, "PV, 8 STRINGS, SEE PV-02")

# CAN between the master BMU and the inverter
d.line("06-DIMS", MX + 3200, SY - 300, MX + 3200, IY - 1800)
d.line("06-DIMS", MX + 3200, IY - 1800, IX + 2000, IY - 1800)
d.line("06-DIMS", IX + 2000, IY - 1800, IX + 2000, IY)
d.text("06-DIMS", MX + 3500, IY - 1600, 190, "CAN, BMS TO INVERTER")

# ------------------------------------------------------------------ AC side
AX = IX + IW
GY = IY + IH - 3600
EY = IY + 3200

d.line("09-CABLE", AX, GY, AX + 1400, GY)
x = AX + 1400
x = box(x, GY - 1100, 4800, 2200, "AC ISOLATOR", "400 V, 250 A, 4P")
d.line("09-CABLE", x, GY, x + 1200, GY)
x += 1200
x = box(x, GY - 1100, 4200, 2200, "MCCB", "160 A, 4 POLE")
d.line("09-CABLE", x, GY, x + 1200, GY)
x += 1200
x = box(x, GY - 1100, 4600, 2200, "kWh METER", "NET METERING")
d.line("09-CABLE", x, GY, x + 1200, GY)
x += 1200
d.circle("08-ELEC", x + 950, GY, 950)
d.text("07-TEXT", x + 350, GY - 120, 250, "GRID")
d.text("07-TEXT", AX + 1600, GY + 1700, 190, "GRID PORT, 4C 95 mm2 CU")

d.line("09-CABLE", AX, EY, AX + 1400, EY)
x = AX + 1400
x = box(x, EY - 1100, 5400, 2200, "EPS BOARD", "ESSENTIAL LOADS, 15 kW")
d.text("07-TEXT", AX + 1600, EY + 1700, 190, "EPS PORT, 4C 35 mm2 CU, 63 A 4P MCB")
lx = x
for lbl in ("LIGHTING", "CONTROLS", "COLD ROOM"):
    d.line("09-CABLE", lx, EY, lx + 1100, EY)
    d.text("07-TEXT", lx + 1300, EY - 95, 190, lbl)
    lx += 5600
d.text("07-TEXT", AX + 1600, EY - 2200, 190,
       "THE EPS BOARD IS FED FROM THE INVERTER AT ALL TIMES AND DOES NOT SEE THE LOSS OF GRID")

# ------------------------------------------------------------------ earthing
d.line("10-EARTH", SX + BW / 2, SY - 2600, SX + BW / 2, SY - 4200)
d.line("10-EARTH", SX + BW / 2, SY - 4200, IX + 3000, SY - 4200)
d.line("10-EARTH", IX + 3000, SY - 4200, IX + 3000, IY)
ex = IX + 7000
d.line("10-EARTH", IX + 3000, SY - 4200, ex, SY - 4200)
d.line("10-EARTH", ex, SY - 3800, ex, SY - 4600)
d.line("10-EARTH", ex - 260, SY - 4200, ex + 260, SY - 4200)
d.line("10-EARTH", ex - 160, SY - 4500, ex + 160, SY - 4500)
d.text("07-TEXT", ex + 700, SY - 4300, 215,
       "EARTH ELECTRODE, 16 mm2 CU TO MAIN EARTH BAR. BATTERY ENCLOSURE AND ARRAY FRAME BONDED.")

# ------------------------------------------------------------------ tables
def table(x, y, head, rows, cols, width, h=225, gap=620):
    d.line("08-ELEC", x, y + 700, x + width, y + 700)
    for c, cell in enumerate(head):
        d.text("07-TEXT", x + cols[c], y, h, cell)
    d.line("08-ELEC", x, y - 170, x + width, y - 170)
    for r, row in enumerate(rows):
        yy = y - (r + 1) * gap
        for c, cell in enumerate(row):
            d.text("07-TEXT", x + cols[c], yy, h, str(cell))
        d.line("08-ELEC", x, yy - 170, x + width, yy - 170)


TX, TY = 4000, 30000
d.text("07-TEXT", TX, TY + 1300, 320, "BATTERY PROTECTION AND SETTINGS")
table(TX, TY - 400, ["ITEM", "VALUE", "WHERE IT COMES FROM"], [
    ["STACK NOMINAL VOLTAGE", "%s V" % B["v_nominal"], "%d x %s V, INSIDE THE %d to %d V WINDOW"
     % (N, MOD_V, D.INV["bat_lo"], D.INV["bat_hi"])],
    ["CONTINUOUS CURRENT", "80 A", "CQ7 MODULE LIMIT, ONE PORT"],
    ["CONTINUOUS POWER", "%s kW" % B["kw_continuous"], "80 A x %s V, SO %.2f C ON THIS STACK"
     % (B["v_nominal"], B["c_rate"])],
    ["PEAK POWER, 60 s", "%s kW" % B["kw_peak_60s"], "110 A CQ7 PEAK RATING"],
    ["DC CABLE", "2 x 35 mm2 CU", "SIZED ON 80 A CONTINUOUS"],
    ["DC PROTECTION", "125 A MCB AND ISOLATOR", "ABOVE 110 A PEAK, BELOW CABLE RATING"],
    ["OPERATING SOC BAND", "10 % to 100 %", "90 % DOD PER THE CQ7 DATASHEET"],
    ["RESERVE HELD FOR OUTAGE", "55 % SOC", "28.4 kWh, 1.9 h ON THE 15 kW EPS BOARD"],
    ["EPS TRANSFER TIME", "<10 ms", "P3 Plus DATASHEET"],
], [0, 10500, 18500], 38000)

MXX, MYY = 46000, 30000
d.text("07-TEXT", MXX, MYY + 1300, 320, "OPERATING MODES")
table(MXX, MYY - 400, ["PERIOD", "MODE", "LIMIT"], [
    ["00:00 to 05:00", "CHARGE FROM GRID, OFF PEAK", "STOP AT 75 % SOC"],
    ["06:00 to 18:00", "CHARGE FROM PV SURPLUS", "UP TO 100 % SOC"],
    ["06:00 to 18:00", "DISCHARGE TO SHAVE THE PEAK", "NOT BELOW 55 % SOC"],
    ["18:00 to 20:00", "GRID OFF, EPS ON PV AND BATTERY", "DOWN TO 10 % SOC"],
    ["20:00 to 24:00", "DISCHARGE IF OVER THE TARGET", "DOWN TO 10 % SOC"],
], [0, 5600, 22000], 32000)
d.text("07-TEXT", MXX, MYY - 4400, 215,
       "GRID IMPORT TARGET 55 kW. SEE PV-03 FOR THE DISPATCH MODEL AND THE ANNUAL RESULT.")

# ------------------------------------------------------------------ notes
NX, NY = 4000, 19500
d.text("07-TEXT", NX, NY + 1300, 320, "BATTERY DESIGN NOTES")
notes = [
    "1. NINE MODULES IS WHAT COVERS A TWO HOUR OUTAGE ON THE 15 kW ESSENTIAL BOARD AND STILL LEAVES RESERVE TO SHAVE THE DAY.",
    "   %s kWh NOMINAL, %s kWh USABLE. THE STACK SITS AT %s V, WELL INSIDE THE INVERTER %d to %d V BATTERY WINDOW."
    % (B["kwh_nominal"], B["kwh_usable"], B["v_nominal"], D.INV["bat_lo"], D.INV["bat_hi"]),
    "2. POWER IS SET BY THE PORT, NOT BY THE CELLS. ONE PORT CARRIES 80 A, SO %s kW CONTINUOUS AT %s V. THE INVERTER"
    % (B["kw_continuous"], B["v_nominal"]),
    "   WOULD TAKE 240 A ACROSS ALL THREE PORTS, SO POWER AND ENERGY BOTH TREBLE WITHOUT CHANGING THE INVERTER.",
    "3. MODULES ARE IN SERIES, NOT PARALLEL. THERE IS ONE CURRENT PATH, SO NO MODULE CAN BACK FEED ANOTHER AND NO",
    "   STRING FUSING IS NEEDED INSIDE THE STACK. THE MASTER MODULE CARRIES THE BMU, THE CONTROLLER AND THE SWITCHGEAR.",
    "4. THE DC MCB IS 125 A: ABOVE THE 110 A SIXTY SECOND PEAK SO IT DOES NOT NUISANCE TRIP, AND BELOW THE RATING OF",
    "   THE 35 mm2 CABLE SO THE CABLE IS PROTECTED. THE ISOLATOR IS THERE FOR SAFE ISOLATION, NOT FOR FAULT CLEARING.",
    "5. THE BMS TALKS TO THE INVERTER OVER CAN. THE INVERTER DOES NOT DECIDE THE CHARGE LIMITS, THE BMS DOES, AND THE",
    "   INVERTER FOLLOWS THEM. LOSS OF CAN SHOULD STOP CHARGE AND DISCHARGE RATHER THAN FALL BACK TO A FIXED LIMIT.",
    "6. THE EPS BOARD IS FED FROM THE INVERTER AT ALL TIMES, NOT SWITCHED TO IT ON FAILURE, SO THE SUB 10 ms TRANSFER",
    "   IS INTERNAL TO THE INVERTER. ONLY THE ESSENTIAL LOADS GO ON IT, AND THEY ARE SIZED AT 15 kW.",
    "7. BATTERY ENCLOSURE, ARRAY FRAME AND INVERTER CHASSIS ARE ALL BONDED TO THE MAIN EARTH BAR.",
    "8. THE BATTERY ROOM NEEDS VENTILATION, A SMOKE DETECTOR AND A CLEAR ONE METRE WORKING SPACE. LFP DOES NOT OFF GAS",
    "   IN NORMAL USE BUT THE INSTALLATION STILL HAS TO SATISFY THE LOCAL FIRE AND ELECTRICAL AUTHORITY.",
    "9. EQUIPMENT RATINGS ARE FROM THE FOXESS DATASHEETS. CABLE SIZES AND THE PROTECTION SETTINGS ARE DESIGN FIGURES",
    "   AND WOULD BE CONFIRMED AGAINST INSTALLED ROUTE LENGTHS AND THE MANUFACTURER COMMISSIONING GUIDE BEFORE ISSUE.",
]
for i, s in enumerate(notes):
    d.text("07-TEXT", NX, NY - 400 - i * 620, 225, s)

open("PV-04 Battery SLD.dxf", "w", encoding="latin1", newline="").write(d.dumps())
print("PV-04 written, %d entities" % len(d.e))
