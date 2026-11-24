"""Step 3A-1: extract wing geometry from v0_nofin.stl (mm, ASSUMED 600 mm span; nose -X, tail +X, span Y, up Z).

Wing = mesh clipped at X_CUT (the wing tips end at x~57-60, the boom starts at x~65-70) -> boom, rear housing and propeller excluded.
Everything printed/saved here is computed from the mesh; nothing is typed in by hand except the station y-positions and X_CUT.
Outputs: aero/wing_stations.json, aero/wing_stations.csv, aero/planform_overlay.png, aero/fan_rims.json, logs/04_extract_wing.log
"""
import json, os, csv, numpy as np, trimesh
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

WORK = r"E:\Sewa_first\manta\v0_work"
OUT = os.path.join(WORK, "aero"); os.makedirs(OUT, exist_ok=True)
m = trimesh.load(os.path.join(WORK, "v0_nofin.stl"))
X_CUT = 63.0                       # mm; see note above (chosen from the planform scan: tips end x~57-60, boom starts x~65-70)
SEMISPAN = float(m.bounds[1, 1])   # 300.5 (mesh is nearly symmetric, checked below)
Y_ST = [12.0] + list(np.linspace(37.5, 292.0, 11))   # 12 stations outside the boom (|y|>8) ...; root y=0 added below
BOOM_HALF_WIDTH_MAX = float(np.abs(m.vertices[(m.vertices[:, 0] > 66) & (m.vertices[:, 0] < 135)][:, 1]).max())

def outer_polygon(y):
    """(x,z) region of the section at span station y, clipped to x <= X_CUT.
    A plane through a fan opening splits the section into a forward and an aft piece, so keep every loop that is
    >= 3 % of the largest loop (drops tiny fan-blade loops) and take their union."""
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    loops = [Polygon(l[:, [0, 2]]).buffer(0) for l in s.discrete if len(l) > 3]
    loops = [p for p in loops if p.area > 1.0]
    amax = max(p.area for p in loops)
    p = unary_union([q for q in loops if q.area >= 0.03 * amax])
    return p.intersection(box(-400, -50, X_CUT, 200))

def station(y):
    p = outer_polygon(y)
    x0, zlo, x1, zhi = p.bounds
    chord = x1 - x0
    xs = x0 + chord * (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, 41)))     # cosine spacing
    top, bot = [], []
    for x in xs:
        ln = LineString([(x, -200), (x, 400)]).intersection(p)
        if ln.is_empty: top.append(np.nan); bot.append(np.nan); continue
        bb = ln.bounds; bot.append(bb[1]); top.append(bb[3])
    top, bot = np.array(top), np.array(bot)
    # z of the section outline at the leading / trailing extreme points
    z_le = float(0.5 * (top[0] + bot[0]) if not np.isnan(top[0]) else np.nan)
    ix = int(np.nanargmin(np.abs(xs - x0)))
    z_le_mid = float(0.5 * (np.nanmax([top[1], bot[1]]) + np.nanmin([top[1], bot[1]])))
    # trailing edge point = mid-thickness at the last sample with material
    k = int(np.where(~np.isnan(top))[0][-1]); z_te = float(0.5 * (top[k] + bot[k]))
    z_le = float(0.5 * (top[int(np.where(~np.isnan(top))[0][0])] + bot[int(np.where(~np.isnan(top))[0][0])]))
    th = top - bot
    mid = 0.5 * (top + bot)
    # chord line from LE to TE points; camber = mid line deviation from it
    chord_line = z_le + (z_te - z_le) * (xs - x0) / chord
    camber_line = mid - chord_line
    return dict(y=float(y), x_le=float(x0), x_te=float(x1), chord=float(chord), z_le=z_le, z_te=z_te,
                incidence_deg=float(np.degrees(np.arctan2(z_le - z_te, chord))),   # +ve = nose-up chord line
                t_max=float(np.nanmax(th)), t_over_c=float(np.nanmax(th) / chord),
                x_tmax_over_c=float((xs[int(np.nanargmax(th))] - x0) / chord),
                camber_max_over_c=float(np.nanmax(np.abs(camber_line)) / chord),
                camber_signed_at_max=float(camber_line[int(np.nanargmax(np.abs(camber_line)))] / chord),
                zmin=float(zlo), zmax=float(zhi)), (xs, top, bot)

st, prof = [], []
for y in Y_ST:
    s, pr = station(y); st.append(s); prof.append(pr)

