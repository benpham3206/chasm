# Rev2 draft checkpoint (Sol)

Done: eight inspected 640x800 draft PNGs in renders/stills/v2/draft, renders/review/v2_contact.jpg, blender/chasm_v2.blend saved in the full flat hero setup, parametric SolidWorks outline/section handoff in blender/out/solidworks_handoff.json. Geometry from design.json + keys_8.json and scripts. Validation evidence: blender/out/rev2_verification.json; logs in blender/tmp/rev2_verify_final.log, rev2_opening_final.log, rev2_batch2.log, rev2_dark_final.log.

Half-done: none in the authorized draft build. Literal vendor tooling/font/icon fidelity and mechanical production validation remain outside the verified result. No finals, commit or push. Stop for Claude/Ben review.

Changed source: design.json, outline.py, build_scene.py, render_shots.py, contact_sheet.py; added rev2_opening.py, regenerate_opening.py, rev2_case.py, rev2_keycaps.py, rev2_environment.py, contact_sheet_windows.ps1 and verify_rev2.py. Original dirty checkout preserved; script/config rollback copies in blender/tmp/rev2_baseline. No packages installed.

Reference substitutions: Bahnschrift plus Segoe UI Symbol, reference-matched Cherry row sculpt and vector kit-style icons. Macro keys use novelties. Layout has no Esc key; its icon mapping is provided without replacing an existing key. Leaf dimensions/count and R135 underside are parametric concept estimates, not vendor CAD. Combined cap skirt wall approximately1.3mm (1.1mm body +0.18mm skin); frost/white legends intentionally subtle, clearest in04.

Measured render seconds: 01 5.9 / 02 5.2 / 03 4.3 / 04 14.4 / 05 7.4 / 06 4.3 / 06b 4.3 / 07 5.5; sum51.3, excluding build. 32spp with denoise; 04 uses64spp. All framing checks passed.

Exact reproducible draft commands, only if revision/rebuild is requested:
```powershell
& 'D:/Apps/Blender/current/blender.exe' -b --factory-startup --python-exit-code 1 --python blender/regenerate_opening.py
& 'D:/Apps/Blender/current/blender.exe' -b --factory-startup --python-exit-code 1 --python blender/render_shots.py -- --draft
python blender/contact_sheet.py
& 'D:/Apps/Blender/current/blender.exe' -b blender/chasm_v2.blend --python-exit-code 1 --python blender/verify_rev2.py
```

Open review: case silhouette/shared family; white frost and white-on-white legend contrast; right gull bay; macro compositions; exploded detail readability. Await Claude/Ben direction. Do not start finals automatically.
