"""PV-03, the battery sheet: control strategy, two days of dispatch, annual
performance and the sizing sensitivity that justifies the battery chosen. A1."""
import json
import design as D
import dispatch as X
from gen_dxf import Dxf, border, SHEET_W, SHEET_H, ADV

B = D.out["battery"]
R = json.load(open("dispatch.json"))
DAYS = json.load(open("days.json"))
SENS = json.load(open("sensitivity.json"))

d = Dxf()
H_TXT = 250                       # nothing on this sheet below 2.5 mm at A1
border(d, "PV-03", "80 kW ROOFTOP PV WITH 63 kWh BATTERY STORAGE",
       "BATTERY CONTROL STRATEGY AND PERFORMANCE", "NTS @ A1")


def table(x, y, head, rows, cols, width, h=H_TXT, gap=640):
    d.line("08-ELEC", x, y + 700, x + width, y + 700)
    for c, cell in enumerate(head):
        d.text("07-TEXT", x + cols[c], y, h, cell)
    d.line("08-ELEC", x, y - 170, x + width, y - 170)
    for r, row in enumerate(rows):
        yy = y - (r + 1) * gap
        for c, cell in enumerate(row):
            d.text("07-TEXT", x + cols[c], yy, h, str(cell))
        d.line("08-ELEC", x, yy - 170, x + width, yy - 170)
    return y - (len(rows) + 1) * gap


def tw(t, h):
    return len(str(t)) * ADV * h


def dash(layer, x1, y1, x2, y2, seg=450, gap=300):
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


def tbox(p):
    return (p[0], p[1] - 0.22 * p[2], p[0] + tw(p[3], p[2]), p[1] + p[2])


def meets(a, b, gap=0):
    return a[0] - gap < b[2] and b[0] - gap < a[2] and a[1] - gap < b[3] and b[1] - gap < a[3]


def hits(s, b, gap=0):
    """True when line segment s passes through box b grown by gap."""
    x1, y1, x2, y2 = s
    bx0, by0, bx1, by1 = b[0] - gap, b[1] - gap, b[2] + gap, b[3] + gap
    dx, dy, t0, t1 = x2 - x1, y2 - y1, 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if p == 0:
            if q <= 0:
                return False
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return False
                t0 = max(t0, t)
            else:
                if t < t0:
                    return False
                t1 = min(t1, t)
    return t1 - t0 > 1e-9


# ------------------------------------------------------------------ control strategy
CX, CY = 3000, 53000
d.text("07-TEXT", CX, CY + 1300, 320, "CONTROL STRATEGY")
d.text("07-TEXT", CX, CY + 650, H_TXT,
       "THE BATTERY HAS THREE JOBS. THE OUTAGE RESERVE OUTRANKS THE OTHER TWO AT ALL TIMES.")
table(CX, CY - 400, ["PERIOD", "ACTION", "LIMIT"], [
    ["00:00 to 05:00", "CHARGE FROM GRID AT THE OFF PEAK RATE", "STOP AT %d %% SOC" % R["grid_charge_target_pct"]],
    ["06:00 to 18:00", "CHARGE FROM PV SURPLUS", "UP TO 100 % SOC"],
    ["06:00 to 18:00", "DISCHARGE ONLY TO HOLD GRID IMPORT DOWN", "NOT BELOW %d %% SOC" % R["outage_floor_pct"]],
    ["18:00 to 20:00", "GRID OFF. EPS BOARD ON PV AND BATTERY", "DOWN TO 10 % SOC"],
    ["20:00 to 06:00", "DISCHARGE IF IMPORT WOULD EXCEED TARGET", "DOWN TO 10 % SOC"],
], [0, 5200, 24000], 36000)

