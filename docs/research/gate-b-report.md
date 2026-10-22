# Render polish + Gate B research (2026-10-13)

Based on rev3 (04b4628). Prices and links were checked on 2026-10-13; **"price: check"** means unverified. Nothing has been ordered.

## 1. Render critique (rev3)

### What makes rev3 look rough, worst first
1. **The hero is not a hero.** In 01 and 02 the camera looks steeply down and the boards fill only about 25% of the frame. The halves sit at random angles. The blind-slat shadows are the strongest graphic element and cut straight across the keys. Keychron and Mode product shots use a low 15–30° camera, the board fills 60–80% of the frame, and the light goes on the product, not the floor.
2. **The frosted case reads as grey plastic.** There is no edge glow, no thickness cue, and no light coming through the case. Real frosted acrylic glows at the edges and shows soft internals. In design.json, `frost_acrylic` uses transmission 0.9, roughness 0.42, a volume-scatter fake, and `shadow_transmit 0.6`. The edges come out dull because the clear-bottom path and the scatter don't pick up enough light.
3. **The caps look like chrome boxes.** In 04 and 05, the clear X-Ray skin (roughness 0.20, IOR 1.5) over the white core reflects the dark environment. The side walls turn into silver and black mirror wedges. Real XRAY caps look milky and soft-glossy, not mirrored.
4. **Legends are tiny, faint and uneven.** They look punched in, not like second-shot plastic, and E, R and T almost disappear. The F homing bar shows as a grey rectangle.
5. **Overall the images are flat and muddy.** Exposure is set to −1.5 with AgX Base Contrast and a warm wood bounce, so the whites go grey-beige with no specular pop. Plinth shot 03 goes the other way: the backdrop is blown white and the subject is small.
6. **Metals are wrong.** The knob in 05 reads copper or bronze from the warm bounce and has no visible brushed grain. The polished weight and gull have nothing bright to reflect.
7. **The wood desk looks CG.** The grain is low-frequency and repeats, and every hero frame is dominated by the stripes.
8. **Detail shots: the DOF is used to hide things.** 04 has a very shallow focus band. 05 puts focus on the cap, so the knob, the main detail of that shot, is soft. The exploded view (07) shows small grey parts on a grey background with no hierarchy, and the switches look like noise.
9. **Geometry artifacts** (from NEXT.md plus what I saw): the second-shot legend volumes sit 0.04 mm proud and overlap the clear shell, which explains the odd legend edges. Icon boolean cuts were removed. The OLED text on the hub (06 and 06b) is blurry and too small. Case corner and bezel proportions are flagged in NEXT.md as an open taste question.

### Fixes in Blender, in priority order
**P0 (framing and light, most of the gain)**
- Hero camera: 50–85 mm lens, about 20° elevation, both halves parallel at the real typing gap, hub centred behind. Subject fills about 70% of the frame. Use f/4–5.6 focused on the right-half F key, so the board stays sharp front to back.
- Lighting recipe for a studio hero: a large softbox key (area light, 1.5–2 m², about 45° camera-left and high), a long strip rim behind and above to catch the acrylic edges and the cap tops, and a low-strength neutral HDRI fill (the CC0 review already picks `small_empty_room_3`). Keep the blind slats for at most one lifestyle frame, softer and running along the board, never across it.
- Set exposure to about 0. Keep AgX but try the "Punchy" or "Medium High Contrast" look. Grade with Curves so the cap tops land around 235/255, not 190.
- Backdrop: seamless sweep in light warm grey (base about 0.55–0.65) for the studio set. Drop the oak for the hero and use it in only one lifestyle shot.

**P1 (materials)**
- *Frosted acrylic (Cycles, Principled v2 in Blender 4.x):* Transmission weight 1.0, IOR 1.49, roughness 0.35–0.5, base white. Add a Noise (scale about 2000/m) → Bump (strength 0.05) for bead-blast. Remove the `shadow_transmit` light-path hack. Instead raise transmission bounces (already 32), turn on Caustics → Filter Glossy 0.5, and add a low Volume Scatter (density 2–5, anisotropy 0.3) inside a solid, non-shell mesh so the edges glow. The edge glow needs solid geometry with real thickness and a rim light.
- *X-Ray caps:* one mesh with two materials, not overlapping volumes. Clear skin at roughness 0.08–0.15 plus Coat 0.3. Give it a slight milky Volume Absorption or Scatter (density 1–3) so the walls go soft white instead of mirror. Make the legend a boolean-unioned inner core with no 0.04 mm coplanar overlap.
- *Legends:* use the real XRAY legend font size, roughly 2.5–3× the current size, as the 2026-10-02 review also asked. Use a decal/second-shot material with a slight emission of 0 and subsurface 0.1. Check that legend depth reaches the skin.
- *Brushed stainless (knob side):* Principled metallic 1, roughness 0.25–0.35, Anisotropic 0.7–0.9, with tangent set to radial or UV along the circumference. Grain comes from a Noise texture stretched about 200:1 → roughness and bump at 0.002 mm. Check the knob base colour is neutral (0.62 grey, no tint) and kill the warm bounce with a light-linked rim. *Polished:* roughness 0.03–0.06. It needs a large softbox to reflect, otherwise it reads black.
- *Knurl:* a real displaced or modelled knurl (Array plus a boolean, or a geo-nodes diamond pattern) so the knurl doesn't alias.

