"""Parametric warm oak/window set and dark exploded studio."""
import bpy
import math
import os
from mathutils import Vector
import rev3_surfaces as surfaces


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
    maps=cfg.get('texture',{})
    if maps.get('color'):
        vector=surfaces.coordinates(nt,maps,world=True)
        color=surfaces.texture(nt,maps['color'],vector,color=True)
        nt.links.new(color.outputs['Color'],p.inputs['Base Color'])
        if maps.get('roughness'):
            rough=surfaces.texture(nt,maps['roughness'],vector)
            nt.links.new(rough.outputs['Color'],p.inputs['Roughness'])
        if maps.get('normal'):
            normal=surfaces.texture(nt,maps['normal'],vector)
            normalmap=nt.nodes.new('ShaderNodeNormalMap')
            normalmap.inputs['Strength'].default_value=maps['normal_strength']
            nt.links.new(normal.outputs['Color'],normalmap.inputs['Color'])
            nt.links.new(normalmap.outputs['Normal'],p.inputs['Normal'])
        if maps.get('height'):
            height=surfaces.texture(nt,maps['height'],vector)
            texbump=nt.nodes.new('ShaderNodeBump')
            texbump.inputs['Distance'].default_value=maps['height_mm']*bs.MM
            texbump.inputs['Strength'].default_value=cfg['grain_bump_strength']
            nt.links.new(height.outputs['Color'],texbump.inputs['Height'])
            if maps.get('normal'):nt.links.new(normalmap.outputs['Normal'],texbump.inputs['Normal'])
            nt.links.new(texbump.outputs['Normal'],p.inputs['Normal'])
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
    # Real blockers in the sun's perpendicular plane create sharp blind shadows.
    g=cfg['gobo']
    basis=ob.rotation_euler.to_matrix()
    toward_sun=basis@Vector((0,0,1))
    u=basis@Vector((math.cos(math.radians(g['angle_deg'])),math.sin(math.radians(g['angle_deg'])),0))
    v=toward_sun.cross(u)
    center=Vector(g['target_mm'])*bs.MM+toward_sun*g['distance_mm']*bs.MM
    blocker=bpy.data.materials.new('window_blinds_opaque')
    blocker.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.02,.02,.02,1)
    for i in range(g['count']):
        off=(i-(g['count']-1)/2)*g['pitch_mm']*bs.MM
        corners=[]
        for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            point=center+v*off+u*(a*g['span_mm']*bs.MM/2)+v*(b*g['bar_width_mm']*bs.MM/2)
            corners.append(tuple(point/bs.MM))
        bar=bs.new_obj(f'window_blind_{i}',corners,[(0,1,2,3)],c,blocker)
        bar.visible_camera=False
        bar.visible_glossy=False
        bar.visible_diffuse=False
        bar.visible_transmission=False
    hdri=cfg.get('hdri',{})
    if hdri.get('path'):
        world=bpy.context.scene.world.node_tree
        coord=world.nodes.new('ShaderNodeTexCoord')
        mapping=world.nodes.new('ShaderNodeMapping')
        mapping.inputs['Rotation'].default_value[2]=math.radians(hdri['rotation_deg'])
        tex=world.nodes.new('ShaderNodeTexEnvironment')
        tex.name='desk_interior_hdri'
        tex.image=bpy.data.images.load(os.path.join(surfaces.ROOT,hdri['path']),check_existing=True)
        world.links.new(coord.outputs['Generated'],mapping.inputs['Vector'])
        world.links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
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
        hdri=bpy.context.scene.world.node_tree.nodes.get('desk_interior_hdri')
        if hdri:
            bpy.context.scene.world.node_tree.links.new(hdri.outputs['Color'],bg.inputs['Color'])
        bg.inputs['Strength'].default_value=cfg['hdri']['strength'] if hdri else cfg['world_strength']
    else:
        for link in list(bg.inputs['Color'].links):
            bpy.context.scene.world.node_tree.links.remove(link)
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