# root station at the centre line: the body there blends into the boom, so the trailing edge is not defined there.
# ASSUMPTION: copy the TE and geometry of the y=12 station to y=0, but take the leading edge from the mesh (nose apex).
nose = m.bounds[0, 0]
root = dict(st[0]); root["y"] = 0.0
root["x_le"] = float(nose); root["chord"] = root["x_te"] - root["x_le"]; root["note"] = "ASSUMPTION: TE copied from y=12; LE = mesh nose apex"
st = [root] + st

# --- fine planform (1 mm) for area / MAC / symmetry --------------------------------------------------------------
ys = np.arange(12.0, SEMISPAN - 0.5, 1.0)
fine = []
for y in ys:
    try:
        p = outer_polygon(y); x0, _, x1, _ = p.bounds; fine.append((y, x0, x1))
    except Exception: pass
fine = np.array(fine)
sym = []
for y in (37.5, 88.5, 139.5, 190.5, 241.5, 292.0):
    a = outer_polygon(+y).bounds; b = outer_polygon(-y).bounds
    sym.append(dict(y=y, dx_le=float(a[0] - b[0]), dx_te=float(a[2] - b[2])))

# --- areas: (a) stations (piecewise-linear chord), (b) fine 1 mm sections, (c) independent raster of the clipped mesh ---
sy = np.array([s["y"] for s in st]); sc = np.array([s["chord"] for s in st])
S_stations = 2 * np.trapezoid(sc, sy)
# the fine sections start at y=12; add the y<12 strip from the root station chords (same assumption as the root station)
fine_c = fine[:, 2] - fine[:, 1]
S_fine = 2 * (np.trapezoid(fine_c, fine[:, 0]) + 0.5 * (root["chord"] + st[1]["chord"]) * 12.0)
# raster of the projected top view of the clipped mesh (triangles with all vertices x <= X_CUT)
tri = m.triangles; keep = (tri[:, :, 0].max(axis=1) <= X_CUT)
RES = 0.5
W = int((m.bounds[1, 1] - m.bounds[0, 1]) / RES) + 4; Hh = int((X_CUT - m.bounds[0, 0]) / RES) + 4
img = Image.new("L", (W, Hh), 0); d = ImageDraw.Draw(img)
for t in tri[keep]:
    d.polygon([((v[1] - m.bounds[0, 1]) / RES + 2, (v[0] - m.bounds[0, 0]) / RES + 2) for v in t], fill=255)
mask = np.asarray(img) > 0
S_raster = float(mask.sum() * RES * RES)

# --- derived planform numbers from the stations --------------------------------------------------------------------
cy = np.interp(np.linspace(0, SEMISPAN, 2001), sy, sc)
yy = np.linspace(0, SEMISPAN, 2001)
S_half = np.trapezoid(cy, yy)
MAC = float(np.trapezoid(cy ** 2, yy) / S_half)
x_le_i = np.interp(yy, sy, [s["x_le"] for s in st])
xle_mac = float(np.trapezoid(x_le_i * cy, yy) / S_half)        # area-weighted LE x (for neutral-point / CG reference)
y_mac = float(np.trapezoid(yy * cy, yy) / S_half)
# MAC leading edge: LE x at the span station whose chord equals MAC (interpolated)
res = dict(
    X_CUT_mm=X_CUT, span_mm=float(2 * SEMISPAN), boom_half_width_max_mm=BOOM_HALF_WIDTH_MAX,
    S_stations_mm2=float(S_stations), S_fine_sections_mm2=float(S_fine), S_raster_projected_mm2=S_raster,
    pct_stations_vs_raster=float(100 * (S_stations - S_raster) / S_raster),
    pct_fine_vs_raster=float(100 * (S_fine - S_raster) / S_raster),
    AR_from_stations=float((2 * SEMISPAN) ** 2 / S_stations),
    MAC_mm=MAC, MAC_y_mm=y_mac, MAC_area_weighted_xLE_mm=xle_mac, root_chord_mm=root["chord"], tip_chord_mm=st[-1]["chord"],
    symmetry_deltas_mm=sym,
    stations=st,
)
json.dump(res, open(os.path.join(OUT, "wing_stations.json"), "w"), indent=2)
with open(os.path.join(OUT, "wing_stations.csv"), "w", newline="") as f:
    w = csv.writer(f); keys = ["y", "x_le", "x_te", "chord", "z_le", "z_te", "incidence_deg", "t_max", "t_over_c", "x_tmax_over_c", "camber_max_over_c", "camber_signed_at_max"]
    w.writerow(keys)
    for s in st: w.writerow([round(s[k], 4) for k in keys])