**P2 (finish)**
- Samples: finals at 1024+ spp with adaptive threshold 0.005, OIDN at "High" quality with the albedo and normal passes. Use light-path clamping (Indirect 10) to kill the caustic fireflies through the stacked clear parts. Turn on motion-blur-free 16-bit PNG output.
- Exploded view: dark background, or white with a soft floor shadow. Space the layers evenly at about 1.5× their thickness. Add 1–2 mm callout lines or labels in post. Render the switches as one instanced row, not scattered.
- OLED: render the screen as an emission texture at 2× res from `make_oled.py`, with real SSD1306 pixel pitch, emission strength 3–5, behind black glass.
- Post: a subtle vignette, 0.2% film grain, and glare (Fog Glow, threshold 1.0) for bright edges only.

### Reference looks (sources to study, not to copy)
- Keychron Q-series and Mode Sonnet/Envoy product pages: low angle, soft key light, gradient sweep, sharp product.
- Qwertykeys (QK) frosted/translucent cases: rim light shows the edge glow.
- PBTFans XRAY listing photos: what the caps should look like (milky, not chrome).

### CC0 texture sources
Poly Haven (polyhaven.com: HDRIs, studio_small_*), ambientCG (ambientcg.com: Plastic, Metal, Wood). The repo already uses ambientCG Metal049A. None has a true frosted-acrylic map, so stay procedural.