for i, t in enumerate([
        "GRID IMPORT TARGET %d kW. ESSENTIAL BOARD %d kW. THE %d %% FLOOR HOLDS %s kWh BACK, WHICH IS %.2f HOURS"
        % (R["peak_target_kw"], R["essential_kw"], R["outage_floor_pct"], R["backup_reserve_kwh"], R["backup_hours_at_floor"]),
        "ON THE ESSENTIAL BOARD AGAINST A %d HOUR OUTAGE, SO %.1f %% OF OUTAGE DEMAND IS MET OVER THE YEAR."
        % (R["outage_hours_per_year"] / 365, R["outage_served_pct"]),
        "A FULL BATTERY WOULD GIVE %.2f HOURS. A HIGHER FLOOR WOULD COVER MORE OF THE OUTAGE AND LEAVE LESS FOR DAY TIME SHAVING." % R["backup_hours_full"]]):
    d.text("07-TEXT", CX, CY - 4500 - i * 620, H_TXT, t)


# ------------------------------------------------------------------ dispatch charts
def chart(ox, oy, w, h, day, soc_start, title, note):
    first = len(d.e)
    kw_max, soc_max = 90.0, 100.0
    sx = w / 24.0
    sy = h / kw_max
    d.rect("00-BORDER", ox, oy, ox + w, oy + h)
    d.text("07-TEXT", ox, oy + h + 1300, 300, title)
    d.text("07-TEXT", ox, oy + h + 700, H_TXT, note)
    # grid lines and axis labels
    for kw in range(0, int(kw_max) + 1, 20):
        y = oy + kw * sy
        if kw:
            d.line("06-DIMS", ox, y, ox + w, y)
        d.text("06-DIMS", ox - 1100, y - 110, H_TXT, str(kw))
    d.text("06-DIMS", ox - 1100, oy + h + 200, H_TXT, "kW")
    for hh in range(0, 25, 3):
        x = ox + hh * sx
        d.line("06-DIMS", x, oy, x, oy - 180)
        d.text("06-DIMS", x - 240, oy - 900, H_TXT, "%02d" % (hh % 24))
    for pct in range(0, 101, 25):
        y = oy + pct / soc_max * h
        d.text("11-BATTERY", ox + w + 300, y - 110, H_TXT, str(pct))
    d.text("11-BATTERY", ox + w + 300, oy + h + 450, H_TXT, "SOC %")
    # the grid import target the control works to
    ty = oy + R["peak_target_kw"] * sy
    dash("06-DIMS", ox, ty, ox + w, ty)
    d.text("06-DIMS", ox + 20.4 * sx, ty + 150, H_TXT, "TARGET %d kW" % R["peak_target_kw"])

    def step(layer, idx, scale):
        for i, row in enumerate(day):
            v = row[idx] * scale
            x0, x1 = ox + i * sx, ox + (i + 1) * sx
            d.line(layer, x0, oy + v, x1, oy + v)
            if i:
                prev = day[i - 1][idx] * scale
                d.line(layer, x0, oy + prev, x0, oy + v)

    step("03-PV-MODULE", 0, sy)        # PV
    step("07-TEXT", 1, sy)             # site demand
    step("08-ELEC", 5, sy)             # grid import
    # state of charge at the end of each hour, starting from the end of the day before
    pts = [(ox, oy + soc_start / soc_max * h)] + [(ox + (i + 1) * sx, oy + day[i][4] / soc_max * h)
                                                for i in range(len(day))]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        d.line("11-BATTERY", xa, ya, xb, yb)
    # the outage window, its two edges only, with the label centred between them
    o0, o1 = X.OUTAGE_HOURS[0], X.OUTAGE_HOURS[-1] + 1
    for hh in (o0, o1):
        d.line("06-DIMS", ox + hh * sx, oy, ox + hh * sx, oy + h)
    d.text("06-DIMS", ox + (o0 + o1) / 2 * sx - tw("OUTAGE", H_TXT) / 2, oy + h - 900, H_TXT, "OUTAGE")

    # name every line on the chart itself, so the chart still reads when it is
    # plotted in black and white and the legend colours are lost
    segs = [p for kind, layer, p in d.e[first:] if kind == "LINE"]
    taken = [tbox(p) for kind, layer, p in d.e[first:] if kind == "TEXT"]
    soc = lambda i: day[i][4] / soc_max * h
    for layer, name, val, order in [
            ("03-PV-MODULE", "PV", lambda i: day[i][0] * sy, "peak"),
            ("07-TEXT", "DEMAND", lambda i: day[i][1] * sy, "peak"),
            ("08-ELEC", "IMPORT", lambda i: day[i][5] * sy, "peak"),
            ("11-BATTERY", "SOC", soc, "early")]:
        hours = list(range(24))
        if order == "peak":
            hours.sort(key=lambda i: -val(i))
        placed = False
        for i in hours:
            if val(i) <= 0:
                continue
            for y in (oy + val(i) + 150, oy + val(i) - 400):
                x = ox + (i + 0.08) * sx
                if order == "early":                       # SOC is flat within these hours
                    x = ox + (i + 1.1) * sx
                b = (x, y - 0.22 * H_TXT, x + tw(name, H_TXT), y + H_TXT)
                inside = b[0] > ox + 100 and b[2] < ox + w - 100 and b[1] > oy + 100 and b[3] < oy + h - 100
                if inside and not any(hits(s, b, 60) for s in segs) and not any(meets(t, b, 60) for t in taken):
                    d.text(layer, x, y, H_TXT, name)
                    taken.append(b)
                    placed = True
                    break
            if placed:
                break
        assert placed, "no clear place for the %s label on %s" % (name, title)


