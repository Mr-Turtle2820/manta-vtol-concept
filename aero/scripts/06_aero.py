"""Step 3A-2: AeroSandbox pre-test of the wing extracted from v0_nofin (wing only: no tail, no boom, no motor/prop, no fan openings).
VLM -> lift slope, neutral point, Cm.  AeroBuildup (NeuralFoil sections) -> CL, CD, Cm polar, trim, drag, aero power.
ASSUMPTIONS (all stated in REPORT/README): span scaled to 600 mm; 420 g design weight (never weighed); sea-level ISA;
airfoil = MH 49 thickness-scaled to the mesh's outboard t/c (camber line preserved); twist = 0; planar (z = 0).
Outputs: aero/aero_results.json, aero/alpha_sweep.csv, aero/*.png
"""
import os, json, csv, numpy as np, aerosandbox as asb, warnings
from scipy.optimize import brentq
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
WORK = r"E:\Sewa_first\manta\v0_work"; OUT = os.path.join(WORK, "aero")
S = json.load(open(os.path.join(OUT, "wing_stations.json")))
CH = json.load(open(os.path.join(OUT, "airfoil_choice.json")))
WEIGHT_KG, G = 0.420, 9.81                       # ASSUMPTION: design weight never weighed
SPEEDS = [10.0, 12.0, 15.0]; CG_FRACS = [0.35, 0.40, 0.45]
ATM = asb.Atmosphere(altitude=0); RHO = float(ATM.density())

# ---------------- geometry from the mesh extraction ------------------------------------------------------------
stations = [s for s in S["stations"] if s["y"] != 12.0]            # y=12 is a near-duplicate of the root (y=0): dropped
tc_mesh = CH["tc_mesh"]
base = asb.Airfoil("mh49"); t0 = float(base.max_thickness())
def thickness_scaled(af, tc_target, n=80):
    k = tc_target / float(af.max_thickness())
    xs = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
    th = np.array([float(af.local_thickness(x)) for x in xs]); cam = np.array([float(af.local_camber(x)) for x in xs])
    up = np.c_[xs, cam + k * th / 2]; lo = np.c_[xs, cam - k * th / 2]
    return asb.Airfoil(name="%s_t%.1f" % (af.name, 100 * tc_target), coordinates=np.vstack([up[::-1], lo[1:]]))
AF_UNI = thickness_scaled(base, tc_mesh)
FAN_Y = (55.5, 109.5)                                                  # from 04c (rim outer edges, mm)
def station_tc(s):                                                     # sensitivity case: per-station t/c, rim-contaminated stations use the outboard median
    return tc_mesh if FAN_Y[0] - 1 <= s["y"] <= FAN_Y[1] + 1 else s["t_over_c"]
def build_wing(per_station=False):
    xs = []
    for s in stations:
        af = thickness_scaled(base, station_tc(s)) if per_station else AF_UNI
        xs.append(asb.WingXSec(xyz_le=[s["x_le"] / 1000, s["y"] / 1000, 0.0], chord=s["chord"] / 1000, twist=0.0, airfoil=af))
    return asb.Wing(name="v0_nofin_wing", symmetric=True, xsecs=xs)
wing = build_wing(False)
S_REF, C_REF, B_REF = float(wing.area()), float(wing.mean_aerodynamic_chord()), float(wing.span())
root = stations[0]; x_root_le, c_root = root["x_le"] / 1000, root["chord"] / 1000
x_cg = {f: x_root_le + f * c_root for f in CG_FRACS}
W_N = WEIGHT_KG * G
def airplane(w, xref):
    return asb.Airplane(name="a", xyz_ref=[xref, 0, 0], wings=[w], s_ref=S_REF, c_ref=C_REF, b_ref=B_REF)
def op(V, a): return asb.OperatingPoint(atmosphere=ATM, velocity=V, alpha=float(a))

