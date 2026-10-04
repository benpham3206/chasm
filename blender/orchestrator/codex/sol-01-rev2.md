# Brief: chasm render rev 2 (Blender, headless) — for GPT-6.1 Sol via Codex

You are the build agent for the **chasm** split keyboard concept renders, working in `D:\3DProjects\chasm` (git repo). Claude orchestrates and reviews; the user (Ben) decides. Read first, in this order:
1. `docs/decisions/2026-10-04-design-rev2.md` — **the requirements for this round** (authoritative)
2. `docs/HANDOFF.md`, `blender/PROGRESS.md` (last 15 lines), `blender/NEXT.md`
3. Existing pipeline: `blender/design.json` (all numbers), `blender/outline.py` (case outlines + top opening from `cad/layout/out/keys_8.json`), `blender/build_scene.py` (scene), `blender/render_shots.py` (shots, auto-framing), `blender/contact_sheet.py`. Blender: `D:\Apps\Blender\current\blender.exe -b --factory-startup --python-exit-code 1 --python <script> -- <args>` (Cycles CUDA, GTX 1660 SUPER 6 GB). Skill notes: `C:\Users\hotdo\.agents\skills\blender-headless\SKILL.md`.
4. References: `ref/shape/evo75/` (SUMMARY, SPECS, frames/, contact.jpg), `ref/shape/neo75/`, `ref/reviews/` (Evo75 transcript, Neo75 notes), `ref/modmusings-xray/INDEX.md` (73 X-Ray images; kit sheet `038_X-ray_R1-17.jpg`, macro `008_X-Ray_HD_25.jpg`), `ref/style/user-2026-10-04/` (03 kit sheet, 04 legend macro, 05/08 caps in warm light, 11 coffee-desk lifestyle, 12 desk top view).

## Hard rules
- Write only inside `D:\3DProjects\chasm`. Scratch in `blender/tmp/`. **No git commit/push** (Claude commits). No installs without logging why.
- Bulk file deletion is blocked by a safety hook; if you must remove generated files, use `python C:/Users/hotdo/.agent-hooks/recycle.py <paths>`.
- Everything stays **parametric**: every dimension in `design.json` (with a one-line note), geometry from scripts. The case will be rebuilt in SolidWorks from the same numbers — prefer lines/arcs/fillets with explicit radii, and write a `blender/out/solidworks_handoff.json` of the case section profile + plan outline params.
- **Crash-safe**: after every meaningful step append to `blender/PROGRESS.md` (`- [YYYY-MM-DD HH:MM] WORKING|CHECKPOINT|BLOCKED <what> | next: ... | files: ...`, tag lines `(Sol)`) and overwrite `blender/NEXT.md` (done / half-done / exact next commands / open problems).
- Look at your own renders (open the PNGs) and fix what's wrong before reporting.

## Work (in order)

**A. Layout sync.** `cad/layout/out/keys_8.json` now has the macro column one row lower and an `encoders` entry (knob slot = top-left of the LEFT half). Re-point the knob to that encoder position (replace `knob_kb` anchor logic; virtual key in `outline.py` should use the encoder slot). Remove the knob from the right half. Hub: no knob anywhere (06b still shows an old knob — fix).

**B. Logo.** Remove the split gull inlays on both halves (beside G/H). Add ONE full gull (variant C, both wings, `brand/gull_logo.py`; same style as the hub gull, polished stainless inlay) on the RIGHT half case top, in the empty spot **right of the Up key, above the Right arrow**.

**C. Case shape = "mini Evo75" per half.** Each half gets the Evo75 silhouette: rounded box top shell over an inward-tucked wedge base, graduated curve on the side, soft rounded edges, uniform bezel, 8° typing angle feel, front height ~19–20 mm; clean uninterrupted lines like the Neo75; softer side curve (~Neo75). Both halves must be the **same family** (same bezel, corner radii, height, edge profile, seam line) — v1 looked inconsistent. Keep frosted acrylic top shell, clear bottom over stainless weight. Plan outline still follows each half's key area (stagger) but with Evo75-like clean straight runs + generous corner radii. Mount: **Evo75-style butterfly leaf-spring gasket** (metal leaf springs at the plate edge + silicone pads; PP plate; 1.2 mm flex-cut PCB) — model it visibly for the exploded view, parameters in design.json.

**D. Keycaps: 1:1 PBTfans X-Ray (Cherry profile) recreation, max detail.** Real Cherry profile per row (R1–R4 heights/tilts, top size, cylindrical dish depth, side wall draft/slight concave, edge radii), hollow shell with ~1.3 mm walls and MX stem/cross (visible in exploded view), homing bars on F/J as in the kit. X-Ray look: **white** double-shot body under a thin frosted-clear outer skin (see macro refs: sparkly frosted top, clear rim at the edges, white body), legends = white second shot reaching the surface, slightly raised/visible by shadow. **Exact kit legends**: sublegends ('!' over '1' etc.), the kit's icon modifiers (⇧ shift arrow, ⌘-like, ◇, ⌥, ↵ enter arrow, ← backspace, Tab arrows, caps lock icon, menu ≡), arrows, Esc, M1–M4 → use kit novelties if no M legend; match the kit's rounded geometric font as closely as possible with installed fonts (log choice). Legend placement as on the kit sheet (alphas top-left, mods bottom-left, sizes). Fix legend font scale already handled by `font_cap_scale()`.

**E. Shots (photoreal).** Replace the shot list with:
1. `01_hero` — **warm oak desk, window light, hard sun shadows**, the full setup visible (both halves + hub; optional mug/notebook props kept minimal), camera close enough to read keycap detail (v1 hero was too far).
2. `02_top` — top-down on the same desk (full setup).
3. `03_plinth` — keep the v1 03_plinth look the user loved (light grey studio, plinth), caps now white X-Ray; tent parked → board flat.
4. `04_macro_legends` — macro point of interest: X-Ray legends/sparkle frost, shallow DOF (ref 04.png / 008_X-Ray_HD_25.jpg).
5. `05_macro_detail` — second macro: the knob + left-half corner, or the gull inlay by the arrows (pick the better).
6. `06_hub` / `06b_hub_ports` — hub (no knob), keep framing approach, warm desk or studio to match.
7. `07_exploded` — **dark grey studio**, both halves + hub exploded with even generous gaps, leaf springs/plate/PCB/foam/weight/caps readable.
Drop the tent shot (03b) and 05_underside this round.

**F. Deliver.** Draft renders of all shots to `renders/stills/v2/draft/` (640×800, low spp + denoise), contact sheet `renders/review/v2_contact.jpg`, then write a `CHECKPOINT (Sol)` line with: what changed, deviations, render times, open questions — and stop. No finals.