K1X, K1Y = 5000, 33000
chart(K1X, K1Y, 30000, 11000, DAYS["apr"], R["soc_start_apr"],
      "DISPATCH, TYPICAL APRIL WEEKDAY",
      "GRID IMPORT KEPT AT OR BELOW THE %d kW TARGET ALL DAY" % R["peak_target_kw"])
K2X = 45000
chart(K2X, K1Y, 30000, 11000, DAYS["dec"], R["soc_start_dec"],
      "DISPATCH, DECEMBER WEEKDAY",
      "THE DAY THAT SETS THE ANNUAL PEAK AT %.1f kW" % R["peak_with_batt"])

d.text("07-TEXT", 5000, 29500, H_TXT,
       "PV IS GENERATION, DEMAND IS SITE DEMAND (ESSENTIAL BOARD ONLY DURING THE OUTAGE), IMPORT IS GRID IMPORT,"
       " SOC IS STATE OF CHARGE.")

# ------------------------------------------------------------------ annual performance
PX, PY = 3000, 25000
d.text("07-TEXT", PX, PY + 1300, 320, "ANNUAL PERFORMANCE")
perf_end = table(PX, PY - 400, ["", "WITHOUT BATTERY", "WITH BATTERY"], [
    ["PV GENERATED", "%s kWh" % R["pv_generated"], "%s kWh" % R["pv_generated"]],
    ["SITE LOAD", "%s kWh" % R["site_load"], "%s kWh" % R["site_load"]],
    ["GRID IMPORT, TOTAL", "%s kWh" % R["grid_import_no_batt"], "%s kWh" % R["grid_import_with_batt"]],
    ["OF WHICH OFF PEAK CHARGING", "NONE", "%s kWh" % R["charged_from_grid"]],
    ["GRID IMPORT LESS BATTERY CHARGING", "%s kWh" % R["grid_import_no_batt"],
     "%s kWh" % (R["grid_import_with_batt"] - R["charged_from_grid"])],
    ["PV EXPORTED", "%s kWh" % R["export_no_batt"], "%s kWh" % R["export_with_batt"]],
    ["ANNUAL GRID PEAK", "%.1f kW" % R["peak_no_batt"], "%.1f kW" % R["peak_with_batt"]],
    ["HOURS OVER %d kW" % R["peak_target_kw"], R["hours_over_target_no_batt"],
     "%s, DOWN %.1f %%" % (R["hours_over_target_with_batt"], R["hours_over_target_cut_pct"])],
    ["OUTAGE DEMAND MET", "0 kWh, 0 %", "%s kWh, %.1f %%" % (R["outage_served_with_batt"], R["outage_served_pct"])],
    ["BATTERY THROUGHPUT", "NONE", "%s kWh, %.1f FULL CYCLES" % (R["discharged_per_year"], R["equivalent_full_cycles"])],
    ["ROUND TRIP LOSS, BATTERY ONLY", "NONE", "%s kWh" % R["round_trip_loss"]],
], [0, 11000, 22000], 36000)
perf_note = [
    "TOTAL IMPORT RISES BECAUSE OFF PEAK CHARGING IS ITSELF AN IMPORT. OF THE %s kWh THE BATTERY DELIVERS A YEAR,"
    % R["discharged_per_year"],
    "%s kWh CARRIES THE ESSENTIAL BOARD THROUGH THE OUTAGE (%.1f %% OF OUTAGE DEMAND MET) AND %s kWh"
    % (R["discharged_to_outage"], R["outage_served_pct"], R["discharged_to_peak"]),
    "DISPLACES DAY TIME IMPORT OVER THE %d kW TARGET." % R["peak_target_kw"]]
