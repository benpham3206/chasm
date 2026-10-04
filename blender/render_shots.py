"""Render the rev2 draft shots. Builds once, re-poses per shot, auto-fits framing.

    blender -b --factory-startup --python-exit-code 1 --python blender/render_shots.py -- \
        [--shots 1,2,3,4,5,6,6b,7] [--draft|--final]

Per-shot spec in design.json "shots": pose, view {az_deg, el_deg} (az 0 = front
/-y side, + toward +x), lens_mm or ortho:true, fit {subjects [collection names
or name globs] or box_mm [[lo],[hi]], fill}, optional support/hide/fstop/
focus_mm/plinth_xy. The camera aims at the subjects' world bbox centre, the
distance (or ortho_scale) is binary-searched so the larger projected extent ==
fill, then shift_x/y centres the bbox (3 iterations).

Outputs renders/stills/v2/{draft|final}/NN_<name>.png + times.json (merged
after EVERY shot), and saves blender/chasm_v2.blend (flat pose) at the end.
"""
import bpy, json, os, sys, time, math, fnmatch
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_scene as bs
import rev2_environment as env

SHOT_ORDER = ["1_hero", "2_top", "3_plinth", "4_macro_legends",
              "5_macro_detail", "6_hub", "6b_hub_ports", "7_exploded"]

MM = 0.001


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


def subject_pts(shot, ctx):
    """world-space bbox corner points of the fit subjects (metres)."""
    fit = shot["fit"]
    if "box_mm" in fit:
        (x0, y0, z0), (x1, y1, z1) = fit["box_mm"]
        return [Vector((x * MM, y * MM, z * MM))
                for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    pts = []
    for pat in fit["subjects"]:
        objs = []
        if pat in ("L", "R", "Hub"):
            coll = ctx["colls"][pat]
            if coll.hide_render:
                continue
            objs = list(coll.all_objects)
        else:
            for cn in ("L", "R", "Hub", "Studio"):
                for o in ctx["colls"][cn].all_objects:
                    if fnmatch.fnmatch(o.name, pat):
                        objs.append(o)
        for o in objs:
            if o.type != 'MESH' or o.hide_render:
                continue
            for c in o.bound_box:
                pts.append(o.matrix_world @ Vector(c))
    return pts


def proj(pts, s, cam):
    from bpy_extras.object_utils import world_to_camera_view as w2c
    bpy.context.view_layer.update()   # camera matrix_world is stale after moves
    xs = [w2c(s, cam, p).x for p in pts]
    ys = [w2c(s, cam, p).y for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def set_camera(shot, ctx):
    s = bpy.context.scene
    cam = bpy.data.cameras.get("shot_cam")
    if cam is None:
        cam = bpy.data.cameras.new("shot_cam")
        ob = bpy.data.objects.new("shot_cam", cam)
        bpy.context.scene.collection.objects.link(ob)
    else:
        ob = bpy.data.objects["shot_cam"]
    cam.shift_x = cam.shift_y = 0.0
    v = shot["view"]
    az, el = math.radians(v["az_deg"]), math.radians(v["el_deg"])
    d3 = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el),
                 math.sin(el)))
    bpy.context.view_layer.update()
    pts = subject_pts(shot, ctx)
    ctr = Vector(((min(p.x for p in pts) + max(p.x for p in pts)) / 2,
                  (min(p.y for p in pts) + max(p.y for p in pts)) / 2,
                  (min(p.z for p in pts) + max(p.z for p in pts)) / 2))
    fill = shot["fit"]["fill"]

    def aim():
        ob.rotation_euler = (ctr - ob.location).to_track_quat('-Z', 'Y').to_euler()

    dist = None
    if shot.get("ortho"):
        cam.type = 'ORTHO'
        ob.location = ctr + d3 * 3.0
        aim()
        lo, hi = 0.02, 5.0
        for _ in range(30):
            cam.ortho_scale = (lo + hi) / 2
            x0, x1, y0, y1 = proj(pts, s, ob)
            if max(x1 - x0, y1 - y0) > fill:
                lo = cam.ortho_scale
            else:
                hi = cam.ortho_scale
        cam.ortho_scale = (lo + hi) / 2
    else:
        cam.type = 'PERSP'
        cam.lens = shot["lens_mm"]
        lo, hi = 0.05, 8.0
        for _ in range(40):
            d_ = (lo + hi) / 2
            ob.location = ctr + d3 * d_
            aim()
            x0, x1, y0, y1 = proj(pts, s, ob)
            if max(x1 - x0, y1 - y0) > fill:
                lo = d_
            else:
                hi = d_
        dist = (lo + hi) / 2
        ob.location = ctr + d3 * dist
        aim()
    # centre via shift (numeric slope is exact; 2 iterations to converge)
    for _ in range(3):
        x0, x1, y0, y1 = proj(pts, s, ob)
        cx, cy2 = (x0 + x1) / 2, (y0 + y1) / 2
        eps = 0.01
        cam.shift_x = eps
        e1 = proj([ctr], s, ob)[0]
        cam.shift_x = 0.0
        e0 = proj([ctr], s, ob)[0]
        slope = (e1 - e0) / eps                       # du per shift unit
        cam.shift_x = -(cx - 0.5) / slope if abs(slope) > 1e-9 else 0.0
        cam.shift_y = -(cy2 - 0.5) / slope if abs(slope) > 1e-9 else 0.0
    x0, x1, y0, y1 = proj(pts, s, ob)
    # DOF: only shots that ask for it (fstop present)
    if shot.get("fstop"):
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = shot["fstop"]
        foc = bpy.data.objects.get("focus")
        if foc is None:
            foc = bpy.data.objects.new("focus", None)
            bpy.context.scene.collection.objects.link(foc)
        if shot.get("focus_subject"):
            target = bpy.data.objects[shot["focus_subject"]]
            foc.location = target.matrix_world @ Vector((0,0,max(c[2] for c in target.bound_box)))
        else:
            foc.location = (Vector(tuple(t * MM for t in shot["focus_mm"]))
                            if shot.get("focus_mm") else ctr)
        cam.dof.focus_object = foc
    else:
        cam.dof.use_dof = False
    s.camera = ob
    return {"cam_mm": [round(v2 * 1000, 1) for v2 in ob.location],
            "dist_mm": round(dist * 1000, 1) if dist else None,
            "ortho_scale_mm": round(cam.ortho_scale * 1000, 1)
            if cam.type == 'ORTHO' else None,
            "fill": round(max(x1 - x0, y1 - y0), 3),
            "frame": [round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)]}


