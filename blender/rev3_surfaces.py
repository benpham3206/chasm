"""Real-scale CC0 material maps and fine physical surface normals."""
import math
import os
import bpy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def texture(nt, path, vector, color=False):
    node=nt.nodes.new('ShaderNodeTexImage')
    node.image=bpy.data.images.load(os.path.join(ROOT,path),check_existing=True)
    node.image.colorspace_settings.name='sRGB' if color else 'Non-Color'
    node.extension='REPEAT'
    nt.links.new(vector,node.inputs['Vector'])
    return node

def coordinates(nt, cfg, world=False):
    coord=nt.nodes.new('ShaderNodeNewGeometry' if world else 'ShaderNodeTexCoord')
    mapping=nt.nodes.new('ShaderNodeMapping')
    tile=cfg['tile_mm']
    mapping.inputs['Scale'].default_value=(1000/tile[0],1000/tile[1],1000/tile[0])
    mapping.inputs['Rotation'].default_value[2]=math.radians(cfg.get('rotation_deg',0))
    nt.links.new(coord.outputs['Position' if world else 'Object'],mapping.inputs['Vector'])
    return mapping.outputs['Vector']

def micro(mat,cfg):
    nt=mat.node_tree;p=nt.nodes.get('Principled BSDF')
    coord=nt.nodes.new('ShaderNodeTexCoord')
    noise=nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=cfg['scale_per_m']
    noise.inputs['Detail'].default_value=2
    if cfg.get('grain_stretch'):
        stretch=nt.nodes.new('ShaderNodeVectorMath')
        stretch.operation='MULTIPLY'
        stretch.inputs[1].default_value=cfg['grain_stretch']
        nt.links.new(coord.outputs['Object'],stretch.inputs[0])
        nt.links.new(stretch.outputs[0],noise.inputs['Vector'])
    else:
        nt.links.new(coord.outputs['Object'],noise.inputs['Vector'])
    bump=nt.nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value=cfg['bump_mm']*.001
    bump.inputs['Strength'].default_value=cfg['strength']
    nt.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    rough=nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value=cfg['roughness_range'][0]
    rough.inputs['To Max'].default_value=cfg['roughness_range'][1]
    nt.links.new(noise.outputs['Fac'],rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'],p.inputs['Roughness'])
    vector=coordinates(nt,cfg)
    if cfg.get('normal'):
        img=texture(nt,cfg['normal'],vector)
        norm=nt.nodes.new('ShaderNodeNormalMap')
        norm.inputs['Strength'].default_value=cfg.get('normal_strength',.2)
        nt.links.new(img.outputs['Color'],norm.inputs['Color'])
        nt.links.new(norm.outputs['Normal'],bump.inputs['Normal'])
    if cfg.get('roughness'):
        img=texture(nt,cfg['roughness'],vector)
        nt.links.new(img.outputs['Color'],rough.inputs['Value'])
    if cfg.get('anisotropic') is not None:
        p.inputs['Anisotropic'].default_value=cfg['anisotropic']

def apply(D,ctx):
    for name,spec in D['materials'].items():
        if 'micro' in spec:
            cfg=dict(spec['micro'])
            if 'anisotropic' in spec:cfg['anisotropic']=spec['anisotropic']
            micro(ctx['mats'][name],cfg)