for i, t in enumerate(perf_note):
    d.text("07-TEXT", PX, perf_end - 100 - i * 620, H_TXT, t)

# ------------------------------------------------------------------ sensitivity
SXX, SYY = 45000, 25000
d.text("07-TEXT", SXX, SYY + 1300, 320, "OVERNIGHT CHARGE TARGET, SENSITIVITY")
d.text("07-TEXT", SXX, SYY + 650, H_TXT,
       "HOW FULL TO CHARGE OFF PEAK IS THE ONE SETTING THAT TRADES THE THREE JOBS AGAINST EACH OTHER.")
table(SXX, SYY - 400,
      ["CHARGE TO", "OUTAGE MET", "HOURS OVER %d kW" % R["peak_target_kw"], "HOURS CUT", "PV STORED", "CYCLES / YR"],
      [[("%d %%" % r["grid_charge_target_pct"]),
        ("%.1f %%" % r["outage_served_pct"]),
        r["hours_over_target"],
        ("%.1f %%" % r["hours_over_cut_pct"]),
        ("%s kWh" % r["pv_surplus_captured"]),
        r["equivalent_full_cycles"]] for r in SENS],
      [0, 4200, 10000, 18500, 22000, 28500], 33000)
d.text("07-TEXT", SXX, SYY - 4400, H_TXT,
       "%d %% IS THE SETTING DRAWN. CHARGING FULLER SHAVES BETTER AND COVERS THE OUTAGE BETTER BUT LEAVES"
       % R["grid_charge_target_pct"])
d.text("07-TEXT", SXX, SYY - 5020, H_TXT,
       "NO ROOM FOR THE MIDDAY PV SURPLUS. AT 100 % THE BATTERY TAKES NO PV AT ALL.")