def plan_pts(names, ctx):
    """world xy points of the subjects' mesh bboxes (metres)."""
    pts = []
    for pat in names:
        if pat == "plinth":
            continue
        if pat in ("L", "R", "Hub"):
            coll = ctx["colls"][pat]
            if coll.hide_render:
                continue
            for o in coll.all_objects:
                if o.type != 'MESH' or o.hide_render:
                    continue
                for c in o.bound_box:
                    pts.append(o.matrix_world @ Vector(c))
        else:
            for cn in ("L", "R", "Hub", "Studio"):
                for o in ctx["colls"][cn].all_objects:
                    if fnmatch.fnmatch(o.name, pat) and o.type == 'MESH':
                        for c in o.bound_box:
                            pts.append(o.matrix_world @ Vector(c))
    return pts


def fit_plinth(shot, ctx):
    """R5: size + centre the plinth under the shot's on-plinth subjects.
    Returns the plinth top height in mm (support z)."""
    plinth = bpy.data.objects["plinth"]
    subj = [p for p in shot["fit"]["subjects"] if p != "plinth"]
    pts = plan_pts(subj, ctx)
    x0 = min(p.x for p in pts); x1 = max(p.x for p in pts)
    y0 = min(p.y for p in pts); y1 = max(p.y for p in pts)
    margin = ctx["design"]["studio"]["plinth_margin_mm"] * MM
    need_w = (x1 - x0) + 2 * margin
    need_d = (y1 - y0) + 2 * margin
    pw, pd, ph = ctx["design"]["studio"]["plinth_mm"]
    plinth.scale = (need_w / (pw * MM), need_d / (pd * MM), 1.0)
    plinth.location.x = (x0 + x1) / 2
    plinth.location.y = (y0 + y1) / 2
    # assert all subject footprint corners are inside the sized plinth
    pcx, pcy = plinth.location.x, plinth.location.y
    for p in pts:
        assert abs(p.x - pcx) <= need_w / 2 + 0.001 and \
               abs(p.y - pcy) <= need_d / 2 + 0.001, \
            "plinth does not cover a subject footprint"
    print(f"[geom] plinth {need_w*1000:.0f}x{need_d*1000:.0f} mm at "
          f"({pcx*1000:.0f},{pcy*1000:.0f})")
    return ph


