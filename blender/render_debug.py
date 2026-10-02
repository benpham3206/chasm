"""Debug views -> blender/tmp/. Not a deliverable.

    blender -b --factory-startup --python blender/render_debug.py -- <view>

views: gull (top-down seam macro, together pose), cap (single caps close),
       internals (top-down of L half with shell hidden), side (flat profile)
"""
import bpy, json, os, sys, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_scene as bs

view = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "gull"

D = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
ctx = bs.build(D)

s = bpy.context.scene
s.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'CUDA'
s.cycles.device = 'GPU'
s.render.resolution_x = 700
s.render.resolution_y = 700
s.render.resolution_percentage = 100
s.cycles.samples = 64
s.cycles.use_denoising = True
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Base Contrast'
s.render.image_settings.file_format = 'PNG'

cam_data = bpy.data.cameras.new("dbg")
cam = bpy.data.objects.new("dbg", cam_data)
s.collection.objects.link(cam)
s.camera = cam

if view == "gull":
    bs.set_pose("together", ctx=ctx)
    cam.location = (0.0, 0.0, 0.13)
    cam.rotation_euler = (0, 0, 0)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 0.075
elif view == "cap":
    bs.set_pose("flat", ctx=ctx)
    # a few L caps: macro keys + alphas area
    cam.location = (-0.10, -0.06, 0.12)
    cam.rotation_euler = (Vector((-0.11, 0.0, 0.028)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 60
    cam_data.dof.use_dof = False
elif view == "internals":
    bs.set_pose("flat", ctx=ctx)
    for n in ("L_shell", "L_plate"):
        bpy.data.objects[n].hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith("L_") and ("_cap" in o.name or "_leg" in o.name):
            o.hide_render = True
    cam.location = (-0.13, 0.0, 0.30)
    cam.rotation_euler = (0, 0, 0)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 0.24
elif view == "side":
    bs.set_pose("flat", ctx=ctx)
    cam.location = (0.0, -0.5, 0.05)
    cam.rotation_euler = (Vector((0, 0, 0.02)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 80
elif view == "hub":
    bs.set_pose("flat", ctx=ctx)
    cam.location = (0.04, 0.16, 0.10)
    cam.rotation_euler = (Vector((0.013, 0.105, 0.014)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 80
elif view == "tent":
    bs.set_pose("tented", ctx=ctx)
    cam.location = (-0.55, -0.35, 0.25)
    cam.rotation_euler = (Vector((-0.12, 0.0, 0.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 60

s.render.filepath = os.path.join(HERE, "tmp", f"dbg_{view}.png")
bpy.ops.render.render(write_still=True)
print("[dbg]", s.render.filepath)
