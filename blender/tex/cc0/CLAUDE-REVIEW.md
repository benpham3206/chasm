# Orchestrator review of Luna's picks (2026-10-04)

| Category | Verdict |
|---|---|
| Desk | **white_oak_veneer** (primary, matches the user's coffee-desk ref); wood_oak_veneer as darker alt. Use real-world scale from INDEX.md |
| Window light | Do NOT use `blinds` HDRI as key/world — strong pink/orange kitchen cast tints white caps. Use **small_empty_room_3** (neutral) at low strength for fill + a **warm sun lamp through physical blind slats / window frame** for the hard shadows |
| Gobo | `gobo_blinds` is the same panorama, not a mask — skip; use physical slats |
| Keycap micro | plastic_microtexture_* are scratch/grunge maps — skip. Make a **procedural fine sparkle/bead-blast**: high-freq noise/voronoi → bump (tiny strength) + roughness variation, sub-0.1 mm scale, on the clear skin top |
| Frosted acrylic | none found — procedural fine noise bump + roughness ~0.35–0.5 with transmission |
| Metal | no real brushed grain — procedural anisotropic/stretched-noise bump for brushed stainless; metal_clean_silver ok as subtle roughness variation for polished |
| Paper | paper_notebook ok for a prop |