def stack_sep_check(s, cam_ob, ctx):
    """H3: exploded-view stacks (L / R / Hub) must not overlap in frame;
    pairwise gap >= 3% of frame width."""
    bbs = {}
    for cn in ("L", "R", "Hub"):
        pts = []
        for o in ctx["colls"][cn].all_objects:
            if o.type != 'MESH' or o.hide_render:
                continue
            for c in o.bound_box:
                pts.append(o.matrix_world @ Vector(c))
        x0, x1, y0, y1 = proj(pts, s, cam_ob)
        bbs[cn] = (x0, y0, x1, y1)
    for a in ("L", "R", "Hub"):
        for b in ("L", "R", "Hub"):
            if a >= b:
                continue
            ax0, ay0, ax1, ay1 = bbs[a]
            bx0, by0, bx1, by1 = bbs[b]
            xg = max(ax0 - bx1, bx0 - ax1)
            yg = max(ay0 - by1, by0 - ay1)
            sep = max(xg, yg)
            print(f"[geom] explode sep {a}-{b}: {sep:.3f} "
                  f"(x {xg:.3f}, y {yg:.3f})")
            assert sep >= 0.03, \
                f"exploded stacks {a}/{b} overlap in frame (sep {sep:.3f})"
    return bbs


def img_stats(path):
    """clipped% (any channel >= 250/255) + mean sRGB and R/B means of the
    top-10% rows. bpy Image.pixels of an sRGB PNG are sRGB-encoded 0..1."""
    im = bpy.data.images.load(path)
    w, h = im.size
    px = im.pixels[:]
    n = w * h
    clipped = 0
    top_sum = top_r = top_b = 0.0
    top_n = 0
    top_from = int(h * 0.9)              # pixel rows are bottom-up
    for i in range(n):
        r_, g_, b_ = px[4 * i], px[4 * i + 1], px[4 * i + 2]
        if max(r_, g_, b_) >= 250 / 255.0:
            clipped += 1
        if i // w >= top_from:
            top_sum += 0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_
            top_r += r_
            top_b += b_
            top_n += 1
    bpy.data.images.remove(im)
    tn = max(top_n, 1)
    return (round(100.0 * clipped / n, 3), round(255.0 * top_sum / tn, 1),
            round(255.0 * top_r / tn, 1), round(255.0 * top_b / tn, 1))


def write_times(outdir, times):
    # H8: merge into the existing file so subset --shots runs keep prior entries
    path = os.path.join(outdir, "times.json")
    if os.path.exists(path):
        try:
            old = json.load(open(path))
            old.update(times)
            times = old
        except Exception:
            pass
    with open(path, "w") as fp:
        json.dump(times, fp, indent=1)


