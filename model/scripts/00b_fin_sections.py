import trimesh, numpy as np
m = trimesh.load(r"E:\Sewa_first\manta\meshy\v0\v0_silent_manta_remesh_quad.stl")
print("horizontal sections of the tail region (x>40): z, x_min, x_max, y_min, y_max, area")
for z in np.arange(8, 50.1, 2.0):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None: continue
    v = s.vertices[s.vertices[:, 0] > 40]
    if len(v): print(round(z, 1), *[round(float(a), 1) for a in (v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max())])
print("\nvertical sections along the tail: x, z_min, z_max, y_min, y_max")
for x in np.arange(40, 92, 3.0):
    s = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if s is None: continue
    v = s.vertices[np.abs(s.vertices[:, 1]) < 30]
    if len(v): print(round(x, 1), *[round(float(a), 1) for a in (v[:, 2].min(), v[:, 2].max(), v[:, 1].min(), v[:, 1].max())])
