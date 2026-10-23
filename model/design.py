"""80 kW commercial PV with FoxESS battery storage: the sizing calculations.

Every equipment figure below is taken from the manufacturer datasheet named beside it.
Site and load figures are design assumptions and are labelled as such.
"""
import json, math

# ----------------------------------------------------------------- equipment data
MOD = dict(                      # Jinko JKM580N-72HL4-V, Tiger Neo 72HL4-(V) 570-590 W datasheet
    name="Jinko JKM580N-72HL4-V",
    pmax=580.0, vmp=43.35, imp=13.38, voc=52.31, isc=14.01,
    tc_voc=-0.25,                # %/degC
    tc_pmax=-0.29,               # %/degC
    fuse=25.0,                   # A series fuse rating
    length=2278, width=1134, depth=30,   # mm
)

INV = dict(                      # FoxESS P3-80-Plus, P3 Plus datasheet V1.0 2025/05/14
    name="FoxESS P3-80-Plus",
    ac_nom=80000.0, ac_max=88000.0,      # W, VA
    ac_imax_380=133.7,                   # A per phase at 380 V
    v_ac=400.0,
    pv_max=160.0,                        # kW max array and max input power
    v_dc_max=1000.0,                     # V withstand
    v_dc_nom=750.0,
    mppt_lo=180.0, mppt_hi=850.0,
    v_start=180.0,
    mppt_imax=40.0, mppt_iscmax=55.0,
    n_mppt=8, strings_per_mppt=2,
    bat_lo=180.0, bat_hi=950.0,
    bat_imax=80.0,                       # A per port, 3 ports, 240 A total
    bat_ports=3,
    eps_max=88000.0,                     # VA, EPS output for the P3-80-Plus column
    eff_max=98.2, eff_eu=97.6,
    h=1060, w=730, d=305, kg=120,        # mm, kg
)

BAT = dict(                      # FoxESS CQ7 high voltage battery
    name="FoxESS CQ7",
    kwh_module=7.02, v_module=57.6,
    dod=0.90,
    i_max=80.0, i_rec=50.0, i_peak=110.0,   # A, peak for 60 s
    max_modules=14,                          # 1 master + 13 slaves
    rte=0.95,
    chem="LFP (LiFePO4)",
)

SITE = dict(                     # design assumptions, not measured data
    place="Commercial unit, I-10 Industrial Area, Islamabad",
    t_min=-5.0,                  # degC, design minimum cell temperature
    t_cell_max=70.0,             # degC, design maximum cell temperature
    tilt=15.0, azimuth=180.0,
    yield_kwh_per_kwp=1480.0,    # modelled specific yield for Islamabad, fixed tilt
)

out = {}

# ----------------------------------------------------------------- string sizing
# Voltage rises as temperature falls, so the cold morning sets the string length.
dt_cold = 25.0 - SITE["t_min"]
voc_cold = MOD["voc"] * (1 + abs(MOD["tc_voc"]) / 100 * dt_cold)
n_max_by_voltage = math.floor(INV["v_dc_max"] / voc_cold)

# The hot afternoon sets the lower end: the string must stay inside the MPPT window.
dt_hot = SITE["t_cell_max"] - 25.0
vmp_hot = MOD["vmp"] * (1 - abs(MOD["tc_voc"]) / 100 * dt_hot)

STRING_N = 17
STRINGS = 8
MODULES = STRING_N * STRINGS
kwp = MODULES * MOD["pmax"] / 1000.0

out["string"] = dict(
    voc_cold_module=round(voc_cold, 2),
    n_max_by_voltage=n_max_by_voltage,
    chosen=STRING_N,
    voc_cold_string=round(STRING_N * voc_cold, 1),
    headroom_pct=round((INV["v_dc_max"] - STRING_N * voc_cold) / INV["v_dc_max"] * 100, 1),
    vmp_hot_string=round(STRING_N * vmp_hot, 1),
    vmp_stc_string=round(STRING_N * MOD["vmp"], 1),
    above_mppt_min=STRING_N * vmp_hot > INV["mppt_lo"],
)

out["array"] = dict(
    modules=MODULES, strings=STRINGS, per_string=STRING_N,
    kwp=round(kwp, 2),
    dc_ac_ratio=round(kwp * 1000 / INV["ac_nom"], 2),
    strings_per_mppt=STRINGS / INV["n_mppt"],
    mppt_current=MOD["imp"], mppt_isc=MOD["isc"],
    mppt_current_limit=INV["mppt_imax"], mppt_isc_limit=INV["mppt_iscmax"],
    string_fuses_needed=False,
)

