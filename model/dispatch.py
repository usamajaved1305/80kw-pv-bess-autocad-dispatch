"""Hourly dispatch model for the 80 kW PV plus FoxESS CQ7 battery.

Plain Python, no libraries, so every number can be traced by reading the file.

The first thing this model showed is the thing worth knowing about the site: the
load is three times the PV, so there is almost no surplus to store. A battery
charged only from surplus PV does nothing. It earns its place by being charged
off peak from the grid and then asked to do three jobs:

  1. Ride the essential board through the daily outage. Non negotiable, so a
     state of charge floor protects it all day.
  2. Hold the grid import under the maximum demand target, which is what the
     tariff bills on.
  3. Take whatever PV surplus there is, in preference to exporting it.

Control, by hour:
  00:00 to 05:00  charge from grid at the off peak rate, up to full
  06:00 to 17:00  charge from PV surplus, discharge only to shave the peak,
                  and never below the floor that protects the outage
  17:00 to 18:00  hold, the outage is coming
  18:00 to 20:00  grid is off, the EPS board runs on PV plus battery
  20:00 to 24:00  shave the evening load down to the backup reserve

Site load, outage window and tariff periods are design assumptions and are
declared here. Equipment limits come from the datasheets, through design.py.
"""
import json, math

import design as D

LAT = 33.68                       # Islamabad
ANNUAL_PV = D.out["yield"]["annual_kwh"]

CLEARNESS = [0.62, 0.64, 0.68, 0.72, 0.74, 0.68, 0.54, 0.55, 0.68, 0.73, 0.69, 0.62]
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

WEEKDAY = [12, 12, 12, 12, 12, 14, 32, 55, 72, 80, 84, 85,
           78, 80, 84, 82, 76, 58, 48, 45, 42, 38, 20, 14]
WEEKEND = [12, 12, 12, 12, 12, 12, 16, 22, 26, 28, 28, 26,
           24, 26, 28, 28, 26, 22, 20, 18, 16, 14, 12, 12]

ESSENTIAL_KW = 15.0               # the loads wired to the EPS board
OUTAGE_HOURS = (18, 19)           # a two hour evening outage, every day
GRID_CHARGE_HOURS = (0, 1, 2, 3, 4)
GRID_CHARGE_TARGET = 0.75         # stop short of full, so there is room for the midday PV surplus
PEAK_TARGET_KW = 55.0             # grid import the site wants to stay under
RESERVE_SOC = 0.10                # hard floor, protects the cells
OUTAGE_FLOOR = 0.55               # held through the day to protect the evening outage

BAT_KWH = D.out["battery"]["kwh_nominal"]
BAT_USABLE = D.out["battery"]["kwh_usable"]
BAT_KW = D.out["battery"]["kw_continuous"]
ETA = math.sqrt(D.BAT["rte"])     # round trip loss split across charge and discharge
INV_KW = D.INV["ac_nom"] / 1000.0


def clear_sky_shape(doy, hour):
    """Relative irradiance on the array plane, 0 to 1, from solar geometry alone."""
    decl = 23.45 * math.sin(math.radians(360 * (284 + doy) / 365))
    ha = 15.0 * (hour + 0.5 - 12.0)
    s = (math.sin(math.radians(LAT)) * math.sin(math.radians(decl))
         + math.cos(math.radians(LAT)) * math.cos(math.radians(decl)) * math.cos(math.radians(ha)))
    if s <= 0:
        return 0.0
    am = 1.0 / (s + 0.50572 * (6.07995 + math.degrees(math.asin(s))) ** -1.6364)
    return s * 0.7 ** (am ** 0.678)


def build_year():
    pv, load, hours = [], [], []
    doy = 0
    for m, nd in enumerate(DAYS):
        for _ in range(nd):
            doy += 1
            prof = WEEKEND if doy % 7 == 0 else WEEKDAY
            for h in range(24):
                pv.append(clear_sky_shape(doy, h) * CLEARNESS[m])
                load.append(float(prof[h]))
                hours.append(h)
    scale = ANNUAL_PV / sum(pv)
    pv = [min(p * scale, INV_KW) for p in pv]     # the 80 kW inverter clips the peak
    return pv, load, hours


def floor_for(h, off_grid):
    if off_grid:
        return BAT_KWH * RESERVE_SOC              # an outage may draw the whole usable store
    if 6 <= h < 18:
        return BAT_KWH * OUTAGE_FLOOR             # protect the evening outage
    return BAT_KWH * RESERVE_SOC


