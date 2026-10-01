# Reference: acrylic case + heavy weight

*Researched 2026-09-29. Goal: frosted acrylic that still feels premium-heavy, "liquid glass" look. Weight math is from material densities, not quotes.*

## How much metal

The Duo is ~800 g per half. An acrylic shell that size is only ~150-250 g, so ~550-650 g per half has to be metal.

| Material | Density | For ~580 g per half | Notes |
|---|---|---|---|
| Brass | ~8.5 g/cc | ~4 mm over 170 x 100 mm | Warm, tarnishes unless coated |
| Stainless | ~8.0 g/cc | ~4.2 mm, same footprint | Cooler, reads more "glass", harder to machine |
| Tungsten | ~19.3 g/cc | ~2 mm | Thin and very heavy, expensive |

Summit's weights were laser-cut 1.6 mm sheet (`flurples-summit.md`). At 1.6 mm brass we'd get ~230 g per half — need either ~4 mm stock or a stack of two plates.

## Acrylic vs polycarbonate

- **Cast acrylic (PMMA):** clearest polish, best edge-lighting. Brittle — cracks at threaded holes and chips at port cutouts. JLCCNC does CNC + optical polish ([guide](https://jlccnc.com/blog/acrylic-polishing-guide)).
- **Polycarbonate:** tough, safer for USB-C cutouts and the ball catch, scratches easier, polishes less clear. What Summit and the XRAY collab boards use.
- Walls ~4-5 mm for stiffness.

Our lock is acrylic. Fine, as long as the plastic isn't load-bearing.

## Structure: metal is the chassis

- Weight plate carries the load. Acrylic is clamped to it with through-bolts + metal barrel nuts or inserts, never tapped threads in acrylic.
- Tenting feet and the ball catch's mating points mount to metal where possible.
- Weight stays clear of the nRF52840 antenna keepout and never touches the LiPo (already in risk register 2 and 7).

## The look

- Frosted inside, polished outside → glow diffuses evenly behind a glassy surface. Matches the frosted-body + clear-window decision.
- Polished chamfers on the top edge catch light like a lens. Biggest single "glass" cue.
- Large, continuous corner radii instead of tight circular ones.
- Edge lighting: side-view LEDs into a polished acrylic edge make the edge glow. Already planned; test strip in Phase 2.
- Single milled shell over stacked laser-cut layers if budget allows — stack lines read industrial. The stacked fallback still works for prototypes at the SJSU makerspace.

## Sound

Hollow acrylic rings bright. The weight, perimeter foam and soft mount pull it back toward the deep/thocky target. Add "weight on vs off" to the Phase 6 matrix (already listed).

## Takeaways applied to Project Alice

- Resolves BOM "brass vs stainless" into a thickness question: ~4 mm of either per half.
- Add to Phase 2 CAD: weight as structural bottom, bolt pattern, antenna window cut into the weight.
- Get CNC quotes for the acrylic pair (rough guess $150-350 polished) and the weights ($60-150 per half) in Phase 3. Unverified estimates.
