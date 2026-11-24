import trimesh, numpy as np
m = trimesh.load(r"E:\Sewa_first\manta\meshy\v0\v0_silent_manta_remesh_quad.stl")
print("watertight", m.is_watertight, "winding", m.is_winding_consistent, "faces", len(m.faces), "verts", len(m.vertices))
print("bounds", m.bounds.tolist(), "extents", m.extents.tolist())
print("components", len(m.split(only_watertight=False)))
x0, x1 = m.bounds[:, 0]
print("x-slices: x, y_extent, z_min, z_max, n_vertices")
for x in np.linspace(x0, x1, 25):
    v = m.vertices[np.abs(m.vertices[:, 0] - x) < (x1 - x0) / 50]
    if len(v): print(round(x, 1), round(np.ptp(v[:, 1]), 1), round(v[:, 2].min(), 1), round(v[:, 2].max(), 1), len(v))
