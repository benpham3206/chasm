"""Regenerate openings using Blender's NumPy, with numeric clearance checks."""
import hashlib
import json
import os
import sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import outline as ol
import rev2_opening
D,keys=ol.load()
ol.check(D,keys)
ops={}
for half in 'LR':
    op=rev2_opening.opening(D,keys,half)
    poly,_,_=ol.outline(D['case']['outline'][half],keys['keys'],half,keys['unit_mm'])
    corners=[p for k in ol.select(keys['keys'],half,'all') if not k.get('solid_top') for p in ol.key_rect(k,keys['unit_mm'])]
    assert all(ol.point_in(op,p) for p in corners),f'{half}: key outside opening'
    clearance=min(ol.dist_to_poly(op,p) for p in corners)
    frame=min(ol.dist_to_poly(poly,p) for p in op)
    assert clearance>=D['case']['opening_clearance_mm']-0.05,f'{half}: opening clearance {clearance}'
    assert frame>=D['case']['opening_frame_min_mm'],f'{half}: frame {frame}'
    print(f'[opening] {half}: {len(op)} pts, clear {clearance:.3f}mm, frame {frame:.3f}mm',flush=True)
    ops[half]=[[round(x,4),round(y,4)] for x,y in op]
src=json.dumps([D['case'],keys['keys']],sort_keys=True)
out={'_doc':'Generated top-opening polylines, CCW millimetres. Blender numpy/stdlib raster union; regenerate with blender/regenerate_opening.py.',
    'source_sha1':hashlib.sha1(src.encode()).hexdigest(),**ops}
with open(os.path.join(HERE,'out','opening.json'),'w',encoding='utf8') as f:json.dump(out,f,indent=1)
print('[opening] wrote opening.json',flush=True)
