# CC0 Texture Scout Index

For Chasm keyboard Cycles renders. Asset folders contain source files and a 512 px JPEG preview. Each folder has its own `INDEX.md`; source package metadata is retained where supplied.

## Desk oak candidates (2K)

| Asset | Source | Maps / scale | Review |
|---|---|---|---|
| [White Oak Veneer](white_oak_veneer/) | [Poly Haven](https://polyhaven.com/a/white_oak_veneer), CC0 | Diffuse, roughness, GL normal, displacement; 50 x 50 cm | Closest match: light white oak, fine pores, matte raw veneer. |
| [Oak Veneer 03](oak_veneer_03/) | [Poly Haven](https://polyhaven.com/a/oak_veneer_03), CC0 | Diffuse, roughness, GL normal, displacement; 100 x 100 cm | Low contrast light oak; soft realistic grain for broad desk panels. |
| [Oak Veneer 05](oak_veneer_05/) | [Poly Haven](https://polyhaven.com/a/oak_veneer_05), CC0 | Diffuse, roughness, GL normal, displacement; 100 x 100 cm | Slightly warmer/darker grain; useful alternate. |

Additional 2K downloaded wood: ambientCG Wood 049 (oak-tagged, 80 cm), Wood Floor 049 (planks, 130 cm), Wood 048 and 050 (light generic wood, 80 cm), Wood 022 (fine generic wood; size not listed). These are documented in their own folders.

## Window light and gobos

| Asset | Source | Resolution / license | Review |
|---|---|---|---|
| [Blinds HDRI](blinds/) | [Poly Haven](https://polyhaven.com/a/blinds), CC0 | 4K EXR, 4096x2048 | Warm direct sun through blind slats; recommended hard-sun source. |
| [Small Empty Room 3](small_empty_room_3/) | [Poly Haven](https://polyhaven.com/a/small_empty_room_3), CC0 | 4K EXR, 4096x2048 | Morning window through curtains and cool LED panels; softer interior fill. |
| [Blinds panorama](gobo_blinds/) | [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:Blinds_%E2%80%93_Panorama_(Greg_Zaal_via_Poly_Haven).jpg), CC0 | 8K JPG panorama; 512x256 preview | Useful texture reference for a projector, but not a binary gobo mask. |

A separate plant silhouette gobo and a clean window/blinds mask image are not included. Extracting the hard-edged window/slat mask from the panorama remains a small follow-up.

## Frosted glass / acrylic

No downloaded set met the fine-grain frosted/sand-blasted criteria. A true surface candidate still needs to be sourced; do not substitute ordinary Glass BSDF roughness as a texture asset.

## Keycap plastic microtexture

Downloaded ambientCG Plastic 004/010 and Plastic 002/006 at 2K. Plastic 004 is the best rough matte experiment; none is confirmed as fine bead-blasted/sparkle ABS. See each folder review.

## Metal

Downloaded Metal 049 A clean silver and Metal 049 B smeared silver at 2K. The latter is the best fingerprint-style surface breakup. None is confirmed as directional brushed stainless; Metal 009/010/011/012 are brushed but are coarse/bumpy exploratory library assets.

## Notebook paper and mug ceramic

[Paper 001](paper_notebook/) is included at 2K. No mug-specific ceramic material was found/downloaded; mug body is better treated as a solid ceramic shader unless a mottled glaze texture is desired.

## RECOMMENDED

- **Desk:** White Oak Veneer ? correct light species/color, subtle pore detail, calibrated 50 cm scale, full PBR set.
- **Window direct light:** Blinds HDRI ? warm interior sun and crisp slatted window pattern.
- **Window fill:** Small Empty Room 3 ? realistic softer curtain-filtered fill.
- **Gobo:** Blinds panorama ? available CC0 projection reference; threshold/extract a grayscale mask before use as a hard gobo.
- **Frosted acrylic:** no recommendation yet; qualifying map set not acquired.
- **Keycap plastic:** Plastic 004 for a matte test; treat it as a rough-plastic proxy pending a true microtexture.
- **Metal:** Metal 049 A base plus Metal 049 B roughness/variation for a handled silver trim look; brushed grain itself remains unfilled.
- **Notebook:** Paper 001.
- **Ceramic mug:** simple ceramic shader; no mug-specific texture candidate acquired.

## Scope / download notes

All files and generated indexes/previews are inside this directory. ambientCG PBR bundles were downloaded via its official `get?file=` endpoint, Poly Haven wood maps and HDRIs via official asset download endpoints, and the panorama via Wikimedia Commons. No project files outside `blender/tex/cc0/` were modified.
