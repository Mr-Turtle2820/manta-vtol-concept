"""Step 2: remove the vertical fin only (boolean difference), verify, export STL + GLB.

Geometry facts (all read off the mesh sections in 00b/00c/00d, original Meshy units):
  - x < ~73.5: the fin plate floats above the boom with an empty gap (boom top <= 19.9, fin lower edge >= 22.18 at x=66..73).
    -> cutter A: box x in [50, 74], |y| <= 8, z >= Z_GAP (inside that gap). Nothing but fin is above it there.
  - x in [74, 84.5]: the rear housing is a "gourd" (lower lobe + upper lobe) with the fin's thin ridge running along its top.
    -> cutter B: prism over |y| <= Y_B whose lower boundary follows the housing's own top height at |y| = Y_B
       (just outside the ridge base), i.e. the ridge is cut flush with the shoulder.
The cutters are built in original units and scaled by K (v0_scaled.stl is the original x K).
"""
import json, os, numpy as np, trimesh
from shapely.geometry import Polygon

WORK = r"E:\Sewa_first\manta\v0_work"
SRC = r"E:\Sewa_first\manta\meshy\v0\v0_silent_manta_remesh_quad.stl"
orig = trimesh.load(SRC)
m = trimesh.load(os.path.join(WORK, "v0_scaled.stl"))
K = json.load(open(os.path.join(WORK, "logs", "01_audit.json")))["scale_factor_to_600mm_span"]

X_A0, X_A1, Z_GAP = 50.0, 74.0, 21.0
X_B0, X_B1, Y_B = 74.0, 83.5, 3.2
X_PROFILE_END = 83.0   # beyond this x the section at |y|=3.2 is the propeller hub (z~17), not the housing: do not follow it

# housing shoulder height along x at |y| = Y_B (take the lower of the +y / -y sections so we never cut below material)
xs = np.arange(X_B0, X_B1 + 0.01, 0.5)
def top_profile(y):
    s = orig.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    pts = []
    for e in s.entities:
        p = s.vertices[e.points]
        for a, b in zip(p[:-1], p[1:]):
            pts.append((a, b))
    out = []
    for x in xs:
        zs = [a[2] + (b[2] - a[2]) * (x - a[0]) / (b[0] - a[0]) for a, b in pts
              if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]]
        out.append(max(zs) if zs else np.nan)
    return np.array(out)
zt = np.minimum(top_profile(+Y_B), top_profile(-Y_B))
ok = ~np.isnan(zt)
keep = ok & (xs <= X_PROFILE_END)
xs_b, zt_b = xs[keep], zt[keep]
xs_b = np.append(xs_b, X_B1); zt_b = np.append(zt_b, zt_b[-1])   # flat to the housing's rear face; only material above it is cut
print("shoulder profile (x, z_top at |y|=%.1f):" % Y_B, [(round(float(a), 1), round(float(b), 2)) for a, b in zip(xs_b, zt_b)])

def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[(x1 - x0), (y1 - y0), (z1 - z0)])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]); return b
cutA = box(X_A0, X_A1, -8, 8, Z_GAP, 80)
poly = Polygon([(float(x), float(z)) for x, z in zip(xs_b, zt_b)] + [(float(xs_b[-1]), 80.0), (float(xs_b[0]), 80.0)])
prism = trimesh.creation.extrude_polygon(poly, height=2 * Y_B)          # extruded along +z of its own frame
# own frame: (x, y_poly=z_world, z_extrude) -> map to world (x, y, z): rotate so poly-y -> world z, extrusion -> world y
R = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)   # poly-y -> world +z, extrusion -> world -y
prism.apply_transform(R); prism.apply_translation([0, Y_B, 0])
cutter = trimesh.boolean.union([cutA, prism], engine="manifold")
cutter.apply_scale(K)
print("cutter watertight:", cutter.is_watertight, "bounds(mm):", np.round(cutter.bounds, 1).tolist())

removed = trimesh.boolean.intersection([m, cutter], engine="manifold")
nofin = trimesh.boolean.difference([m, cutter], engine="manifold")

rem_parts = removed.split(only_watertight=False)
res = dict(
    cutter_params_original_units=dict(X_A=[X_A0, X_A1], Z_GAP=Z_GAP, X_B=[X_B0, X_B1], Y_B=Y_B,
                                      shoulder_profile=[[float(a), float(b)] for a, b in zip(xs_b, zt_b)]),
    scale_K=K,
    removed_n_pieces=len(rem_parts), removed_volume_mm3=float(removed.volume), removed_bounds_mm=removed.bounds.tolist(),
    removed_max_abs_y_mm=float(np.abs(removed.vertices[:, 1]).max()),
    before_volume_mm3=float(m.volume), after_volume_mm3=float(nofin.volume) if nofin.is_watertight else None,
    nofin_watertight=bool(nofin.is_watertight), nofin_winding_consistent=bool(nofin.is_winding_consistent),
    nofin_n_faces=int(len(nofin.faces)), nofin_n_components=len(nofin.split(only_watertight=False)),
    nofin_bounds_mm=nofin.bounds.tolist(), nofin_extents_mm=nofin.extents.tolist(),
)
# nothing may be cut away outside the tail region: compare vertices that were NOT in the cutter's x-y footprint
away = m.vertices[m.vertices[:, 0] < 50.0 * K]
tree = trimesh.proximity.ProximityQuery(nofin)
d = tree.signed_distance(away[:: max(1, len(away) // 4000)])
res["wing_body_check_max_abs_signed_distance_mm"] = float(np.abs(d).max())
json.dump(res, open(os.path.join(WORK, "logs", "02_remove_fin.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in res.items() if k != "cutter_params_original_units"}, indent=1))
nofin.export(os.path.join(WORK, "v0_nofin.stl"))
nofin.export(os.path.join(WORK, "v0_nofin.glb"))
removed.export(os.path.join(WORK, "logs", "02_removed_piece.stl"))
