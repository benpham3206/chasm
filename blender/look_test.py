"""Look A/B tests -> blender/tmp/look_*.png. Not a deliverable.

    blender -b --factory-startup --python blender/look_test.py -- frost|caps

frost: 3 variants of frost_acrylic on a corner close-up of the L half.
caps: 3 variants of abs_clear_frosted (+legend) on a few caps.
"""
import bpy, json, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_scene as bs

which = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "frost"

D = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
ctx = bs.build(D)
bs.set_pose("flat", ctx=ctx)

s = bpy.context.scene
s.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'CUDA'
s.cycles.device = 'GPU'
s.render.resolution_x = 420
s.render.resolution_y = 420
s.render.resolution_percentage = 100
s.cycles.samples = 96
s.cycles.use_denoising = True
for k, v in dict(max_bounces=32, transmission_bounces=24, volume_bounces=0,
                 diffuse_bounces=4, glossy_bounces=6,
                 transparent_max_bounces=24, blur_glossy=1.0).items():
    setattr(s.cycles, k, v)
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Base Contrast'
s.view_settings.exposure = -0.4

cam_data = bpy.data.cameras.new("look")
cam = bpy.data.objects.new("look", cam_data)
s.collection.objects.link(cam)
s.camera = cam
cam_data.dof.use_dof = False

# hide R + Hub for clean reads
ctx["colls"]["R"].hide_render = True
ctx["colls"]["Hub"].hide_render = True


def bsdf(mat):
    return mat.node_tree.nodes["Principled BSDF"]


def vol(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'VOLUME_SCATTER':
            return n
    return None


if which == "frost":
    # inner-edge frame band + caps + gull of the L half
    cam.location = (-0.06, -0.10, 0.105)
    tgt = Vector((-0.085, -0.005, 0.012))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 55
    cur = D["materials"]["frost_acrylic"]
    variants = [
        ("A_cur",  dict(base=cur["base"], tr=cur["transmission"],
                        rough=cur["roughness"], vol=cur["volume_scatter_density_per_m"])),
        ("B_thin", dict(base=[0.88, 0.89, 0.90], tr=0.9, rough=0.42, vol=10)),
        ("C_clear", dict(base=[0.85, 0.86, 0.88], tr=0.95, rough=0.35, vol=4)),
    ]
    m = bpy.data.materials["frost_acrylic"]
    for tag, v in variants:
        bsdf(m).inputs["Base Color"].default_value = (*v["base"], 1)
        bsdf(m).inputs["Transmission Weight"].default_value = v["tr"]
        bsdf(m).inputs["Roughness"].default_value = v["rough"]
        vol(m).inputs["Density"].default_value = v["vol"]
        s.render.filepath = os.path.join(HERE, "tmp", f"look_frost_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("[look]", tag)
elif which == "caps":
    # a few caps: G (L26), adjacent alphas, and a wide cap
    cam.location = (-0.14, -0.11, 0.13)
    tgt = Vector((-0.155, -0.015, 0.024))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 65
    cur = D["materials"][D["keycap"]["material"]]
    variants = [
        ("A_cur",  dict(base=cur["base"], tr=1.0, rough=cur["roughness"],
                        vol=cur.get("volume_scatter_density_per_m", 0))),
        ("B_soft", dict(base=[0.9, 0.9, 0.91], tr=0.85, rough=0.3, vol=8)),
        ("C_glass", dict(base=[0.82, 0.84, 0.87], tr=0.95, rough=0.18, vol=0)),
    ]
    m = bpy.data.materials["abs_clear_frosted"]
    for tag, v in variants:
        bsdf(m).inputs["Base Color"].default_value = (*v["base"], 1)
        bsdf(m).inputs["Transmission Weight"].default_value = v["tr"]
        bsdf(m).inputs["Roughness"].default_value = v["rough"]
        vn = vol(m)
        if vn:
            vn.inputs["Density"].default_value = v["vol"]
        s.render.filepath = os.path.join(HERE, "tmp", f"look_caps_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("[look]", tag)
