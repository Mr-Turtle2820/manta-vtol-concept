"""Derived figures from aero_results.json (no new aero runs). Everything here is arithmetic on the saved results."""
import json, os, numpy as np
OUT = r"E:\Sewa_first\manta\v0_work\aero"
r = json.load(open(os.path.join(OUT, "aero_results.json"))); g = r["geometry"]; W = r["assumptions"]["weight_kg"] * r["assumptions"]["g"]
rho, S, C, x0, cr = r["assumptions"]["rho"], g["S_ref_m2"], g["MAC_m"], g["x_root_le_m"], g["root_chord_m"]
f15 = r["flight"]["15"]; cm = f15["Cm_at_required_CL"]
# CG (fraction of root chord) at which Cm = 0 at the required CL, linear interpolation between the 40 % and 45 % results
c40, c45 = cm["0.4"], cm["0.45"]; f0 = 0.40 + 0.05 * (0 - c40) / (c45 - c40)
x_cg0 = x0 + f0 * cr
sm = {k: 100 * (r[k]["x_np_m"] - x_cg0) / C for k in ("AeroBuildup_NP",)}; sm["VLM"] = 100 * (r["VLM"]["res_8x8"]["x_np_m"] - x_cg0) / C
# speed at which the wing alone trims (Cm = 0) at CG 35 / 40 %, from the 15 m/s trim CL (CL_trim is Reynolds-dependent; approximate)
vtrim = {k: float(np.sqrt(2 * W / (rho * S * d["CL_at_trim"]))) for k, d in f15["trim"].items() if d["CL_at_trim"]}
# VLM cross-check of the required alpha at 15 m/s
v = r["VLM"]["res_8x8"]; a_vlm = (f15["CL_required"] - v["CL0"]) / v["CL_alpha_per_deg"]
v5, v12 = r["VLM"]["res_5x5"], r["VLM"]["res_12x10"]
post = dict(
    CG_fraction_root_chord_for_Cm0_at_CLreq_15ms=f0, x_cg_mm=1000 * x_cg0, static_margin_at_that_CG_pct_MAC=sm,
    speed_for_trim_at_CG_mps=vtrim,
    alpha_required_VLM_crosscheck_deg=a_vlm, alpha_required_AeroBuildup_deg=f15["alpha_required_deg"],
    CL_alpha_per_rad=dict(VLM_8x8=v["CL_alpha_per_rad"], AeroBuildup_0_8deg=r["AeroBuildup_15ms"]["CL_alpha_per_deg_fit_0_8"] * 180 / np.pi),
    CL_alpha_disagreement_pct=100 * (r["AeroBuildup_15ms"]["CL_alpha_per_deg_fit_0_8"] * 180 / np.pi / v["CL_alpha_per_rad"] - 1),
    VLM_resolution_spread=dict(NP_x_mm=[1000 * q["x_np_m"] for q in (v5, v, v12)], CL_alpha_per_rad=[q["CL_alpha_per_rad"] for q in (v5, v, v12)], CL0=[q["CL0"] for q in (v5, v, v12)]),
    level_flight_speed_where_AB_peak_CL=float(np.sqrt(2 * W / (rho * S * r["AeroBuildup_15ms"]["max_CL_in_sweep"]))),
    note="the last line is arithmetic on the AeroBuildup section roll-over CL; it is NOT a stall-speed prediction")
json.dump(post, open(os.path.join(OUT, "aero_results_post.json"), "w"), indent=2); print(json.dumps(post, indent=1))