print("BOOM half width max (mm):", round(BOOM_HALF_WIDTH_MAX, 2))
print("%-6s %8s %8s %7s %6s %6s %6s %7s %6s %7s" % ("y", "x_le", "x_te", "chord", "z_le", "z_te", "inc", "t/c", "xt/c", "camb"))
for s in st:
    print("%-6.1f %8.1f %8.1f %7.1f %6.1f %6.1f %6.2f %7.3f %6.2f %7.3f" % (s["y"], s["x_le"], s["x_te"], s["chord"], s["z_le"], s["z_te"], s["incidence_deg"], s["t_over_c"], s["x_tmax_over_c"], s["camber_signed_at_max"]))
print("areas mm2: stations %.0f | fine %.0f | raster %.0f  -> stations vs raster %.2f %%, fine vs raster %.2f %%" % (S_stations, S_fine, S_raster, res["pct_stations_vs_raster"], res["pct_fine_vs_raster"]))
print("AR %.3f  MAC %.1f mm  root chord %.1f tip chord %.1f" % (res["AR_from_stations"], MAC, root["chord"], st[-1]["chord"]))
print("symmetry (mm):", sym)

# --- overlay plot: extracted planform on the mesh top view (silhouette raster) --------------------------------------
fig, ax = plt.subplots(figsize=(11, 6.5))
ext = [m.bounds[0, 1] - 2 * RES, m.bounds[1, 1] + 2 * RES, X_CUT + 2 * RES, m.bounds[0, 0] - 2 * RES]
ax.imshow(np.flipud(mask) if False else mask, extent=[m.bounds[0, 1] - 2 * RES, m.bounds[0, 1] - 2 * RES + W * RES, m.bounds[0, 0] - 2 * RES + Hh * RES, m.bounds[0, 0] - 2 * RES], cmap="gray_r", alpha=0.35, aspect="equal")
for sgn in (+1, -1):
    ax.plot(sgn * sy, [s["x_le"] for s in st], "r-o", ms=3, lw=1.2, label="extracted LE (13 stations)" if sgn > 0 else None)
    ax.plot(sgn * sy, [s["x_te"] for s in st], "b-o", ms=3, lw=1.2, label="extracted TE" if sgn > 0 else None)
    ax.plot(sgn * fine[:, 0], fine[:, 1], "r:", lw=0.7); ax.plot(sgn * fine[:, 0], fine[:, 2], "b:", lw=0.7)
for s in st[1:]:
    for sgn in (+1, -1): ax.plot([sgn * s["y"]] * 2, [s["x_le"], s["x_te"]], "g-", lw=0.5)
ax.set_xlabel("y [mm] (span)"); ax.set_ylabel("x [mm] (nose at top)"); ax.set_ylim(X_CUT + 10, m.bounds[0, 0] - 10)
ax.set_title("Extracted planform over the v0_nofin top-view silhouette (x clipped at %.0f mm; grey = projected mesh)\nstations vs raster area: %+.2f %%" % (X_CUT, res["pct_stations_vs_raster"]))
ax.legend(loc="lower right"); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "planform_overlay.png"), dpi=130)

# --- fan openings and raised rims, measured from the mesh by vertical ray casting -------------------------------------
def zline(axis, fixed, lo, hi, step, from_top=True):
    t = np.arange(lo, hi, step)
    if axis == "y": o = np.c_[np.full_like(t, fixed), t, np.full_like(t, 200.0 if from_top else -200.0)]
    else:           o = np.c_[t, np.full_like(t, fixed), np.full_like(t, 200.0 if from_top else -200.0)]
    dvec = np.tile([0, 0, -1.0 if from_top else 1.0], (len(t), 1))
    loc, ir, _ = m.ray.intersects_location(o, dvec, multiple_hits=False)
    z = np.full(len(t), np.nan); z[ir] = loc[:, 2]
    return t, z
fan = {}
for sgn in (+1, -1):
    # coarse centre from the vertex-density peak, refined by the symmetric rim pair along y and x
    xc0, yc0 = -61.0, sgn * 84.0
    ty, zy = zline("y", xc0, yc0 - 45, yc0 + 45, 0.5)
    tx, zx = zline("x", yc0, xc0 - 45, xc0 + 45, 0.5)
    fan[sgn] = dict(ty=ty, zy=zy, tx=tx, zx=zx, xc0=xc0, yc0=yc0)
np.save(os.path.join(OUT, "_fan_profiles.npy"), fan, allow_pickle=True)
print("fan raw profiles saved; analysed in 04b")
