"""Writes the two A1 drawings for the 80 kW PV plus battery project as DXF R12.

Everything is drawn full size in millimetres with the sheet border scaled by 100,
so the plot comes out at 1:100 and any dimension read off the model is true.

PV-01  mechanical: roof layout, row setting out, mounting section, plant area
PV-02  electrical: single line diagram, battery, EPS board, earthing, schedule

Text widths are checked against AutoCAD's rendered advance of 0.96 of the text
height, not the 0.6 nominal, so labels sit inside their boxes.
"""
import math
import design as D

ADV = 0.96                        # AutoCAD renders txt.shx at about this per character

SHEET_W, SHEET_H = 84100, 59400   # A1 at 1:100
LAYERS = {
    "00-BORDER": 7,
    "01-ROOF": 7,
    "02-MOUNT": 4,
    "03-PV-MODULE": 5,
    "06-DIMS": 2,
    "07-TEXT": 7,
    "08-ELEC": 1,
    "09-CABLE": 3,
    "10-EARTH": 4,
    "11-BATTERY": 6,
    "12-CONTROL": 6,
    "13-TAG": 2,
}


class Dxf:
    def __init__(self):
        self.e = []

    def line(self, layer, x1, y1, x2, y2):
        self.e.append(("LINE", layer, (x1, y1, x2, y2)))

    def rect(self, layer, x1, y1, x2, y2):
        self.line(layer, x1, y1, x2, y1)
        self.line(layer, x2, y1, x2, y2)
        self.line(layer, x2, y2, x1, y2)
        self.line(layer, x1, y2, x1, y1)

    def circle(self, layer, cx, cy, r):
        self.e.append(("CIRCLE", layer, (cx, cy, r)))

    def text(self, layer, x, y, h, s):
        self.e.append(("TEXT", layer, (x, y, h, str(s))))

    def width(self, h, s):
        return len(str(s)) * ADV * h

    def dim_h(self, y, x1, x2, label, h=200, tick=180):
        """A horizontal dimension line with ticks and a centred label above it."""
        self.line("06-DIMS", x1, y, x2, y)
        for x in (x1, x2):
            self.line("06-DIMS", x, y - tick, x, y + tick)
        w = self.width(h, label)
        self.text("06-DIMS", (x1 + x2) / 2 - w / 2, y + tick + 60, h, label)

    def dim_v(self, x, y1, y2, label, h=200, tick=180):
        self.line("06-DIMS", x, y1, x, y2)
        for y in (y1, y2):
            self.line("06-DIMS", x - tick, y, x + tick, y)
        self.text("06-DIMS", x + tick + 80, (y1 + y2) / 2 - h / 2, h, label)

    def dumps_scr(self, title):
        """Emits the same sheet as an AutoCAD script.

        Run it inside AutoCAD with the SCRIPT command and AutoCAD draws every
        entity itself with its own LINE, TEXT and CIRCLE commands. Nothing is
        imported, so the result is a native drawing you can edit and save as DWG.
        """
        o = ["; " + title,
             "; run with the SCRIPT command inside AutoCAD",
             "OSMODE", "0",            # no object snap, so points land exactly where told
             "ORTHOMODE", "0",
             "ATTDIA", "0",
             "DTEXTED", "1",           # one line per TEXT command; the default (2) leaves
                                       # TEXT waiting on screen and stalls the script
             "LIMITS", "0,0", "%d,%d" % (SHEET_W, SHEET_H)]

        names = list(LAYERS.keys())
        o += ["-LAYER", "N", ",".join(names)]
        for name, col in LAYERS.items():
            o += ["C", str(col), name]
        o += [""]                      # leave the LAYER command

        cur = None
        for kind, layer, p in self.e:
            if layer != cur:
                o += ["CLAYER", layer]
                cur = layer
            if kind == "LINE":
                o += ["LINE", "%.3f,%.3f" % (p[0], p[1]), "%.3f,%.3f" % (p[2], p[3]), ""]
            elif kind == "CIRCLE":
                o += ["CIRCLE", "%.3f,%.3f" % (p[0], p[1]), "%.3f" % p[2]]
            else:
                txt = str(p[3])
                # a leading space reads as Enter inside a script and would end the
                # TEXT command early, so indent by moving the start point instead
                lead = len(txt) - len(txt.lstrip(" "))
                txt = txt.lstrip(" ")
                if not txt:
                    continue
                x = p[0] + lead * ADV * p[2]
                # no blank line after the text: with DTEXTED at 1 the command
                # already ends here, and a blank line would start TEXT again
                o += ["TEXT", "%.3f,%.3f" % (x, p[1]), "%.3f" % p[2], "0", txt]

        o += ["ZOOM", "E",
              "DTEXTED", "2"]          # put AutoCAD's default back
        return "\r\n".join(o) + "\r\n"

    def dumps(self):
        o = []

        def g(c, v):
            o.append(str(c))
            o.append(str(v))

        g(0, "SECTION"); g(2, "HEADER")
        g(9, "$ACADVER"); g(1, "AC1009")
        g(9, "$INSBASE"); g(10, 0.0); g(20, 0.0); g(30, 0.0)
        g(9, "$EXTMIN"); g(10, 0.0); g(20, 0.0); g(30, 0.0)
        g(9, "$EXTMAX"); g(10, float(SHEET_W)); g(20, float(SHEET_H)); g(30, 0.0)
        g(0, "ENDSEC")

        g(0, "SECTION"); g(2, "TABLES")
        g(0, "TABLE"); g(2, "LAYER"); g(70, len(LAYERS))
        for name, col in LAYERS.items():
            g(0, "LAYER"); g(2, name); g(70, 0); g(62, col); g(6, "CONTINUOUS")
        g(0, "ENDTAB"); g(0, "ENDSEC")

        g(0, "SECTION"); g(2, "ENTITIES")
        for kind, layer, p in self.e:
            if kind == "LINE":
                g(0, "LINE"); g(8, layer)
                g(10, float(p[0])); g(20, float(p[1])); g(30, 0.0)
                g(11, float(p[2])); g(21, float(p[3])); g(31, 0.0)
            elif kind == "CIRCLE":
                g(0, "CIRCLE"); g(8, layer)
                g(10, float(p[0])); g(20, float(p[1])); g(30, 0.0); g(40, float(p[2]))
            else:
                g(0, "TEXT"); g(8, layer)
                g(10, float(p[0])); g(20, float(p[1])); g(30, 0.0)
                g(40, float(p[2])); g(1, p[3])
        g(0, "ENDSEC"); g(0, "EOF")
        return "\r\n".join(o) + "\r\n"


