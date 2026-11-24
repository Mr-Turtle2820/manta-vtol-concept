"""Step 1: audit the v0 mesh and scale it uniformly so the span = 600 mm (ASSUMPTION)."""
import json, os, trimesh, numpy as np
SRC = r"E:\Sewa_first\manta\meshy\v0\v0_silent_manta_remesh_quad.stl"
OUT = r"E:\Sewa_first\manta\v0_work"
SPAN_TARGET_MM = 600.0
m = trimesh.load(SRC)
ext = m.extents
a_span, a_up = int(np.argmax(ext)), int(np.argmin(ext))
a_len = ({0, 1, 2} - {a_span, a_up}).pop()
names = "XYZ"
# nose: swept planform is widest aft of mid-length, so the nose is the end at the opposite side
xs = np.linspace(m.bounds[0, a_len], m.bounds[1, a_len], 80)
wid = []
for x in xs:
    v = m.vertices[np.abs(m.vertices[:, a_len] - x) < ext[a_len] / 160]
    wid.append(np.ptp(v[:, a_span]) if len(v) else 0)
x_widest = float(xs[int(np.argmax(wid))])
mid = float(m.bounds.mean(0)[a_len])
nose_sign = -1 if x_widest > mid else +1
k = SPAN_TARGET_MM / ext[a_span]
ms = m.copy(); ms.apply_scale(k)
ms.export(os.path.join(OUT, "v0_scaled.stl"))
res = dict(
    source=SRC, watertight=bool(m.is_watertight), winding_consistent=bool(m.is_winding_consistent),
    n_faces=int(len(m.faces)), n_vertices=int(len(m.vertices)), n_components=len(m.split(only_watertight=False)),
    euler_number=int(m.euler_number),
    bounds_original_units=m.bounds.tolist(), extents_original_units=ext.tolist(),
    axis_span=names[a_span], axis_nose_to_tail=names[a_len], axis_up=names[a_up],
    nose_direction=("+" if nose_sign > 0 else "-") + names[a_len],
    nose_rule="ASSUMPTION: swept wing is widest aft of mid-length; widest section at %s=%.2f, mid=%.2f" % (names[a_len], x_widest, mid),
    scale_factor_to_600mm_span=float(k),
    scaled_extents_mm=ms.extents.tolist(), scaled_bounds_mm=ms.bounds.tolist(),
    scaled_watertight=bool(ms.is_watertight),
    scaled_volume_mm3=float(ms.volume) if ms.is_watertight else None, scaled_surface_area_mm2=float(ms.area),
    scale_note="ASSUMPTION: span set to 600 mm. Meshy meshes have no true scale; no dimension here is measured.",
)
json.dump(res, open(os.path.join(OUT, "logs", "01_audit.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