res = dict(assumptions=dict(weight_kg=WEIGHT_KG, g=G, rho=RHO, airfoil=AF_UNI.name, airfoil_base="MH 49 (UIUC), base t/c %.3f, scaled x%.2f" % (t0, tc_mesh / t0),
                            tc_mesh_outboard_median=tc_mesh, twist_deg=0.0, planar_z0=True, stations_used_mm=[[s["y"], s["x_le"], s["chord"]] for s in stations]),
           geometry=dict(S_ref_m2=S_REF, MAC_m=C_REF, span_modelled_m=B_REF, span_mesh_m=S["span_mm"] / 1000, AR=float(wing.aspect_ratio()),
                         root_chord_m=c_root, x_root_le_m=x_root_le, x_cg_m={str(f): x_cg[f] for f in CG_FRACS},
                         mesh_planform_area_raster_m2=S["S_raster_projected_mm2"] * 1e-6, area_pct_model_vs_raster=100 * (S_REF - S["S_raster_projected_mm2"] * 1e-6) / (S["S_raster_projected_mm2"] * 1e-6)))

# ---------------- VLM: lift slope & neutral point (+ resolution check) ----------------------------------------------
def vlm_case(w, xref, a, sr, cr):
    r = asb.VortexLatticeMethod(airplane=airplane(w, xref), op_point=op(15, a), spanwise_resolution=sr, chordwise_resolution=cr).run()
    return float(r["CL"]), float(r["Cm"])
def vlm_np(w, sr, cr):
    x1, x2 = x_cg[0.35], x_cg[0.45]
    out = {}
    for tag, xr in (("x1", x1), ("x2", x2)):
        pts = [(a,) + vlm_case(w, xr, a, sr, cr) for a in (0.0, 2.0, 4.0, 6.0, 8.0)]
        al = np.array([p[0] for p in pts]); cl = np.array([p[1] for p in pts]); cm = np.array([p[2] for p in pts])
        out[tag] = (np.polyfit(al, cl, 1), np.polyfit(al, cm, 1))
    dcl = out["x1"][0][0]                                              # per deg
    s1, s2 = out["x1"][1][0], out["x2"][1][0]                          # dCm/dalpha at the two reference points
    x_np = x1 - s1 * (x2 - x1) / (s2 - s1)
    return dict(CL_alpha_per_deg=float(dcl), CL_alpha_per_rad=float(dcl * 180 / np.pi), CL0=float(out["x1"][0][1]), x_np_m=float(x_np),
                np_frac_MAC_from_root_LE=float((x_np - x_root_le) / C_REF), np_frac_root_chord=float((x_np - x_root_le) / c_root),
                dCm_dalpha_at_cg35_per_deg=float(s1), dCm_dalpha_at_cg45_per_deg=float(s2))
res["VLM"] = {"res_%dx%d" % (sr, cr): vlm_np(wing, sr, cr) for sr, cr in ((5, 5), (8, 8), (12, 10))}
vlm = res["VLM"]["res_8x8"]
print("VLM:", json.dumps(res["VLM"], indent=1))

# ---------------- AeroBuildup: polar, Cm, trim, drag -------------------------------------------------------------------
ALPHAS = np.arange(-4.0, 20.1, 1.0)
def ab(w, V, a, xref):
    r = asb.AeroBuildup(airplane=airplane(w, xref), op_point=op(V, a)).run()
    return float(r["CL"]), float(r["CD"]), float(r["Cm"])
def sweep(w, V):
    rows = {f: [ab(w, V, a, x_cg[f]) for a in ALPHAS] for f in CG_FRACS}
    cl = np.array([r[0] for r in rows[0.40]]); cd = np.array([r[1] for r in rows[0.40]])
    cm = {f: np.array([r[2] for r in rows[f]]) for f in CG_FRACS}
    return cl, cd, cm
cl15, cd15, cm15 = sweep(wing, 15.0)
i_peak = int(np.argmax(cl15))
res["AeroBuildup_15ms"] = dict(alpha=ALPHAS.tolist(), CL=cl15.tolist(), CD=cd15.tolist(), LD=(cl15 / cd15).tolist(), Cm={str(f): cm15[f].tolist() for f in CG_FRACS},
                               alpha_of_max_CL_in_sweep=float(ALPHAS[i_peak]), max_CL_in_sweep=float(cl15[i_peak]),
                               note="Sections' NeuralFoil polars roll over here; this is NOT a validated stall prediction (CLmax is NOT MODELLED).")
