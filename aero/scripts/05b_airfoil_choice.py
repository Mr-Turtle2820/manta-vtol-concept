"""Compare classic reflex flying-wing airfoils, as-is and thickness-scaled (camber line preserved) to the mesh t/c, with NeuralFoil.
ASSUMPTION: the mesh has no real airfoil; the choice below is a modelling decision, not a measurement."""
import os, json, numpy as np, aerosandbox as asb, warnings
warnings.filterwarnings("ignore")
WORK = r"E:\Sewa_first\manta\v0_work"
S = json.load(open(os.path.join(WORK, "aero", "wing_stations.json")))
tc_mesh = float(np.median([s["t_over_c"] for s in S["stations"] if 140 <= s["y"] < 290]))
Re = 1.225 * 15.0 * (S["MAC_mm"] / 1000) / 1.81e-5
def thickness_scaled(af, k, n=80):
    xs = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
    u = np.array([float(af.local_thickness(x)) for x in xs]); cam = np.array([float(af.local_camber(x)) for x in xs])
    up = np.c_[xs, cam + k * u / 2]; lo = np.c_[xs, cam - k * u / 2]
    coords = np.vstack([up[::-1], lo[1:]])
    return asb.Airfoil(name=af.name + "_t%.0f" % (100 * k * af.max_thickness()), coordinates=coords)
rows = []
alphas = np.arange(-4, 13, 1.0)
def metrics(af):
    a = af.get_aero_from_neuralfoil(alpha=alphas, Re=Re, model_size="xlarge")
    cl, cm, cd = np.array(a["CL"]), np.array(a["CM"]), np.array(a["CD"])
    i35 = int(np.argmin(np.abs(cl - 0.35))); imax = int(np.argmax(cl / cd))
    return dict(CL_at_pick=float(cl[i35]), CM_at_CL035=float(cm[i35]), CD_at_CL035=float(cd[i35]), LD_at_CL035=float(cl[i35] / cd[i35]),
                LDmax=float((cl / cd)[imax]), alpha_LDmax=float(alphas[imax]), CLmax_in_sweep=float(cl.max()),
                CM_slope_per_deg=float(np.polyfit(alphas[(alphas >= 0) & (alphas <= 8)], cm[(alphas >= 0) & (alphas <= 8)], 1)[0]))
for nm in ["mh45", "mh49", "mh60", "mh61", "mh62", "e186", "e184", "e180", "e182", "eh1070", "naca4412", "naca0012"]:
    try:
        af = asb.Airfoil(name=nm); t0 = float(af.max_thickness())
    except Exception as e:
        continue
    for k in (1.0, tc_mesh / t0):
        try:
            a2 = af if k == 1.0 else thickness_scaled(af, k)
            r = dict(name=a2.name, base=nm, t_over_c=float(a2.max_thickness()), scale_k=float(k), **metrics(a2)); rows.append(r)
        except Exception as e:
            print("skip", nm, k, e)
print("mesh outboard t/c %.3f  Re %.0f" % (tc_mesh, Re))
print("%-14s %6s %5s %7s %8s %7s %7s %6s" % ("airfoil", "t/c", "k", "CL", "CM@CL.35", "L/D@.35", "L/Dmax", "dCM/da"))
for r in rows: print("%-14s %6.3f %5.2f %7.2f %8.4f %7.1f %7.1f %6.4f" % (r["name"], r["t_over_c"], r["scale_k"], r["CL_at_pick"], r["CM_at_CL035"], r["LD_at_CL035"], r["LDmax"], r["CM_slope_per_deg"]))
json.dump(dict(tc_mesh=tc_mesh, Re=Re, rows=rows), open(os.path.join(WORK, "aero", "airfoil_choice.json"), "w"), indent=1)