def border(d, number, title, sub, scale, rev="P1", date="08.10.2026", status="ISSUED FOR COMMENT"):
    """Sheet frame and title block. The bottom row carries the revision, date,
    issue status and the check and approval cells a drawing needs to be issued."""
    m = 1000
    d.rect("00-BORDER", m, m, SHEET_W - m, SHEET_H - m)
    tb_x, tb_y, tb_w, tb_h = SHEET_W - m - 24000, m, 24000, 5800
    d.rect("00-BORDER", tb_x, tb_y, tb_x + tb_w, tb_y + tb_h)
    d.line("00-BORDER", tb_x, tb_y + 4200, tb_x + tb_w, tb_y + 4200)
    d.line("00-BORDER", tb_x, tb_y + 2800, tb_x + tb_w, tb_y + 2800)
    d.line("00-BORDER", tb_x, tb_y + 1200, tb_x + tb_w, tb_y + 1200)
    d.line("00-BORDER", tb_x + 15000, tb_y, tb_x + 15000, tb_y + 2800)
    d.text("07-TEXT", tb_x + 400, tb_y + 4800, 420, title)
    d.text("07-TEXT", tb_x + 400, tb_y + 3250, 340, sub)
    d.text("07-TEXT", tb_x + 400, tb_y + 2200, 240, "DRAWN  USAMA JAVED")
    d.text("07-TEXT", tb_x + 400, tb_y + 1600, 240, "SITE  I-10 INDUSTRIAL AREA, ISLAMABAD")
    d.text("07-TEXT", tb_x + 15400, tb_y + 2200, 240, "SCALE  " + scale)
    d.text("07-TEXT", tb_x + 15400, tb_y + 1600, 240, "DWG  " + number)
    d.text("07-TEXT", tb_x + 400, tb_y + 450, 240, "REV  %s    DATE  %s    CHK  --    APP  --" % (rev, date))
    d.text("07-TEXT", tb_x + 15400, tb_y + 450, 240, status)
