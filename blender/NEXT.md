# NEXT — F-pass R1..R12 complete, awaiting lead review

9 drafts at renders/stills/v1/draft/ + v1_contact.jpg (3x3). chasm_v1.blend saved.

## Deviations from spec
- plate.inset_mm: spec 4.7 -> 4.4 (opening min dist to outline is L 4.72 / R 4.58;
  4.7 fails its own assert). Gasket tabs reach 1.8 mm into the wall w/ notches.
- R10: contrast target >=20 required SMOKED near-opaque caps (clear cap tops
  saturate ~236 sRGB regardless of tint). Chose variant N: cap base
  [0.05,0.06,0.08] trans 0.35 rough 0.45 + legend emission 2.2 + glyph proud
  0.05 mm -> contrast 20.4. Tradeoff: caps no longer clear X-Ray.
- R2: front/back arm lengths + phi solved (front shorter). L: 31.4/48.6 mm,
  skew 15.5 deg, phi -24.8; R: 32.1/47.9, skew 14.3, phi 24.5; both bar ends
  at desk z +/-0.000.

## Evidence (blender/tmp/)
dbg_ustowed/udeployed/hub_gull/legends/exploded.png, look_bottom_A000/B030.png,
look_legend_{A..N}.png + _mask.png, prod_1_hero/2_top.png + _mask.png,
mask_stats.py, look_legend.py, prod_stats.py, design_rebuild.py, design_write.py
