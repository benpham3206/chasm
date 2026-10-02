"""Render the 6 v1 shots. Builds once, re-poses per shot.

    blender -b --factory-startup --python-exit-code 1 --python blender/render_shots.py -- \
        [--shots 1,2,3,4,5,6] [--draft|--final]

Outputs renders/stills/v1/{draft|final}/NN_<name>.png + times.json,
and saves blender/chasm_v1.blend (flat pose) at the end.
"""
import bpy, json, os, sys, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_scene as bs

SHOT_ORDER = ["1_hero", "2_top", "3_plinth", "4_gull", "5_underside", "6_hub"]


def setup_render(D, draft):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type = 'CUDA'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == 'CUDA'
        s.cycles.device = 'GPU'
    except Exception as e:
        print("[warn] CUDA setup failed:", e)
    r = D["render"]
    s.render.resolution_x = r["final_px"][0]
    s.render.resolution_y = r["final_px"][1]
    s.render.resolution_percentage = r["draft_pct"] if draft else 100
    s.cycles.samples = r["draft_samples"] if draft else r["final_samples"]
    s.cycles.use_denoising = True
    try:
        s.cycles.denoiser = r["denoise"]
    except Exception:
        pass
    s.cycles.max_bounces = r["bounces"]["max"]
    s.cycles.transmission_bounces = r["bounces"]["transmission"]
    s.cycles.volume_bounces = r["bounces"]["volume"]
    s.cycles.diffuse_bounces = r["bounces"]["diffuse"]
    s.cycles.glossy_bounces = r["bounces"]["glossy"]
    s.cycles.transparent_max_bounces = r["bounces"]["transparent"]
    s.cycles.blur_glossy = r.get("blur_glossy", 1.0)
    try:
        s.cycles.caustics_reflective = False
        s.cycles.caustics_refractive = False
    except Exception:
        pass
    s.view_settings.view_transform = r["view_transform"]
    s.view_settings.look = r["look"]
    s.view_settings.exposure = r["exposure"]
    s.render.image_settings.file_format = 'PNG'

    # compositor: desaturate + black lift
    ng = bpy.data.node_groups.new("grade", 'CompositorNodeTree')
    ng.interface.new_socket("Image", in_out='INPUT', socket_type='NodeSocketColor')
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers')
    hs = ng.nodes.new('CompositorNodeHueSat')
    hs.inputs["Saturation"].default_value = r["saturation"]
    bc = ng.nodes.new('CompositorNodeBrightContrast')
    bc.inputs["Bright"].default_value = r["black_lift"] * 100.0
    out = ng.nodes.new('NodeGroupOutput')
    ng.links.new(rl.outputs["Image"], hs.inputs["Image"])
    ng.links.new(hs.outputs["Image"], bc.inputs["Image"])
    ng.links.new(bc.outputs["Image"], out.inputs["Image"])
    s.compositing_node_group = ng


def set_camera(shot, D):
    s = bpy.context.scene
    cam = bpy.data.cameras.get("shot_cam")
    if cam is None:
        cam = bpy.data.cameras.new("shot_cam")
        ob = bpy.data.objects.new("shot_cam", cam)
        bpy.context.scene.collection.objects.link(ob)
    else:
        ob = bpy.data.objects["shot_cam"]
    ob.location = tuple(c * bs.MM for c in shot["cam"])
    tgt = shot["target"]
    if isinstance(tgt, str):
        target = Vector(bpy.data.objects[tgt].matrix_world.translation)
    else:
        target = Vector(tuple(t * bs.MM for t in tgt))
    ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()
    if shot.get("ortho_scale_mm"):
        cam.type = 'ORTHO'
        cam.ortho_scale = shot["ortho_scale_mm"] * bs.MM
    else:
        cam.type = 'PERSP'
        cam.lens = shot["lens_mm"]
    s.camera = ob
    # DOF
    if shot.get("fstop"):
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = shot["fstop"]
        foc = bpy.data.objects.get("focus")
        if foc is None:
            foc = bpy.data.objects.new("focus", None)
            bpy.context.scene.collection.objects.link(foc)
        foc.location = (Vector(tuple(t * bs.MM for t in shot["focus_mm"]))
                        if shot.get("focus_mm") else target)
        cam.dof.focus_object = foc
    else:
        cam.dof.use_dof = False


