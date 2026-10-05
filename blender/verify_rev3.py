"""Inspect the generated scene before the draft handoff; writes evidence JSON."""
import bpy,bmesh,json,math,os,sys
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import outline as ol
D=json.load(open(os.path.join(HERE,'design.json'),encoding='utf8'))
_,keys=ol.load()
report={'case':{},'keycaps':{},'mount':{},'knobs':[], 'gulls':[]}
for half in 'LR':
    root=bpy.data.objects[half+'_root']
    poly,_,_=ol.outline(D['case']['outline'][half],keys['keys'],half,keys['unit_mm'])
    deck=[root.matrix_world@Vector((x*.001,y*.001,D['case']['height_mm']*.001)) for x,y in poly]
    front_height=min(p.z for p in deck)*1000
    normal=root.matrix_world.to_3x3()@Vector((0,0,1))
    typing=math.degrees(math.acos(normal.normalized().z))
    assert abs(front_height-19.3)<.02,(half,front_height)
    assert abs(typing-8.0)<.02,(half,typing)
    report['case'][half]={'front_deck_above_desk_mm':round(front_height,3),'typing_angle_deg':round(typing,3),
        'PCB_thickness_mm':D['stack']['pcb_z'][1]-D['stack']['pcb_z'][0],
        'plate_top_minus_PCB_top_mm':D['stack']['plate_z'][1]-D['stack']['pcb_z'][1]}
    assert abs(report['case'][half]['PCB_thickness_mm']-1.2)<1e-6
    assert abs(report['case'][half]['plate_top_minus_PCB_top_mm']-5)<1e-6
    springs=[o for o in bpy.data.objects if o.name.startswith(half+'_leaf') and not '_pad' in o.name]
    report['mount'][half]={'metal_leaves':len(springs),'silicone_pads':len([o for o in bpy.data.objects if o.name.startswith(half+'_leaf_pad')])}
    assert len(springs)>=12
    # The assembled leaves must fit within the case outline.
    clear=min(ol.dist_to_poly(poly,(v.co.x*1000,v.co.y*1000)) for o in springs for v in o.data.vertices)
    assert all(ol.point_in(poly,(v.co.x*1000,v.co.y*1000)) for o in springs for v in o.data.vertices),half+' leaf outside case'
    report['mount'][half]['minimum_leaf_to_outline_mm']=round(clear,3)
caps=[o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('_cap')]
seen=set()
for ob in caps:
    if ob.data.name in seen:continue
    seen.add(ob.data.name)
    bm=bmesh.new();bm.from_mesh(ob.data)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    assert nonmanifold==0,(ob.name,nonmanifold)
report['keycaps']['count']=len(caps)
assert len(caps)==len([k for k in keys['keys'] if not k.get('virtual')])
report['keycaps']['closed_outer_profile_meshes_checked']=len(seen)
evaluated_checks={}
dg=bpy.context.evaluated_depsgraph_get()
for cap in caps:
    name=cap.name
    ob=cap.evaluated_get(dg)
    me=ob.to_mesh()
    bm=bmesh.new();bm.from_mesh(me)
    count=sum(not e.is_manifold for e in bm.edges)
    evaluated_checks[name]={'nonmanifold_edges':count,'polygons':len(me.polygons)}
    assert count==0,(name,count)
    assert len(me.polygons)>0,name+' empty clear shell'
    bm.free();ob.to_mesh_clear()
report['keycaps']['evaluated_clear_shells']=evaluated_checks
cores=[o for o in bpy.data.objects if o.name.endswith('_white_core')]
assert len(cores)==len(caps)
for ob in cores:
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges),ob.name
    bm.free()
cfg=D['keycap']['rev2']
assert .6<=cfg['shell_wall_mm']<=1.0
report['keycaps']['physical_clear_skin_mm']=cfg['shell_wall_mm']
report['keycaps']['core_top_recess_mm']=cfg['body_top_recess_mm']
report['keycaps']['core_count']=len(cores)
report['case']['plan']=D['case']['plan']
assert D['case']['plan']['derived']['L']['corner_radius_mm']==D['case']['plan']['derived']['R']['corner_radius_mm']
report['render_bounces']=D['render']['bounces']
report['desk_maps']=D['environments']['desk']['texture']
report['desk_hdri']=D['environments']['desk']['hdri']
rootdir=os.path.dirname(HERE)
for cfg in [D['environments']['desk']['texture'],D['environments']['desk']['hdri']]:
    for key in ['color','roughness','normal','height','path']:
        if cfg.get(key):assert os.path.isfile(os.path.join(rootdir,cfg[key])),cfg[key]

report['keycaps']['hollow_sockets']=len([o for o in bpy.data.objects if o.name.endswith('_mx_socket')])
report['keycaps']['homing_bars']=[o.name for o in bpy.data.objects if o.name.endswith('_homing')]
report['keycaps']['font']=D['keycap']['legend']['font']
report['keycaps']['font_substitute']=True
report['knobs']=[o.name for o in bpy.data.objects if o.name.endswith('_knob')]
assert report['knobs']==['L_knob'],report['knobs']
report['gulls']=[o.name for o in bpy.data.objects if 'gull' in o.name and 'groove' not in o.name]
assert not any(n.startswith('L_') for n in report['gulls'])
assert set(report['gulls'])=={'R_gullL','R_gullR','hub_gullL','hub_gullR'},report['gulls']
enc=next(e for e in keys['encoders'] if e['half']=='L')
kn=bpy.data.objects['L_knob']
assert abs(kn.location.x*1000-enc['x_mm'])<.001 and abs(kn.location.y*1000-enc['y_mm'])<.001
report['encoder_xy_mm']=[kn.location.x*1000,kn.location.y*1000]
with open(os.path.join(HERE,'out','rev3_verification.json'),'w',encoding='utf8') as f:json.dump(report,f,indent=2)
print('[verified]',json.dumps(report))
