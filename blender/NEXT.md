# Rev3 checkpoint (Sol)

Done: Eight inspected 640x800 drafts in renders/stills/v3/draft; renders/review/v3_contact.jpg; two inspected 1600x2000/192spp single-frame previews in renders/stills/v3/preview. Saved full flat hero scene blender/chasm_v3.blend. Parametric case and caps, runtime plan derivation from design.json + keys_8, SolidWorks handoff refreshed. Saved-scene and artifact checks passed.

Half-done: None in authorized delivery. STOP for Claude/Ben review; no finals or further edits automatically.

Evidence: blender/out/rev3_verification.json, rev3_artifact_audit.json; blender/tmp/rev3_delivery_closed_final.log, rev3_verify_final.log, rev3_opening_final.log. Render timings in each output directory times.json.

Rollback: blender/tmp/rev3_baseline contains original source/config copies. No git operations, installs, or main-agent deletions. Geometry workers used recycle.py for scratch cleanup.

Texture limits: INDEX.md recommended White Oak Veneer at50cm and Blinds4K integrated. Plastic004 is an explicitly labelled cap microtexture proxy; accurate frosted acrylic and directional brushed steel maps were not acquired, so fine procedural surface normals/anisotropy supply those. Physical slats supply hard shadows because no binary gobo was delivered. White second-shot volumes overlap the closed clear render shell and finish0.04mm proud; unstable icon Boolean cuts were removed. Disjoint production tooling, fonts/vendor geometry and spring/section geometry remain pending production CAD review.

Measured draft times: 1_hero=6.8s, 4_macro_legends=18.9s, 2_top=6.5s, 3_plinth=5.0s, 5_macro_detail=10.0s, 6_hub=5.5s, 6b_hub_ports=5.4s, 7_exploded=5.4s. Preview times: 1_hero=77.8s, 4_macro_legends=279.4s.

Exact commands, only if revision is requested:
```powershell
& 'D:/Apps/Blender/current/blender.exe' -b --factory-startup --python-exit-code 1 --python blender/regenerate_opening.py
& 'D:/Apps/Blender/current/blender.exe' -b --factory-startup --python-exit-code 1 --python blender/render_shots.py -- --draft-and-preview
python blender/contact_sheet.py
& 'D:/Apps/Blender/current/blender.exe' -b blender/chasm_v3.blend --python-exit-code 1 --python blender/verify_rev3.py
python blender/tmp/rev3_artifact_audit.py
```

Open review: rectangle case family and bezel proportions; clear skin/core/legend depth; hard shadow placement; photo texture/lighting quality. User owns taste and direction. Stop here.
