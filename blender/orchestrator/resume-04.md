Resume after quota reset. While you were out (2026-10-02 09:00-10:00) the orchestrator (Claude) applied part of section G directly - read PROGRESS.md (last lines) and `git log -3` first:
DONE by Claude: G1 clear X-Ray caps (abs_clear_frosted base 0.72/trans 0.95/rough 0.12, legend no emission); G2 legend size bug = Segoe fonts load at 0.42 x size in Blender -> font_cap_scale() in build_scene.add_legend, bold segoeuib; G5 plinth mat 0.26, height 25, margin 25; gull: edge_fillet 1.0->0.5, vertex_inset 0.8->0.3 (wings now meet at one point across the seam); 07_exploded: gap 42 mm, hub at [0,-150], no plinth (desk), el 21; G6 USB-C cutters now cross the full wall (halves -(wall+1.5)..3, hub Dd/2-wall-1.5..Dd/2+2).
REMAINING - do these, re-render drafts + contact sheet, update PROGRESS.md and NEXT.md after every step, then CHECKPOINT and stop (no finals):
1. G6 still failing: hub ports in 06b still render as frosted pills even with the through-cutter. Ray-cast from 10 mm outside each port (hub + both halves) and report the first hit; fix until it is usb_dark/usb_shell/tongue (suspects: bevel after boolean re-closing the hole, cutter normals, recess_mm geometry inside the shell).
2. G4: 05_underside weight renders as a black mirror; add the glossy-only reflection card (spec G4) and grey foam is already in; meet the G4 metrics.
3. 07_exploded: the hub's exploded stack overlaps the right half's lowest layers in frame - move it clear (e.g. further forward/left) so all three stacks read separately.
4. 01_hero: set fills ~70% of frame width.
Hub orientation and the 06/06b shots: keep exactly as they are (user).
Commits: do NOT git commit or push.