# ----------------------------------------------------------------- battery sizing
N_BAT = 9
bat_kwh = N_BAT * BAT["kwh_module"]
bat_v = N_BAT * BAT["v_module"]
bat_kw = bat_v * BAT["i_max"] / 1000.0
out["battery"] = dict(
    modules=N_BAT,
    kwh_nominal=round(bat_kwh, 2),
    kwh_usable=round(bat_kwh * BAT["dod"], 2),
    v_nominal=round(bat_v, 1),
    inside_inverter_window=INV["bat_lo"] < bat_v < INV["bat_hi"],
    kw_continuous=round(bat_kw, 1),
    kw_peak_60s=round(bat_v * BAT["i_peak"] / 1000.0, 1),
    c_rate=round(bat_kw / bat_kwh, 2),
    ports_used=1, ports_spare=INV["bat_ports"] - 1,
    expandable_kwh=round(BAT["max_modules"] * BAT["kwh_module"] * INV["bat_ports"], 1),
)

# ----------------------------------------------------------------- AC side
i_ac_nom = INV["ac_nom"] / (math.sqrt(3) * INV["v_ac"])
i_ac_max = INV["ac_max"] / (math.sqrt(3) * INV["v_ac"])
out["ac"] = dict(
    i_nominal=round(i_ac_nom, 1),
    i_max=round(i_ac_max, 1),
    i_max_at_380=INV["ac_imax_380"],
    mccb="160 A 4 pole",
    isolator="250 A 4 pole",
    cable="4C 95 mm2 Cu",
    eps_kva=INV["eps_max"] / 1000.0,
)

# ----------------------------------------------------------------- yield
annual = kwp * SITE["yield_kwh_per_kwp"]
out["yield"] = dict(
    specific=SITE["yield_kwh_per_kwp"],
    annual_kwh=round(annual),
    daily_avg_kwh=round(annual / 365, 1),
)



# ----------------------------------------------------------------- mechanical setting out
def _solar(doy, hour, lat=33.68):
    d = math.radians(23.45 * math.sin(math.radians(360 * (284 + doy) / 365)))
    ha = math.radians(15.0 * (hour - 12.0))
    la = math.radians(lat)
    el = math.asin(math.sin(la) * math.sin(d) + math.cos(la) * math.cos(d) * math.cos(ha))
    az = math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(d) * math.cos(la))
    return math.degrees(el), (math.degrees(az) + 180.0) % 360.0


TILT = 15.0
MOD_L, MOD_W = MOD["length"], MOD["width"]          # 2278 x 1134 mm
proj = MOD_W * math.cos(math.radians(TILT))          # landscape, slope runs along the 1134 side
rise = MOD_W * math.sin(math.radians(TILT))

# the shading case: 21 December, 09:00, the start of the solar window the site wants clear
el, az = _solar(355, 9.0)
shadow = rise * abs(math.cos(math.radians(az - 180.0))) / math.tan(math.radians(el))
pitch_min = proj + shadow
PITCH = 1800.0                                       # chosen, rounded up from pitch_min

ROWS, PER_ROW = 8, 17
GAP = 20.0
row_len = PER_ROW * MOD_L + (PER_ROW - 1) * GAP
array_depth = (ROWS - 1) * PITCH + proj

out["mech"] = dict(
    tilt=TILT, module_mm=[MOD_L, MOD_W, MOD["depth"]],
    projected_depth=round(proj),
    rise=round(rise),
    shading_case="21 December 09:00",
    sun_elevation=round(el, 1), sun_azimuth=round(az, 1),
    shadow=round(shadow),
    pitch_min=round(pitch_min),
    pitch_used=PITCH,
    ground_cover_ratio=round(MOD_W / PITCH, 2),          # slope length over pitch, as PVsyst defines it
    rows=ROWS, per_row=PER_ROW,
    row_length=round(row_len),
    array_depth=round(array_depth),
    array_area=round(row_len * array_depth / 1e6, 1),
    roof=[46000, 24000],
    roof_area=round(46000 * 24000 / 1e6),
    coverage_pct=round(row_len * array_depth / (46000 * 24000) * 100, 1),
    rail_front=300, rail_rear=round(300 + rise),
)


if __name__ == "__main__":
    print(json.dumps(out, indent=2))
    with open("design.json", "w") as f:
        json.dump(dict(mod=MOD, inv=INV, bat=BAT, site=SITE, out=out), f, indent=2)
