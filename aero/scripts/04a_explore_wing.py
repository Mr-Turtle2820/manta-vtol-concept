import trimesh, numpy as np
from scipy import ndimage as ndi
m = trimesh.load(r"E:\Sewa_first\manta\v0_work\v0_nofin.stl")      # mm, nose -X
print("bounds", np.round(m.bounds, 1).tolist())
# 1) planform y-extent vs x (find where the wing ends and the boom starts)
for x in np.arange(-150, 152, 10):
    v = m.vertices[np.abs(m.vertices[:, 0] - x) < 3]
    if len(v): print("x=%6.1f  y_extent=%6.1f  y_min=%7.1f y_max=%7.1f" % (x, np.ptp(v[:, 1]), v[:, 1].min(), v[:, 1].max()))
# 2) fan centres: vertex density peaks (blades are vertex-dense)
H, xe, ye = np.histogram2d(m.vertices[:, 0], m.vertices[:, 1], bins=[np.arange(-160, 160, 6), np.arange(-300, 301, 6)])
Hs = ndi.gaussian_filter(H, 2)
for sgn in (+1, -1):
    sub = Hs.copy(); sub[:, (ye[:-1] * sgn) < 20] = 0
    i, j = np.unravel_index(np.argmax(sub), sub.shape)
    print("fan density peak (sign y=%+d): x=%.0f y=%.0f  count/bin=%.0f" % (sgn, xe[i] + 3, ye[j] + 3, H[i, j]))
# 3) left/right symmetry of the planform
for y in (50, 100, 150, 200, 250, 290):
    out = []
    for s in (+1, -1):
        sec = m.section(plane_origin=[0, s * y, 0], plane_normal=[0, 1, 0])
        v = sec.vertices; v = v[v[:, 0] < 100]
        out.append((v[:, 0].min(), v[:, 0].max(), v[:, 2].min(), v[:, 2].max()))
    print("y=+-%d  +y: xLE %.1f xTE %.1f zmin %.1f zmax %.1f | -y: xLE %.1f xTE %.1f zmin %.1f zmax %.1f" % ((y,) + out[0] + out[1]))
