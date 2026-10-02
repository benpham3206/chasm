Orchestrator feedback on draft set 1 (from the user + orchestrator review). Apply all, re-render drafts, contact sheet, then write the CHECKPOINT line and stop.

USER DESIGN CHANGE - tenting (overrides brief; see user's sketch + paper prototype in ref/tenting/ and docs/decisions/2026-10-01-tenting.md): the current tent mechanism is far too much. Replace it with a minimal polished-stainless U-frame per half, recessed flush in the case underside near the OUTER edge. The U's arms run inward from the outer edge; the hinge line is across the arm ends (inboard); the U's bar lies along the outer edge. To tent, the U swings down about the hinge and its bar becomes the outer foot. A small folding locking linkage (over-center strut) on each arm holds it open; it folds flat with the U when stowed. Tent angle: 4 deg exactly (design.json param). Reference: the QK Alice Duo's all-metal dual-hinge tenting (two positions, 0 deg flat / 5 deg; stiff metal hinge, no plastic kickstand) - ours is the same idea with positions 0 / 4 deg; Duo underside photos are in ref/style/alexotos/ (duo_2018, duo_2045). Show stowed (invisible from above/side) and deployed. Remove the black block and any other legs/struts.

Fixes:
1. Framing: every shot except the hero is far too close and focus is extremely shallow (check mm vs m in camera distance and f-stop/focus distance). Keep the whole subject of each shot in frame with breathing room; DOF only gently soft on 04_gull.
2. Hero: left half is cut off at the left edge - fit the full set with margin.
3. Exposure/backdrop: scenes are blown toward pure white. Backdrop must read as light cool grey (alexotos), caps and frost need visible edge definition; nothing clipped.
4. 03_plinth: big black shape in the background (a flag/card visible to camera?) - hide it from camera or remove.
5. Key legends: not visible anywhere yet - add the white double-shot-look legends per brief.
6. OLED: content is inverted. Real OLED = black glass, white/light pixels on black.
7. Gull logo: must be variant C exactly (two mirrored wings from one vertex, wings rising from the vertex then curving out; brand/gull_logo.py). On the hub it currently reads as a single arch + tick. Beside G/H on the halves it is not visible in 04_gull - make sure the inlays exist and the shot shows both wings meeting at one point with the halves pushed together.
8. Clear bottom acrylic renders as frosted - make it clear/polished so the weight reads sharply.

NEW SHOT (user request): 07_exploded - the entire keyboard exploded along Z with even gaps, both halves + hub: keycaps / switches / stabilizers / PP plate / gasket strips / PCB / foam / battery + RF module / stainless weight / U-frame tent / clear bottom / frosted case frame. Backdrop inspired by ref/style/alexotos (light cool grey seamless, soft window light, low plinths). Add explode distance + order to design.json so CAD can reuse it. Mount is now GASKET: show gasket tabs on the plate edge (positions are placeholders, see docs/HANDOFF.md).

CRASH-SAFE WORK (user requirement - usage may cut out at any moment):
- After EVERY meaningful step (not just milestones): append a PROGRESS.md line and overwrite blender/NEXT.md with: what is done, what is half-done, the exact next command(s) to run, and any open problem. A fresh agent must be able to continue from NEXT.md alone.
- Keep all work as re-runnable scripts + design.json (never only in Blender memory); save chasm_v1.blend after each successful build.
- Write render outputs directly to their final paths so partial results survive.