def img_stats(path):
    """clipped% (any channel >= ~250/255 sRGB) + mean sRGB of the top-10% rows."""
    im = bpy.data.images.load(path)
    w, h = im.size
    px = im.pixels[:]
    clip_lin = (250 / 255.0) ** 2.2      # sRGB 250 -> linear
    n = w * h
    clipped = 0
    top_sum = 0.0
    top_n = 0
    top_from = int(h * 0.9)              # pixel rows are bottom-up
    for i in range(n):
        r_, g_, b_ = px[4 * i], px[4 * i + 1], px[4 * i + 2]
        if max(r_, g_, b_) >= clip_lin:
            clipped += 1
        if i // w >= top_from:
            top_sum += 0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_
            top_n += 1
    bpy.data.images.remove(im)
    lin = top_sum / max(top_n, 1)
    srgb = 255.0 * (12.92 * lin if lin <= 0.0031308
                    else 1.055 * lin ** (1 / 2.4) - 0.055)
    return round(100.0 * clipped / n, 2), round(srgb, 1)


def render_shots(which, draft=True):
    D = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    bpy.context.preferences.filepaths.temporary_directory = os.path.join(HERE, "tmp")
    ctx = bs.build(D)
    setup_render(D, draft)
    tag = "draft" if draft else "final"
    outdir = os.path.join(ROOT, "renders", "stills", "v1", tag)
    os.makedirs(outdir, exist_ok=True)
    plinth = bpy.data.objects.get("plinth")
    ph = D["studio"]["plinth_mm"][2]
    times = {}
    for n in which:
        key = SHOT_ORDER[n - 1]
        shot = D["shots"][key]
        support = ph if shot.get("support") == "plinth" else 0.0
        if plinth:
            on = shot.get("support") == "plinth"
            plinth.hide_render = not on
            plinth.hide_set(not on)
            if on and shot.get("plinth_xy"):
                plinth.location.x = shot["plinth_xy"][0] * bs.MM
                plinth.location.y = shot["plinth_xy"][1] * bs.MM
        for hcol in ("L", "R", "Hub"):
            ctx["colls"][hcol].hide_render = hcol in shot.get("hide", [])
        bs.set_pose(shot["pose"], support_z_mm=support, ctx=ctx)
        set_camera(shot, D)
        name = f"{n:02d}_{key.split('_', 1)[1]}"
        bpy.context.scene.render.filepath = os.path.join(outdir, name + ".png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        clip, bg = img_stats(bpy.context.scene.render.filepath)
        times[key] = {"seconds": round(time.time() - t0, 1),
                      "samples": bpy.context.scene.cycles.samples,
                      "res": [bpy.context.scene.render.resolution_x *
                              bpy.context.scene.render.resolution_percentage // 100,
                              bpy.context.scene.render.resolution_y *
                              bpy.context.scene.render.resolution_percentage // 100],
                      "clipped_pct": clip, "bg_mean_srgb": bg}
        print(f"[shot] {name} {times[key]['seconds']}s clip {clip}% bg {bg} -> {outdir}")
    with open(os.path.join(outdir, "times.json"), "w") as fp:
        json.dump(times, fp, indent=1)
    if plinth:
        plinth.hide_render = True
    bs.set_pose("flat", ctx=ctx)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", "chasm_v1.blend"))
    print("[done] blend saved")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    which = [1, 2, 3, 4, 5, 6]
    draft = True
    for i, a in enumerate(argv):
        if a == "--shots":
            which = [int(x) for x in argv[i + 1].split(",")]
        elif a == "--final":
            draft = False
    render_shots(which, draft)
