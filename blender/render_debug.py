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
elif view == "stick":
    bs.set_pose("flat", ctx=ctx)
    # close-up on the region between L inner-back corner and the hub
    cam.location = (-0.18, -0.15, 0.12)
    cam.rotation_euler = (Vector((-0.05, 0.09, 0.02)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 70
elif view == "oled":
    bs.set_pose("flat", ctx=ctx)
    cam.location = (0.013, 0.02, 0.14)
    cam.rotation_euler = (Vector((0.013, 0.105, 0.016)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 60
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
elif view == "ustowed":
    # underside pose (bottom faces up), camera above the U pocket region
    bs.set_pose("underside", ctx=ctx)
    hp = bpy.data.objects["L_u_frame"].matrix_world.translation
    hp = hp + Vector((0, 0, 0))  # verts are world-ish; use object origin + offset
    tgt = Vector(hp) + Vector((-0.03, 0.0, 0.0))
    cam.location = tgt + Vector((-0.14, -0.16, 0.30))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 55
elif view == "udeployed":
    # tented L, close on the deployed U bar + links from the outer side
    bs.set_pose("tented", ctx=ctx)
    for cn in ("R", "Hub"):
        ctx["colls"][cn].hide_render = True
    # aim at the bar: U-frame origin + its bbox centre in world
    uo = bpy.data.objects["L_u_frame"]
    bpy.context.view_layer.update()
    bb = [uo.matrix_world @ Vector(c) for c in uo.bound_box]
    tgt = sum(bb, Vector()) / 8
    cam.location = tgt + Vector((-0.16, -0.10, 0.05))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 70
elif view == "hub_gull":
    # top-down over the hub's gull inlay (verts are world-ish; use vert mean)
    bs.set_pose("flat", ctx=ctx)
    go = bpy.data.objects["hub_gullR"]
    bpy.context.view_layer.update()
    gv = [go.matrix_world @ v.co for v in go.data.vertices]
    gx = sum(v.x for v in gv) / len(gv)
    gy = sum(v.y for v in gv) / len(gv)
    gz = sum(v.z for v in gv) / len(gv)
    cam.location = (gx, gy, gz + 0.10)
    cam.rotation_euler = (0, 0, 0)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 0.06
elif view == "legends":
    # 1:1-ish crop on G/H + neighbours, flat pose, no DOF
    bs.set_pose("together", ctx=ctx)
    tgt = Vector((0.0, 0.0, 0.022))
    cam.location = tgt + Vector((-0.03, -0.07, 0.12))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 100
elif view == "exploded":
    bs.set_pose("exploded", ctx=ctx)
    cam.location = (0.45, -0.9, 0.5)
    cam.rotation_euler = (Vector((0.0, 0.1, 0.10)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 50

s.render.filepath = os.path.join(HERE, "tmp", f"dbg_{view}.png")
bpy.ops.render.render(write_still=True)
print("[dbg]", s.render.filepath)
