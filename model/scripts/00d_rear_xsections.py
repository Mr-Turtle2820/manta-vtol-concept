import trimesh, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(r"E:\Sewa_first\manta\meshy\v0\v0_silent_manta_remesh_quad.stl")  # original Meshy units
xs = [62, 66, 70, 73, 75, 77, 79, 81, 83, 85, 86.5, 88]
fig, axs = plt.subplots(3, 4, figsize=(16, 11))
for ax, x in zip(axs.ravel(), xs):
    s = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if s is not None:
        for e in s.entities:
            p = s.vertices[e.points]; ax.plot(p[:, 1], p[:, 2], "k-", lw=0.9)
    ax.set_xlim(-12, 12); ax.set_ylim(5, 32); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(f"x={x} (y horizontal, z up)")
plt.tight_layout(); plt.savefig(r"E:\Sewa_first\manta\v0_work\renders\00d_rear_xsections.png", dpi=80)
