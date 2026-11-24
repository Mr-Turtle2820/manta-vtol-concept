"""Screen the AeroSandbox/UIUC airfoil database for tailless-wing candidates near the mesh's measured thickness.
Screen: thickness within a window around the mesh t/c, camber line reflexed at the TE, then NeuralFoil Cm at CL~0.35 (Re from 15 m/s, MAC 0.1257 m).
All numbers computed here. The choice itself is an ASSUMPTION (the mesh has no real airfoil)."""
import os, json, glob, numpy as np, aerosandbox as asb, aerosandbox.numpy as anp, warnings
warnings.filterwarnings("ignore")
WORK = r"E:\Sewa_first\manta\v0_work"
st = json.load(open(os.path.join(WORK, "aero", "wing_stations.json")))
tc_out = [s["t_over_c"] for s in st["stations"] if s["y"] >= 140 and s["y"] < 290]     # outboard of the fans, before the tip
tc_mesh = float(np.median(tc_out)); print("mesh outboard t/c (median of stations y=140..266):", round(tc_mesh, 4), "from", [round(x, 3) for x in tc_out])
Re = 1.225 * 15.0 * (st["MAC_mm"] / 1000) / 1.81e-5
print("Re at 15 m/s on the extracted MAC: %.0f" % Re)
import aerosandbox, pathlib
root = pathlib.Path(aerosandbox.__file__).parent
cands = [p for p in root.rglob("*.dat")]
print("n .dat files:", len(cands), "e.g.", [c.name for c in cands[:3]], "dir", cands[0].parent if cands else None)
rows = []
for p in cands:
    name = p.stem
    try:
        af = asb.Airfoil(name=name)
        t = float(af.max_thickness()); xc = np.linspace(0.05, 0.95, 19)
        cam = np.array([float(af.local_camber(x)) for x in xc]); 
        if not (0.10 <= t <= 0.20): continue
        reflex = cam[-3] < cam[np.argmax(cam)] - 0.0  # placeholder
        te_slope = float(cam[-1] - cam[-4])            # camber-line slope near TE: <0 = reflexed (TE camber falls back toward/below chord)
        if not (np.nanmax(cam) > 0.005 and te_slope < 0 and cam[-1] < 0.5 * np.nanmax(cam)): continue
        a = asb.NeuralFoil if False else None
        aero = af.get_aero_from_neuralfoil(alpha=np.array([0.0, 2.0, 4.0, 6.0]), Re=Re, model_size="large")
        i = int(np.argmin(np.abs(aero["CL"] - 0.35)))
        rows.append((name, t, float(np.nanmax(cam)), te_slope, float(aero["CL"][i]), float(aero["CM"][i]), float(aero["CD"][i])))
    except Exception as e:
        continue
rows.sort(key=lambda r: (abs(r[1] - tc_mesh), -r[5]))
print("%-12s %6s %7s %8s %6s %8s %8s" % ("name", "t/c", "camber", "TEslope", "CL", "CM", "CD"))
for r in rows[:25]: print("%-12s %6.3f %7.3f %8.3f %6.2f %8.4f %8.4f" % r)
json.dump(dict(tc_mesh=tc_mesh, Re=Re, candidates=rows[:40]), open(os.path.join(WORK, "aero", "airfoil_scan.json"), "w"), indent=1)
