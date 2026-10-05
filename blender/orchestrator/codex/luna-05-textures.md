Texture scout for the chasm keyboard renders (Blender Cycles). Work ONLY in D:\3DProjects\chasm\blender\tex\cc0\ (create). No git, no deletes. Append to blender/tex/cc0/LOG.md after each step. If creating a file fails with access denied, write it under a fresh subfolder instead and log it.
Find and download FREE, commercially-usable (CC0 preferred: Poly Haven, ambientCG, Share Textures; note license per asset) PBR sets at 2K (4K only for the desk):
1. Desk: light/medium natural OAK or white-oak wood (plank or veneer, fine grain, matte oil finish) - 3 candidates. Need color/albedo, roughness, normal (and displacement if small).
2. Window light: an HDRI of a bright interior with a strong sunlit window (Poly Haven interior HDRIs), 2-4K .hdr/.exr - 2 candidates; plus 1-2 window/blinds/plant shadow gobo images (CC0) for hard sun-shadow projection.
3. Frosted/sand-blasted acrylic or glass roughness/normal map (fine grain) - 2 candidates.
4. Fine plastic micro-texture (bead-blasted / sparkle-textured ABS like keycap tops) - roughness/normal - 2 candidates.
5. Metal: brushed stainless + polished/fingerprint smudge roughness overlay - 2 candidates.
6. Paper (for a notebook prop) and ceramic (mug) - 1 each.
For EACH asset: save into a subfolder per asset, make a 512px preview jpg (use Blender's Python if PIL is unavailable: D:\Apps\Blender\current\blender.exe -b --python-expr ...), and write INDEX.md: asset -> source URL -> license -> maps -> resolution -> one-line review (realism, tileability, scale in real cm, fit for our warm-oak-desk + window-light look). Finish with a "RECOMMENDED" section picking one per category with reasons.
