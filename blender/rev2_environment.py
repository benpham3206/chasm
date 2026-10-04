"""Parametric warm oak/window set and dark exploded studio."""
import bpy
import math
from mathutils import Vector


def build(D, ctx, bs):
    st = ctx['colls']['Studio']
    c = bpy.data.collections.new('Desk')
    bpy.context.scene.collection.children.link(c)
    ctx['colls']['Desk'] = c
    cfg = D['environments']['desk']
    mat = bpy.data.materials.new('warm_oak')
    nt = mat.node_tree
    p = nt.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value = cfg['roughness']
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    stretch = nt.nodes.new('ShaderNodeVectorMath')
    stretch.operation = 'MULTIPLY'
    stretch.inputs[1].default_value = cfg['grain_stretch']
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = cfg['grain_scale_per_m']
    noise.inputs['Detail'].default_value = 3.0
    noise.inputs['Roughness'].default_value = 0.72
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = (*cfg['grain_dark'],1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*cfg['grain_light'],1)
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = cfg['grain_bump_strength']
    bump.inputs['Distance'].default_value = cfg['grain_bump_mm'] * bs.MM
    nt.links.new(geo.outputs['Position'],stretch.inputs[0])
    nt.links.new(stretch.outputs[0],noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'],ramp.inputs[0])
    nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
    nt.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs[0],p.inputs['Normal'])
    w,h=cfg['size_mm']
    bs.prism('oak_desk',[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)],
             cfg['surface_z_mm']-1,cfg['surface_z_mm'],c,mat)
    sun=bpy.data.lights.new('window_sun','SUN')
    sun.energy=cfg['sun_energy']
    sun.angle=math.radians(cfg['sun_angle_deg'])
    sun.color=cfg['sun_color']
    ob=bpy.data.objects.new('window_sun',sun)
    c.objects.link(ob)
    ob.rotation_euler=tuple(math.radians(a) for a in cfg['sun_rotation_deg'])
    window=bpy.data.lights.new('window_fill','AREA')
    window.shape='RECTANGLE'
    window.size,window.size_y=(s*bs.MM for s in cfg['window_size_mm'])
    window.energy=cfg['window_power_w']
    window.color=cfg['window_color']
    ob=bpy.data.objects.new('window_fill',window)
    c.objects.link(ob)
    ob.location=Vector(cfg['window_pos_mm'])*bs.MM
    ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    glint=bpy.data.lights.new('macro_glint','AREA')
    glint.shape='DISK'
    glint.size=cfg['macro_glint_size_mm']*bs.MM
    glint.energy=cfg['macro_glint_power_w']
    ob=bpy.data.objects.new('macro_glint',glint)
    c.objects.link(ob)
    ob.location=Vector(cfg['macro_glint_pos_mm'])*bs.MM
    aim=Vector(cfg['macro_glint_target_mm'])*bs.MM
    ob.rotation_euler=(aim-ob.location).to_track_quat('-Z','Y').to_euler()
    ob.hide_render=True
    ctx['studio_original_base']=tuple(ctx['mats']['studio_seamless'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)


def select(mode,D,ctx,shot=None):
    desk=mode=='desk'
    ctx['colls']['Desk'].hide_render=not desk
    bpy.data.objects['macro_glint'].hide_render=not (desk and (shot or {}).get('glint'))
    for ob in ctx['colls']['Studio'].objects:
        if ob.name=='plinth': continue
        ob.hide_render=desk
    bg=bpy.context.scene.world.node_tree.nodes.get('Background')
    floor=ctx['mats']['studio_seamless'].node_tree.nodes['Principled BSDF']
    if desk:
        cfg=D['environments']['desk']
        bg.inputs['Color'].default_value=(*cfg['world_color'],1)
        bg.inputs['Strength'].default_value=cfg['world_strength']
    else:
        bg.inputs['Color'].default_value=(0.78,0.82,0.9,1)
        if mode=='dark':
            cfg=D['environments']['dark']
            for name in cfg['hidden_lights']:
                bpy.data.objects[name].hide_render=True
            bg.inputs['Strength'].default_value=cfg['world_strength']
            floor.inputs['Base Color'].default_value=(*cfg['base'],1)
        else:
            bg.inputs['Strength'].default_value=D['studio']['world_strength']
            floor.inputs['Base Color'].default_value=ctx['studio_original_base']