### Re-render notes
- `blender/chasm_v3.blend` is not in the repo (saved on Ben's PC). The scene can be rebuilt from `build_scene.py` / `render_shots.py` + `design.json`; `render.device` is "CUDA" and must change for CPU-only machines.
- CPU is fine for look-dev drafts (640×800, 32–64 spp). Finals (1600×2000, 512–1024 spp, 32 transmission bounces) belong on a GPU.

---
## 2. Gate B: recommendations

| # | Item | Recommendation | Source |
|---|---|---|---|
| B2 | LiPo | **803450, 1500 mAh, about 8 × 34 × 50 mm** (some listings say 52 mm or 7.8 × 33.4 × 49.3 ±5%), PCM protection, JST-PH 2.0. Gives about 4+ weeks on the §8b budget. If the 8 mm height breaks the stack, fall back to a 603450-class 1200 mAh (Adafruit #258 is **34 × 62 × 5 mm**, which is longer). Leave about 10% swelling clearance and **verify polarity**. | ydlbattery.com/en-gb/products/1500mah-803450-rechargeable-lipo-battery · temperosystems.com.au/products/803450-3-7v-1500mah-lithium-ion-polymer-battery-lipo-ph2-0/ · adafruit.com/product/258 (price: check) |
| B4 | Hot-swap vs solder | **Hot-swap (Kailh CPG151101S11)**. It allows switch testing for the feel matrix, the cost is trivial ($1.50 per 10 at Typeractive), and it works with a PP plate as long as the switches seat in the plate. Cost: about 1.8 mm under the PCB (the stack-up draft value; confirm from the datasheet drawing) and a 100-cycle rating on the base part (the -4 variant is rated 5000). | typeractive.xyz/products/hotswap-sockets · kailh datasheet m.fi.kailhdz.com/uploads/15927/files/CPG151101S11.pdf · kailh.com/en/Products/Ks/HPC/CPG151101S11-4.pdf |
| B5 | Stabs | **PCB screw-in.** A PP plate flexes, and plate-mount stabs on PP rattle and shift. Need: 2× 2u (Bksp, L-Space), 2× 2.25u (L-Shift, Enter), 1× 2.75u (R-Space). Common kits ship 4× 2u + 6.25u/7u only, so confirm 2.25u/2.75u wires or buy individual sizes. Durock V2 kits run $16–20: $18 at mechanicalkeyboards.com, $19.50 at pkkeyboards.com. | mechanicalkeyboards.com/products/durock-stabilizers-v2-pcb-mount-screw-in-tkl-kit · pkkeyboards.com/products/durock-v2-stabilizers-screw-in |
| B6 | Gasket tabs (PP) | Starting point (common gasket practice; test in Phase 2): **6–8 tabs per half**, about 10–15 mm wide, about 1.5–3 mm Poron each side. Put them at the corners plus mid-span of the long edges, and add one by the knob and one by the 2.75u. Keep them out of the switch rows' stress lines and away from the antenna keep-out. A PP gasket mount is fine; PP sags in a tray mount. | doonx.com/products/1-5mm-white-polypropylene-sheet (laser-safe 1.5 mm PP) |
| B7 | Case route | **CNC per JLCCNC rules:** walls ≥1.5 mm, 2 mm+ where drilled or fastened. Internal radius R = H/10 + 0.5 mm, so about R0.5 for pockets ≤3 mm and larger as pockets get deeper. Model threads at the tap-drill diameter, thread depth ≤3× diameter, ±0.05 mm possible, 3-day minimum lead. Bead-blast or frost and the clear-bottom polish must be called out on a 2D drawing. **I have no quotes:** JLCCNC and PCBWay need a STEP upload to quote, which is a reversible step but needs CAD first. Fallback: stacked laser-cut acrylic at the Makerspace (≤1/4"). | jlccnc.com/help/article/cnc-machining-design-guideline · jlccnc.com/blog/acrylic-and-pmma-cnc-machining · jlccnc.com/help/article/cnc-machining-ordering-guidelines |
| B8 | Fasteners | Don't tap thin acrylic: an M3 thread in a 3 mm wall strips or crazes. Run M2/M2.5 **through-bolts from the bottom into tapped holes in the stainless weight** (the weight carries the threads). Where acrylic needs a thread, use **heat-set or press-in brass inserts** in ≥2× diameter of wall, or a captive nut. JLCCNC offers threaded-insert service. Leave clear-bottom bolt holes about 0.2 mm oversize, use nylon washers, and don't over-torque (crazing). | glcncmachining.com/acrylic-cnc-processing-service-guide/ · jlccnc capabilities page |
| B3 | Ball plunger | Press-fit stainless ball plunger, **3 mm body × 4 mm long, 2.38 mm ball, 4 N initial / 9 N full**. A 4 × 5 mm / 3 mm-ball version is the step up. Test catch force in Phase 2. | vital-parts.co.uk/press-fit-spring-plunger/14227-ind100 (and 14228-ind101) · mcmaster.com/products/ball-plungers/mount-type~press-fit/ (price: check) |
| B3 | OLED | 128×64 SSD1306 0.96" I²C (ZMK-supported). The display spec already calls for this class; get the module outline and active area into `ref/` from the chosen vendor. **Not verified today: dims, price: check.** | — |
| B3 | Encoder | Alps EC11-family with a knob shaft. The knob is a custom stainless part. **Dims and price: check** (Alps EC11E datasheet). | — |
| B3 | USB-C | 16-pin USB 2.0 mid-mount or top-mount receptacle (common JLC parts). Pick one so the port edge height matches the stack-up, with CC 5.1 kΩ pull-downs (risk #1). **Part # and price: check.** | — |
| B3 | Tent hinge | The U-frame needs a detent or friction hinge, or the ball-catch itself. **Not researched today.** | — |

---
## 3. Phase 2: typeable prototype parts (per both halves)

| Part | Qty | Price | Link |
|---|---|---|---|
| nice!nano v2 | 2 | $25.00 each = $50 | typeractive.xyz/products/nice-nano |
| Kailh MX hot-swap sockets | 7 packs of 10 (68 keys + spares) | $1.50/10 → $10.50 | typeractive.xyz/products/hotswap-sockets |
| Keygeek Y2 switches | 70 (7 × 10) | about $3.50/10 → about $24.50 | unikeyboards.com/products/keygeek-y2-linear-switch-factory-lubed-10pcs · milktooth.com/products/y2 |
| Durock V2 screw-in stabs | 1 kit + 2.25u/2.75u wires | $18–19.50 | see B5 |
| LiPo (proto: nano-sized, e.g. 301230, or the 803450 to test fit) | 2 | price: check | see B2 |
| 1.5 mm PP sheet (plate, laser at Makerspace) | 1 | price: check | doonx.com/products/1-5mm-white-polypropylene-sheet |
| Diodes 1N4148 (THT), wire, machine-pin sockets | ~70 | price: check | typeractive.xyz/collections/nice-nano (sockets from $6.50) |
| Poron gasket strips | — | price: check | — |

Note: hand-wiring with hot-swap sockets means soldering the sockets to wire, which is doable, or using a cheap 2-layer "matrix" PCB. The XRAY caps are already owned, or planned.
**Known subtotal, excluding unknowns: about $103–105** before shipping and tax.

The roadmap drafted from this research lives in [`docs/ROADMAP.md`](../ROADMAP.md).
