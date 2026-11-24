"""Fan openings / raised rims: vertical ray-cast height profiles (top and bottom skin) through both fan centres. mm, assumed 600 mm span."""
import os, numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
WORK = r"E:\Sewa_first\manta\v0_work"
m = trimesh.load(os.path.join(WORK, "v0_nofin.stl"))
def zline(axis, fixed, lo, hi, step, top=True):
    t = np.arange(lo, hi, step); zz = np.full_like(t, 200.0 if top else -200.0)
    o = np.c_[np.full_like(t, fixed), t, zz] if axis == "y" else np.c_[t, np.full_like(t, fixed), zz]
    d = np.tile([0, 0, -1.0 if top else 1.0], (len(t), 1))
    loc, ir, _ = m.ray.intersects_location(o, d, multiple_hits=False)
    z = np.full(len(t), np.nan); z[ir] = loc[:, 2]; return t, z
fig, axs = plt.subplots(2, 2, figsize=(15, 8))
for col, sgn in enumerate((+1, -1)):
    xc, yc = -61.0, sgn * 84.0
    for top, c in ((True, "k"), (False, "r")):
        t, z = zline("y", xc, yc - 50, yc + 50, 0.5, top); axs[0, col].plot(t, z, c, lw=1, label="top skin" if top else "bottom skin")
        t, z = zline("x", yc, xc - 50, xc + 50, 0.5, top); axs[1, col].plot(t, z, c, lw=1)
    axs[0, col].set_title("fan %+d: along y through x=%.0f (spanwise)" % (sgn, xc)); axs[1, col].set_title("fan %+d: along x through y=%.0f (chordwise)" % (sgn, yc))
    for a in axs[:, col]: a.grid(alpha=.3); a.set_ylabel("z [mm]")
axs[0, 0].legend()
plt.tight_layout(); plt.savefig(os.path.join(WORK, "aero", "fan_profiles_raw.png"), dpi=90)