lin = (ALPHAS >= 0) & (ALPHAS <= 8)
res["AeroBuildup_15ms"]["CL_alpha_per_deg_fit_0_8"] = float(np.polyfit(ALPHAS[lin], cl15[lin], 1)[0])
# neutral point from the AeroBuildup Cm slopes at two reference points (same two-point method as VLM)
s = {f: float(np.polyfit(ALPHAS[lin], cm15[f][lin], 1)[0]) for f in CG_FRACS}
dcl_ab = res["AeroBuildup_15ms"]["CL_alpha_per_deg_fit_0_8"]
x_np_ab = x_cg[0.35] - s[0.35] * (x_cg[0.45] - x_cg[0.35]) / (s[0.45] - s[0.35])
res["AeroBuildup_NP"] = dict(x_np_m=float(x_np_ab), np_frac_root_chord=float((x_np_ab - x_root_le) / c_root), np_frac_MAC=float((x_np_ab - x_root_le) / C_REF),
                             dCm_dalpha_per_deg={str(f): s[f] for f in CG_FRACS})
# static margin (positive = stable), in % MAC, both methods, at each CG
res["static_margin_pct_MAC"] = {str(f): dict(VLM=100 * (vlm["x_np_m"] - x_cg[f]) / C_REF, AeroBuildup=100 * (x_np_ab - x_cg[f]) / C_REF) for f in CG_FRACS}
res["static_margin_verdict"] = {str(f): ("STABLE (both)" if all(v > 0 for v in res["static_margin_pct_MAC"][str(f)].values())
                                         else "UNSTABLE (both)" if all(v < 0 for v in res["static_margin_pct_MAC"][str(f)].values()) else "SIGN DISAGREES between VLM and AeroBuildup: neutral")
                                for f in CG_FRACS}

# ---------------- required CL, trim angle, drag, aero power at 10/12/15 m/s ------------------------------------------------
def crossing(x, y, target=0.0):
    for i in range(len(x) - 1):
        if (y[i] - target) * (y[i + 1] - target) <= 0 and y[i] != y[i + 1]:
            return float(x[i] + (target - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i]))
    return None
flight = {}
for V in SPEEDS:
    q = 0.5 * RHO * V * V; cl_req = W_N / (q * S_REF)
    cl, cd, cm = sweep(wing, V) if V != 15.0 else (cl15, cd15, cm15)
    a_req = crossing(ALPHAS, cl, cl_req)
    d = dict(q_Pa=q, CL_required=cl_req, Re_MAC=RHO * V * C_REF / float(ATM.dynamic_viscosity()), alpha_required_deg=a_req)
    if a_req is None:
        d["note"] = "CL required is above the max CL of the model sweep (%.3f): not reachable in this model." % cl.max()
    else:
        CD = float(np.interp(a_req, ALPHAS, cd)); D = q * S_REF * CD
        d.update(CD=CD, LD=cl_req / CD, drag_N=D, aero_power_W=D * V,
                 Cm_at_required_CL={str(f): float(np.interp(a_req, ALPHAS, cm[f])) for f in CG_FRACS})
    d["trim"] = {}
    for f in CG_FRACS:
        a_t = crossing(ALPHAS, cm[f]);
        d["trim"][str(f)] = dict(alpha_trim_deg=a_t, CL_at_trim=None if a_t is None else float(np.interp(a_t, ALPHAS, cl)),
                                 dCm_dalpha_per_deg=float(np.polyfit(ALPHAS[lin], cm[f][lin], 1)[0]))
    flight["%g" % V] = d
res["flight"] = flight

# ---------------- sensitivity: per-station thickness instead of one uniform airfoil --------------------------------------
wing_b = build_wing(True)
clb, cdb, cmb = sweep(wing_b, 15.0)
a_req15 = flight["15"]["alpha_required_deg"]; cl_req15 = flight["15"]["CL_required"]
a_b = crossing(ALPHAS, clb, cl_req15)
res["sensitivity_per_station_thickness_15ms"] = dict(alpha_required_deg=a_b, CD=None if a_b is None else float(np.interp(a_b, ALPHAS, cdb)),
                                                     CD_baseline=flight["15"]["CD"], note="per-station t/c from the mesh (rim-contaminated fan stations use the outboard median)")
