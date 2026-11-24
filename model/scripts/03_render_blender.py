"""Headless Blender 3.6 renders of an STL/GLB (mm). usage: blender -b -P 03_render_blender.py -- model outdir prefix
Frame (v0): nose -X, tail +X, span Y, up Z. Same cameras for every model so before/after are comparable."""
import bpy, sys, os
from mathutils import Vector

path, outdir, prefix = sys.argv[sys.argv.index("--") + 1:][:3]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
if path.lower().endswith(".stl"):
    bpy.ops.wm.stl_import(filepath=path)
else:
    bpy.ops.import_scene.gltf(filepath=path)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
ctr = (lo + hi) / 2
for o in objs:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x, sc.render.resolution_y = 1000, 700
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "SINGLE"
sc.display.shading.single_color = (0.78, 0.78, 0.80)
sc.display.shading.show_cavity = True
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.10, 0.11, 0.13)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.clip_end = 5000

TAIL = Vector((130.0, 0.0, 40.0))     # mm, v0_scaled frame
views = {  # name: (target, direction camera->outward, ortho_scale_mm)
    "top":        (ctr, (0.0, 0.02, 1.0), 680),
    "side":       (ctr, (0.0, 1.0, 0.0), 420),
    "rear":       (ctr, (1.0, 0.0, 0.0), 680),
    "iso":        (ctr, (0.8, -1.0, 0.7), 640),
    "tail_side":  (TAIL, (0.0, 1.0, 0.0), 150),
    "tail_rear":  (TAIL, (1.0, 0.0, 0.0), 120),
    "tail_top":   (TAIL, (0.0, 0.02, 1.0), 150),
    "tail_34":    (TAIL, (0.8, 0.8, 0.5), 160),
}
for name, (tgt, d, scale) in views.items():
    d = Vector(d).normalized()
    cam.data.ortho_scale = scale
    cam.location = tgt + d * 1500
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(outdir, f"{prefix}_{name}.png")
    bpy.ops.render.render(write_still=True)
