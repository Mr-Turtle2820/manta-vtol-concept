import trimesh, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(r"E:\Sewa_first\manta\meshy\v0\v0_silent_manta_remesh_quad.stl")
fig, axs = plt.subplots(1, 2, figsize=(14, 5))
for ax, y0 in zip(axs, (0.0, 3.5)):
    s = m.section(plane_origin=[0, y0, 0], plane_normal=[0, 1, 0])
    for e in s.entities:
        p = s.vertices[e.points]; ax.plot(p[:, 0], p[:, 2], "k-", lw=0.8)
    ax.set_xlim(35, 95); ax.set_ylim(0, 55); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(f"longitudinal section y={y0} (x aft ->, z up)")
plt.tight_layout(); plt.savefig(r"E:\Sewa_first\manta\v0_work\renders\00c_tail_profile.png", dpi=110)