def render_shots(which, draft=True):
    D = json.load(open(os.path.join(HERE, "design.json"), encoding="utf-8"))
    bpy.context.preferences.filepaths.temporary_directory = os.path.join(HERE, "tmp")
    ctx = bs.build(D)
    env.build(D, ctx, bs)
    setup_render(D, draft)
    print("[units] scale_length", bpy.context.scene.unit_settings.scale_length,
          bpy.context.scene.unit_settings.length_unit)
    tag = "draft" if draft else "final"
    outdir = os.path.join(ROOT, "renders", "stills", "v2", tag)
    os.makedirs(outdir, exist_ok=True)
    plinth = bpy.data.objects.get("plinth")
    ph = D["studio"]["plinth_mm"][2]
    times = {}
    for n in which:
        key = next(k for k in SHOT_ORDER if k.split("_", 1)[0] == str(n))
        shot = D["shots"][key]
        bpy.context.scene.cycles.samples=shot.get('draft_samples',D['render']['draft_samples']) if draft else D['render']['final_samples']
        env.select(shot.get("environment", "studio"), D, ctx, shot)
        for hcol in ("L", "R", "Hub"):
            ctx["colls"][hcol].hide_render = hcol in shot.get("hide", [])
        bs.set_pose(shot["pose"], ctx=ctx)          # pose first so bbox is real
        support = 0.0
        if plinth:
            on = shot.get("support") == "plinth"
            plinth.hide_render = not on
            plinth.hide_set(not on)
            if on:
                support = fit_plinth(shot, ctx)
                bs.set_pose(shot["pose"], support_z_mm=support, ctx=ctx)
        cam_info = set_camera(shot, ctx)
        # per-shot exposure override (e.g. 06b's distant lit floor)
        bpy.context.scene.view_settings.exposure = \
            shot.get("exposure", D["environments"].get(shot.get("environment"), {}).get("exposure", D["render"]["exposure"]))
        if shot["pose"] == "exploded":
            stack_sep_check(bpy.context.scene, bpy.data.objects["shot_cam"],
                            ctx)
        num = key.split('_', 1)[0]
        name = (f"{int(num):02d}" if num.isdigit() else f"0{num}") + \
               "_" + key.split('_', 1)[1]                     # 6 -> 06_, 6b -> 06b_
        bpy.context.scene.render.filepath = os.path.join(outdir, name + ".png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        clip, bg, bg_r, bg_b = img_stats(bpy.context.scene.render.filepath)
        frame_ok = all(0.04 <= v <= 0.96 for v in cam_info["frame"])
        if key == "1_hero":
            # Rev2: closer full setup with safe outer margin.
            fx0, fy0, fx1, fy1 = cam_info["frame"]
            fw, fh = fx1 - fx0, fy1 - fy0
            assert 0.84 <= fw <= 0.92, f"01 width frac {fw:.3f} out of range"
            assert fh >= 0.40, f"01 height frac {fh:.3f} < 0.40"
        times[key] = {"seconds": round(time.time() - t0, 1),
                      **cam_info, "frame_ok": frame_ok,
                      "samples": bpy.context.scene.cycles.samples,
                      "res": [bpy.context.scene.render.resolution_x *
                              bpy.context.scene.render.resolution_percentage // 100,
                              bpy.context.scene.render.resolution_y *
                              bpy.context.scene.render.resolution_percentage // 100],
                      "clipped_pct": clip, "bg_mean_srgb": bg,
                      "bg_r_srgb": bg_r, "bg_b_srgb": bg_b}
        write_times(outdir, times)
        print(f"[shot] {name} {times[key]['seconds']}s clip {clip}% bg {bg}"
              f" (R{bg_r}/B{bg_b}) frame {cam_info['frame']}"
              f" cam {cam_info['cam_mm']}"
              f"{'' if frame_ok else ' <OUT>'} -> {outdir}", flush=True)
    if plinth:
        plinth.hide_render = True
    bs.set_pose("flat", ctx=ctx)
    env.select("desk", D, ctx)
    for cn in ('L','R','Hub'):
        ctx['colls'][cn].hide_render=False
    set_camera(D['shots']['1_hero'],ctx)
    bpy.context.scene.view_settings.exposure = D['shots']['1_hero'].get('exposure', D['environments']['desk']['exposure'])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", "chasm_v2.blend"))
    print("[done] blend saved")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    which = [1, 2, 3, 4, 5, 6, "6b", 7]
    draft = True
    for i, a in enumerate(argv):
        if a == "--shots":
            which = [int(x) if x.isdigit() else x for x in argv[i + 1].split(",")]
        elif a == "--final":
            draft = False
    render_shots(which, draft)