def run(pv, load, hours, battery=True, outages=True, grid_charge=True):
    soc = BAT_KWH * OUTAGE_FLOOR
    imp = exp = chg_pv = chg_grid = dis = dis_out = 0.0
    unserved = outage_served = peak = 0.0
    series = []
    for p, l, h in zip(pv, load, hours):
        off_grid = outages and h in OUTAGE_HOURS
        demand = ESSENTIAL_KW if off_grid else l   # only the EPS board runs in an outage
        direct = min(p, demand)
        surplus = p - direct
        deficit = demand - direct
        c = d = g = 0.0
        if battery:
            if surplus > 0:                        # PV surplus first, it is free
                c = min(surplus, BAT_KW, max(0.0, BAT_KWH - soc) / ETA)
                soc += c * ETA
                surplus -= c
                chg_pv += c
            if grid_charge and not off_grid and h in GRID_CHARGE_HOURS:
                g = min(BAT_KW - c, max(0.0, BAT_KWH * GRID_CHARGE_TARGET - soc) / ETA)
                soc += g * ETA
                chg_grid += g
            if deficit > 0:
                avail = max(0.0, soc - floor_for(h, off_grid))
                want = deficit if off_grid else max(0.0, deficit - PEAK_TARGET_KW)
                d = min(want, BAT_KW, avail * ETA)
                soc -= d / ETA
                deficit -= d
                dis += d
                if off_grid:
                    dis_out += d                   # discharge that carried the outage
        if off_grid:
            unserved += deficit
            outage_served += direct + d
            grid = 0.0
        else:
            grid = deficit + g                     # grid charging shows up as import too
            imp += grid
            peak = max(peak, grid)
            exp += surplus
        series.append((round(p, 2), round(demand, 2), round(c + g, 2), round(d, 2),
                       round(soc / BAT_KWH * 100, 1), round(grid, 2)))
    over = sum(1 for x in series if x[5] > PEAK_TARGET_KW)
    return dict(over=over, imp=imp, exp=exp, chg_pv=chg_pv, chg_grid=chg_grid, dis=dis, dis_out=dis_out, peak=peak,
                unserved=unserved, outage_served=outage_served, series=series)


APR_DAY, DEC_DAY = 103, 351       # the two weekdays drawn on PV-03, as day of year minus one


def summarise():
    pv, load, hours = build_year()
    base = run(pv, load, hours, battery=False)
    with_b = run(pv, load, hours, battery=True)
    pv_total, load_total = sum(pv), sum(load)
    need = ESSENTIAL_KW * len(OUTAGE_HOURS) * 365
    r = dict(
        pv_generated=round(pv_total),
        site_load=round(load_total),
        pv_share_of_load_pct=round(pv_total / load_total * 100, 1),

        peak_no_batt=round(base["peak"], 1),
        peak_with_batt=round(with_b["peak"], 1),
        peak_cut_kw=round(base["peak"] - with_b["peak"], 1),
        peak_cut_pct=round((base["peak"] - with_b["peak"]) / base["peak"] * 100, 1),
        peak_target_kw=PEAK_TARGET_KW,
        hours_over_target_no_batt=base["over"],
        hours_over_target_with_batt=with_b["over"],
        hours_over_target_cut_pct=round((base["over"] - with_b["over"]) / base["over"] * 100, 1),
        grid_charge_target_pct=GRID_CHARGE_TARGET * 100,

        outage_demand_per_year=round(need),
        outage_served_with_batt=round(with_b["outage_served"]),
        outage_served_pct=round(with_b["outage_served"] / need * 100, 1),
        outage_unserved_no_batt=round(base["unserved"]),
        outage_unserved_with_batt=round(with_b["unserved"]),
        outage_hours_per_year=len(OUTAGE_HOURS) * 365,
        outage_window="%02d:00 to %02d:00" % (OUTAGE_HOURS[0], OUTAGE_HOURS[-1] + 1),

        export_no_batt=round(base["exp"]),
        export_with_batt=round(with_b["exp"]),
        pv_surplus_captured=round(base["exp"] - with_b["exp"]),
        grid_import_no_batt=round(base["imp"]),
        grid_import_with_batt=round(with_b["imp"]),

        charged_from_pv=round(with_b["chg_pv"]),
        charged_from_grid=round(with_b["chg_grid"]),
        discharged_per_year=round(with_b["dis"]),
        equivalent_full_cycles=round(with_b["dis"] / BAT_USABLE, 1),
        round_trip_loss=round(with_b["chg_pv"] + with_b["chg_grid"] - with_b["dis"]),

        backup_reserve_kwh=round(BAT_KWH * (OUTAGE_FLOOR - RESERVE_SOC), 1),
        backup_hours_at_floor=round(BAT_KWH * (OUTAGE_FLOOR - RESERVE_SOC) / ESSENTIAL_KW, 2),
        backup_hours_full=round(BAT_USABLE / ESSENTIAL_KW, 2),
        essential_kw=ESSENTIAL_KW,
        outage_floor_pct=OUTAGE_FLOOR * 100,
    )
    # what the discharge was used for, and the PV-only case the design started from
    pv_only = run(pv, load, hours, battery=True, outages=False, grid_charge=False)
    r.update(
        discharged_to_outage=round(with_b["dis_out"]),
        discharged_to_peak=round(with_b["dis"] - with_b["dis_out"]),
        pv_only_cycles=round(pv_only["dis"] / BAT_USABLE, 1),
        soc_start_apr=with_b["series"][APR_DAY * 24 - 1][4],
        soc_start_dec=with_b["series"][DEC_DAY * 24 - 1][4],
    )
    return r, with_b


if __name__ == "__main__":
    r, w = summarise()
    print(json.dumps(r, indent=2))
    json.dump(r, open("dispatch.json", "w"), indent=2)
    # two weekdays: a typical April day when PV is strong, and the December day
    # that sets the annual grid peak
    apr, dec = APR_DAY * 24, DEC_DAY * 24
    json.dump({"apr": w["series"][apr:apr + 24], "dec": w["series"][dec:dec + 24]},
              open("days.json", "w"), indent=1)
