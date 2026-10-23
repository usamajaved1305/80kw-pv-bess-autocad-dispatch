"""Draws the two representative dispatch days as one web sized figure.

The charts on PV-03 are sized for an A1 plot. Cropped down to the width a web
page gives them the axis labels fall under 7 px, so this redraws the same data
at a size that reads on screen.
"""
import json

BG = "#1e2228"
GRID = "#39414c"
TXT = "#e8eaed"
DIM = "#9aa0a6"
PV = "#6fa8ff"
LOAD = "#e8eaed"
IMPORT = "#ff5b5b"
SOC = "#e081ff"
BAND = "#3b3524"

DAYS = json.load(open("days.json"))
R = json.load(open("dispatch.json"))

W = 1800
PAD_L, PAD_R, PAD_T, PAD_B = 90, 95, 76, 58
PH = 420                      # plot height
PANEL = PAD_T + PH + PAD_B
KW_MAX = 90.0
OUT = (18, 19)

panels = [
    ("dec", "December weekday", "The day that sets the annual peak at %.1f kW" % R["peak_with_batt"]),
    ("apr", "Typical April weekday", "Grid import kept at or below the %d kW target all day" % R["peak_target_kw"]),
]

o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
     % (W, PANEL * 2 + 54, W, PANEL * 2 + 54),
     '<rect width="%d" height="%d" fill="%s"/>' % (W, PANEL * 2 + 54, BG),
     '<style>text{font-family:"DejaVu Sans Mono","Consolas",monospace}</style>']


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


for pi, (key, title, sub) in enumerate(panels):
    day = DAYS[key]
    top = pi * PANEL
    x0, y0 = PAD_L, top + PAD_T
    pw = W - PAD_L - PAD_R
    sx = pw / 24.0
    sy = PH / KW_MAX

    o.append('<text x="%d" y="%d" fill="%s" font-size="30" font-weight="bold">%s</text>'
             % (x0, top + 34, TXT, esc(title)))
    o.append('<text x="%d" y="%d" fill="%s" font-size="22">%s</text>'
             % (x0 + len(title) * 18 + 50, top + 34, DIM, esc(sub)))   # clear of the title, 30 px mono

    # the outage window
    o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"/>'
             % (x0 + OUT[0] * sx, y0, (OUT[-1] + 1 - OUT[0]) * sx, PH, BAND))
    o.append('<text x="%.1f" y="%d" fill="#ffd34d" font-size="20">OUTAGE</text>'
             % (x0 + OUT[0] * sx + 6, y0 + 24))

    # axes
    for kw in range(0, int(KW_MAX) + 1, 20):
        y = y0 + PH - kw * sy
        o.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>'
                 % (x0, y, x0 + pw, y, GRID))
        o.append('<text x="%d" y="%.1f" fill="%s" font-size="21" text-anchor="end">%d</text>'
                 % (x0 - 12, y + 7, DIM, kw))
    o.append('<text x="%d" y="%d" fill="%s" font-size="21" text-anchor="end">kW</text>'
             % (x0 - 12, y0 - 10, DIM))
    for pct in range(0, 101, 25):
        y = y0 + PH - pct / 100.0 * PH
        o.append('<text x="%.1f" y="%.1f" fill="%s" font-size="21">%d</text>'
                 % (x0 + pw + 12, y + 7, SOC, pct))
    o.append('<text x="%.1f" y="%d" fill="%s" font-size="21">SoC %%</text>' % (x0 + pw + 12, y0 - 10, SOC))
    for h in range(0, 25, 3):
        x = x0 + h * sx
        o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>'
                 % (x, y0 + PH, x, y0 + PH + 7, GRID))
        o.append('<text x="%.1f" y="%d" fill="%s" font-size="21" text-anchor="middle">%02d</text>'
                 % (x, y0 + PH + 32, DIM, h % 24))
    o.append('<rect x="%d" y="%d" width="%.1f" height="%d" fill="none" stroke="%s" stroke-width="1.5"/>'
             % (x0, y0, pw, PH, GRID))
    # the grid import target the control works to
    ty = y0 + PH - R["peak_target_kw"] * sy
    o.append('<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6" stroke-dasharray="6 6"/>'
             % (x0, ty, x0 + pw, ty, DIM))
    o.append('<text x="%.1f" y="%.1f" fill="%s" font-size="20">Target %d kW</text>'
             % (x0 + 20.3 * sx, ty - 8, DIM, R["peak_target_kw"]))

    def step(idx, colour, width=2.6):
        pts = []
        for i, row in enumerate(day):
            v = y0 + PH - row[idx] * sy
            pts.append("%.1f,%.1f" % (x0 + i * sx, v))
            pts.append("%.1f,%.1f" % (x0 + (i + 1) * sx, v))
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>'
                 % (" ".join(pts), colour, width))

    step(0, PV)        # PV generation
    step(1, LOAD)      # site demand
    step(5, IMPORT)    # grid import
    # state of charge at the end of each hour, from the end of the day before
    soc = ["%.1f,%.1f" % (x0, y0 + PH - R["soc_start_" + key] / 100.0 * PH)] +           ["%.1f,%.1f" % (x0 + (i + 1) * sx, y0 + PH - row[4] / 100.0 * PH) for i, row in enumerate(day)]
    o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.6" stroke-dasharray="9 6"/>'
             % (" ".join(soc), SOC))

# legend
ly = PANEL * 2 + 30
for i, (c, lbl, dash) in enumerate([(PV, "PV generation", ""), (LOAD, "Site demand", ""),
                                    (IMPORT, "Grid import", ""),
                                    (SOC, "State of charge", ' stroke-dasharray="9 6"')]):
    x = PAD_L + i * 400
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="3"%s/>'
             % (x, ly, x + 46, ly, c, dash))
    o.append('<text x="%d" y="%d" fill="%s" font-size="22">%s</text>' % (x + 60, ly + 8, DIM, lbl))

o.append("</svg>")
open("w5-dispatch.svg", "w", encoding="utf-8").write("\n".join(o))
print("w5-dispatch.svg written, %dx%d" % (W, PANEL * 2 + 54))