# ------------------------------------------------------------------ notes
NX, NY = 3000, perf_end - 100 - (len(perf_note) - 1) * 620 - 3300   # below the performance note, so they never collide
d.text("07-TEXT", NX, NY + 1300, 320, "BATTERY DESIGN NOTES")
notes = [
    "1. BATTERY %s kWh NOMINAL, %s kWh USABLE AT %d %% DEPTH OF DISCHARGE. %d No. FOXESS CQ7 LFP MODULES IN SERIES AT" % (
        B["kwh_nominal"], B["kwh_usable"], D.BAT["dod"] * 100, B["modules"]),
    "   %s V NOMINAL, ONE MASTER AND %d SLAVES, ON BATTERY PORT 1 OF THE THREE THE INVERTER PROVIDES." % (
        B["v_nominal"], B["modules"] - 1),
    "2. POWER IS SET BY THE PORT, NOT BY THE CELLS. 80 A AT %s V IS %s kW CONTINUOUS, WHICH IS %.2f C ON THIS STACK." % (
        B["v_nominal"], B["kw_continuous"], B["c_rate"]),
    "   THE CQ7 CAN GIVE %d A FOR 60 s, BUT THE 80 A PORT CAPS IT, SO %s kW IS ALSO THE PEAK. 240 A ACROSS ALL 3 PORTS." % (
        D.BAT["i_peak"], B["kw_continuous"]),
    "3. THE SITE LOAD IS %.1f TIMES THE PV GENERATION, SO THERE IS ALMOST NO SURPLUS TO STORE. A BATTERY CHARGED ONLY" % (
        R["site_load"] / R["pv_generated"]),
    "   FROM PV SURPLUS WOULD CYCLE ABOUT %d TIMES A YEAR AND WOULD NOT BE WORTH FITTING. IT EARNS ITS PLACE BY" % round(
        R["pv_only_cycles"]),
    "   BEING CHARGED OFF PEAK AND BY CARRYING THE OUTAGE, WHICH IS WHY THE CONTROL ABOVE IS BUILT THE WAY IT IS.",
    "4. THE ANNUAL GRID PEAK IS NOT REDUCED. IT FALLS ON A DECEMBER AFTERNOON WHEN THERE IS NO PV LEFT AND THE STATE",
    "   OF CHARGE IS PINNED AT THE FLOOR THAT PROTECTS THE 18:00 OUTAGE. HOURS SPENT OVER THE TARGET DO FALL, BY",
    "   %.1f %%. LOWERING THE ANNUAL MAXIMUM AS WELL WOULD NEED A SECOND CQ7 STACK ON PORT 2, OR AN AGREEMENT TO" % (
        R["hours_over_target_cut_pct"]),
    "   ACCEPT A SHORTER BACKUP THROUGH THE WINTER. THAT IS A COMMERCIAL DECISION, NOT AN ELECTRICAL ONE.",
    "5. %.1f EQUIVALENT FULL CYCLES A YEAR. AT A TYPICAL LFP WARRANTY OF 6000 CYCLES TO 70 %% THAT IS ABOUT %d YEARS," % (
        R["equivalent_full_cycles"], round(6000 / R["equivalent_full_cycles"])),
    "   JUST PAST THE 25 YEAR LIFE OF THE ARRAY, SO CALENDAR AGEING AND THE WARRANTY TERM WILL DECIDE REPLACEMENT.",
    "6. BATTERY PACK (DC) ROUND TRIP EFFICIENCY TAKEN AT %d %%, SPLIT EVENLY ACROSS CHARGE AND DISCHARGE, GIVING %s kWh" % (
        D.BAT["rte"] * 100, R["round_trip_loss"]),
    "   OF LOSS A YEAR. INVERTER CONVERSION LOSSES ON THE WAY IN AND OUT ARE NOT INCLUDED.",
    "7. THE LOAD PROFILE, THE DAILY OUTAGE WINDOW AND THE TARIFF PERIODS ARE DESIGN ASSUMPTIONS, NOT METERED DATA.",
    "   THEY ARE DECLARED IN THE MODEL AND WOULD BE REPLACED WITH HALF HOURLY METER DATA BEFORE ANYTHING IS ORDERED.",
]
for i, s in enumerate(notes):
    d.text("07-TEXT", NX, NY - 400 - i * 620, H_TXT, s)
assert NY - 400 - (len(notes) - 1) * 620 > 1400, "notes run off the bottom of the sheet"

open("PV-03 Battery Control and Performance.dxf", "w", encoding="latin1", newline="").write(d.dumps())
open("PV-03 Battery Control and Performance.scr", "w", encoding="latin1", newline="").write(d.dumps_scr("PV-03 Battery Control and Performance"))
print("PV-03 written, %d entities" % len(d.e))