json.dump(res, open(os.path.join(OUT, "aero_results.json"), "w"), indent=2)
with open(os.path.join(OUT, "alpha_sweep.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["alpha_deg", "CL", "CD", "L_over_D", "Cm_cg35", "Cm_cg40", "Cm_cg45"])
    for i, a in enumerate(ALPHAS): w.writerow([a, round(cl15[i], 5), round(cd15[i], 5), round(cl15[i] / cd15[i], 3)] + [round(cm15[ff][i], 5) for ff in CG_FRACS])
with open(os.path.join(OUT, "flight_points.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["V_mps", "CL_required", "alpha_required_deg", "CD", "L_over_D", "drag_N", "aero_power_W"])
    for V, d in flight.items(): w.writerow([V, d["CL_required"], d.get("alpha_required_deg"), d.get("CD"), d.get("LD"), d.get("drag_N"), d.get("aero_power_W")])

# ---------------- plots -------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(2, 2, figsize=(13, 9))
ax[0, 0].plot(ALPHAS, cl15, "b-o", ms=3, label="AeroBuildup (NeuralFoil sections)")
alv = np.array([0, 2, 4, 6, 8.0]); ax[0, 0].plot(alv, [vlm_case(wing, x_cg[0.40], a, 8, 8)[0] for a in alv], "r--s", ms=3, label="VLM 8x8")
for V, d in flight.items(): ax[0, 0].axhline(d["CL_required"], ls=":", c="gray"); ax[0, 0].text(-3.8, d["CL_required"] + 0.02, "CL req %s m/s (420 g ASSUMED)" % V, fontsize=8)
ax[0, 0].set_xlabel("alpha [deg]"); ax[0, 0].set_ylabel("CL"); ax[0, 0].legend(); ax[0, 0].grid(alpha=.3); ax[0, 0].set_title("Lift curve, 15 m/s (post-peak points = section roll-over, not a stall prediction)")
ax[0, 1].plot(ALPHAS, cl15 / cd15, "g-o", ms=3); ax[0, 1].set_xlabel("alpha [deg]"); ax[0, 1].set_ylabel("L/D"); ax[0, 1].grid(alpha=.3); ax[0, 1].set_title("L/D vs alpha (wing only, 15 m/s)")
ax[1, 0].plot(cd15, cl15, "m-o", ms=3); ax[1, 0].set_xlabel("CD"); ax[1, 0].set_ylabel("CL"); ax[1, 0].grid(alpha=.3); ax[1, 0].set_title("Drag polar (wing only)")
for f, c in zip(CG_FRACS, ("tab:green", "tab:orange", "tab:red")):
    ax[1, 1].plot(ALPHAS, cm15[f], "-o", ms=3, c=c, label="CG %d%% root chord (x=%.1f mm): SM VLM %+.1f%% / AB %+.1f%% MAC" % (100 * f, 1000 * x_cg[f], *[res["static_margin_pct_MAC"][str(f)][k] for k in ("VLM", "AeroBuildup")]))
ax[1, 1].axhline(0, c="k", lw=.8); ax[1, 1].set_xlabel("alpha [deg]"); ax[1, 1].set_ylabel("Cm (nose-up +)"); ax[1, 1].legend(fontsize=8); ax[1, 1].grid(alpha=.3)
ax[1, 1].set_title("Pitching moment about CG (negative slope = statically stable)")
fig.suptitle("v0_nofin wing only | fan openings, rims, propwash, boom/motor/prop NOT modelled | 600 mm span & 420 g are ASSUMPTIONS | pre-test estimate", fontsize=10)
plt.tight_layout(rect=[0, 0, 1, 0.96]); plt.savefig(os.path.join(OUT, "aero_summary.png"), dpi=120)
print(json.dumps({k: res[k] for k in ("geometry", "AeroBuildup_NP", "static_margin_pct_MAC", "static_margin_verdict", "sensitivity_per_station_thickness_15ms")}, indent=1))
print(json.dumps(res["flight"], indent=1))
