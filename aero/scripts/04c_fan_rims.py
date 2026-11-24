"""Measure fan opening (rim outer diameter) and raised-rim height, top and bottom, from ray-cast profiles. mm @ assumed 600 mm span.
Rim outer edges = first rise / last drop > JUMP mm along the profile. Rim height = rim extreme within RIM_W of the edge minus the
median skin level in the 4..14 mm band just outside the edge. Hub height = max z of the profile inside the rim minus the same skin level."""
import os, json, numpy as np, trimesh
WORK = r"E:\Sewa_first\manta\v0_work"
m = trimesh.load(os.path.join(WORK, "v0_nofin.stl"))
JUMP, RIM_W = 1.5, 4.0
def zline(axis, fixed, lo, hi, step, top=True):
    t = np.arange(lo, hi, step); zz = np.full_like(t, 200.0 if top else -200.0)
    o = np.c_[np.full_like(t, fixed), t, zz] if axis == "y" else np.c_[t, np.full_like(t, fixed), zz]
    d = np.tile([0, 0, -1.0 if top else 1.0], (len(t), 1))
    loc, ir, _ = m.ray.intersects_location(o, d, multiple_hits=False)
    z = np.full(len(t), np.nan); z[ir] = loc[:, 2]; return t, z
def analyse(t, z, top):
    s = 1.0 if top else -1.0               # work in "height outward from the wing": top -> z, bottom -> -z
    h = s * z; dh = np.diff(h)
    rise = np.where(dh > JUMP)[0]; drop = np.where(dh < -JUMP)[0]
    ia, ib = rise[0], drop[-1] + 1          # outer rim edges (indices into t)
    step = t[1] - t[0]; band = lambda i0, i1: h[max(0, i0):i1]
    skin_a = np.nanmedian(band(ia - int(14 / step), ia - int(4 / step)))
    skin_b = np.nanmedian(band(ib + int(4 / step), ib + int(14 / step)))
    rim_a = np.nanmax(h[ia + 1: ia + 1 + int(RIM_W / step)]); rim_b = np.nanmax(h[ib - int(RIM_W / step): ib])
    hub = np.nanmax(h[ia + int(RIM_W / step): ib - int(RIM_W / step)])
    skin = 0.5 * (skin_a + skin_b)
    return dict(edge_a=float(t[ia]), edge_b=float(t[ib]), outer_diameter=float(t[ib] - t[ia]), centre=float(0.5 * (t[ia] + t[ib])),
                skin_a=float(s * skin_a), skin_b=float(s * skin_b), rim_height_a=float(rim_a - skin_a), rim_height_b=float(rim_b - skin_b),
                hub_height_above_skin=float(hub - skin))
out = {}
for sgn in (+1, -1):
    xc, yc = -61.0, sgn * 84.0
    r = {}
    for top in (True, False):
        side = "top" if top else "bottom"
        ty, zy = zline("y", xc, yc - 50, yc + 50, 0.25, top); tx, zx = zline("x", yc, xc - 50, xc + 50, 0.25, top)
        r[side] = dict(spanwise_line=analyse(ty, zy, top), chordwise_line=analyse(tx, zx, top))
    out["fan_y%+d" % sgn] = r
# summary across all measurements; a line is EXCLUDED if its outer diameter differs >5 % from the median of all lines
# (edge detection locked onto an inner feature, e.g. the spike inside the rim of the +y fan's bottom spanwise line)
lines = [(f, sd, ln, a) for f, v in out.items() for sd, w in v.items() for ln, a in w.items()]
Dmed = float(np.median([a["outer_diameter"] for *_, a in lines]))
for *_, a in lines: a["valid"] = bool(abs(a["outer_diameter"] - Dmed) <= 0.05 * Dmed)
excluded = ["%s/%s/%s" % (f, sd, ln) for f, sd, ln, a in lines if not a["valid"]]
good = [(sd, a) for f, sd, ln, a in lines if a["valid"]]
def collect(key, side=None):
    v = []
    for sd, a in good:
        if side and sd != side: continue
        v += [a[key + "_a"], a[key + "_b"]] if key + "_a" in a else [a[key]]
    return v
st = lambda v: dict(min=float(np.min(v)), max=float(np.max(v)), mean=float(np.mean(v)), n=len(v))
summ = dict(rim_height_top=st(collect("rim_height", "top")), rim_height_bottom=st(collect("rim_height", "bottom")),
            rim_height_all=st(collect("rim_height")), outer_diameter=st(collect("outer_diameter")),
            hub_height_above_skin=st(collect("hub_height_above_skin")), excluded_lines=excluded, diameter_median=Dmed)
summ["fan_centres_xy_mm"] = [[out["fan_y+1"]["top"]["chordwise_line"]["centre"], out["fan_y+1"]["top"]["spanwise_line"]["centre"]],
                             [out["fan_y-1"]["top"]["chordwise_line"]["centre"], out["fan_y-1"]["top"]["spanwise_line"]["centre"]]]
res = dict(note="MODEL RESULT (mesh measurement at ASSUMED 600 mm span; not a true dimension). Rim heights are measured relative to the skin just outside the rim.",
           params=dict(JUMP_mm=JUMP, RIM_W_mm=RIM_W), summary=summ, detail=out)
json.dump(res, open(os.path.join(WORK, "aero", "fan_rims.json"), "w"), indent=2)
print(json.dumps(summ, indent=1))
for k, f in out.items():
    for sd, v in f.items():
        for ln, a in v.items():
            print(k, sd, ln, "D=%.1f centre=%.1f rimA=%.2f rimB=%.2f hub=%.2f skinA=%.1f skinB=%.1f" % (a["outer_diameter"], a["centre"], a["rim_height_a"], a["rim_height_b"], a["hub_height_above_skin"], a["skin_a"], a["skin_b"]))
