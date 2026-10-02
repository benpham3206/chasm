# Brief: chasm concept render v1 (Blender, headless)

You are building the first concept renders of **chasm**, a split Alice mechanical keyboard with a wireless hub box. Inspired by the QK Alice Duo. Work only in `D:\3DProjects\chasm`. Use the `/blender-headless` skill (Blender 5.2.1 at `D:\Apps\Blender\current\blender.exe`, Cycles + CUDA on a GTX 1660 SUPER, 6 GB VRAM) and follow the `/3d-pipeline` stages.

An orchestrator (Claude Code) reviews your work at checkpoints and may resume this session with feedback. Make your state easy to read (see Reporting).

## Hard rules

- No git commit/push. Never write anywhere outside `D:\3DProjects\chasm`, not even temp files: use `blender/tmp/` for scratch (contact sheets, test renders). No skill edits, no installs without logging why in PROGRESS.md.
- You run non-interactively: a rejected tool call ends your session. Keep commands simple and inside the project.
- Read-only inputs: `cad/`, `docs/`, `brand/`, `hardware/`, `ref/`. Write only under `blender/` and `renders/`.
- Everything is **generated from numbers**: no hand-modelled one-offs. The case must later be rebuilt in SolidWorks from the same numbers, so every dimension lives in `blender/design.json` (with units and a one-line note each). Anything you had to assume goes in `design.json` → `"assumptions"`.
- Headless only: `blender.exe -b --factory-startup --python-exit-code 1 --python <script> -- <args>`.
- Draft renders first (low res, low samples). Do not spend GPU time on finals before checkpoint 1 is approved.

## Inputs

| File | What |
|---|---|
| `cad/layout/out/keys_8.json` | **Source of truth** for key positions: per half (`half` L/R), mm, y up, origin = that half's key-area bbox centre; `x_mm, y_mm` = key centre, `rot_deg`, `w_u` (1u = 19.05 mm), `stab` (≥2u), `label` |
| `cad/layout/out/preview_8.png` | Visual of the layout (68 keys) |
| `brand/gull_logo.py` | Logo. Use variant **"C gull"**: right wing = cubic Bézier from vertex (0,0) via (1,6),(8,10) to (12,8), y up; left wing = mirror in x |
| `docs/cad-gates.md`, `docs/decisions/*.md` | Decisions + stack-up draft (heights) |
| `ref/style/alexotos/` | Photo style reference (alexotos' QK Alice Duo review) — `contact_sheet.jpg` |
| `ref/` (QK Duo images if present), Duo product render the user liked: two halves + small hub box, studio |

## What to build

### Halves (×2, from keys_8.json)
- **Case shape: Duo-like slab.** Even bezel around the key outline (start ~7 mm sides, ~6 mm top/bottom), outer corners rounded (~6–8 mm), front edge follows the angled alpha block (gentle curve/kink like the Duo), back edge straight-ish. The right half is wider at the bottom-right (arrow cluster) — the outline must follow it cleanly, no awkward notch. Inner edges face each other.
- **Thickness ~24 mm flat case** (stack-up in `docs/cad-gates.md`). Typing angle comes from slim rear feet (placeholder 6°) — model feet as part of the case bottom.
- **Material: full frost acrylic** for top frame + walls (translucent, diffusing, slight thickness-dependent glow, polished-free matte surface, soft edges with small fillets ~1 mm). **Clear polished acrylic bottom** (3 mm) through which you see the internals.
- **Internals (stand-ins at true size):** PP plate 1.5 mm (milky translucent), switches (simplified MX: 14 mm body, translucent housing, stem), white-soldermask PCB 1.6 mm, a nRF52840 RF module (~13 × 18 mm metal can) near the inner back corner, LiPo pouch (~50 × 34 × 5 mm, silver), **polished stainless steel weight** under the PCB visible through the clear bottom (rounded-rect slab ~4 mm, keep it clear of the RF module antenna end). One USB-C port per half on the **inner edge, near the back**.
- **Keycaps: PBTfans X-Ray look**, Cherry profile with row sculpt (R1: number row incl. `` ` ``, `-`, `=`, Bksp; R2: Tab…`\`; R3: Caps…Enter; R4: shift row, bottom row, arrows; macro M1–M4 = R1–R4 top to bottom). Material: clear ABS, lightly frosted body; **legends in white, double-shot look** (glyph embedded just under the top surface, readable mostly by shading/shadow, low contrast like the kit renders). Alphas/numbers legend top-left; modifiers bottom-left text. 1u cap base 18 mm, ~0.5 mm top dish. Spaces/2u+ stabilised (stab housings faintly visible through frost is fine).
- **No knob on the halves.** (Knob lives on the hub.)
- **Logo:** gull variant C as **polished stainless inlay** flush in the frosted top bezel, at each half's **inner edge**, beside G (left half) / H (right half), at home-row height. **One wing per half**, vertex at the inner edge, so the two halves pushed together form the full gull meeting at one point. Wing span ~10–12 mm per wing, stroke ~1.2 mm, rounded ends.
- **Tenting:** flip-out hinged legs on each half's **outer edge** (one or two legs per half), modelled stowed (flush in the bottom) and deployed (~12° tent). Parameterise hinge position and angle.

### Hub box (×1)
- Small Duo-like box (~62 × 42 × 16 mm start), same full-frost acrylic + clear bottom, internals visible as silhouettes (white PCB, RF module).
- **OLED** 128×64 behind a black glass window on top (show a simple status screen as an emissive texture: two battery bars L/R, "BLE", layer name).
- **Knob:** polished stainless, knurled side, ~18 mm dia, on top (Duo has its red knob there; ours is stainless).
- Ports on the back: 1 USB-C upstream + 2 USB-C downstream. Small gull inlay (full gull, both wings) on the top.

### Scene and look (alexotos-inspired)
Study `ref/style/alexotos/contact_sheet.jpg`. Key traits: **light grey (slightly cool) seamless**, large soft diffused key light (window/softbox feel), gentle soft shadows, muted and slightly desaturated grade, lifted blacks, no harsh specular blowouts; **low plinths/steps** for eye-level shots; shallow depth of field on detail shots; product fills the frame cleanly with generous negative space. AgX view transform (skill shows how). No busy props in v1.

### Shots (renders/stills/v1/)
| # | Shot | Notes |
|---|---|---|
| 1 | Hero 3/4 | Both halves split naturally (inner edges ~60–90 mm apart, slight inward yaw), hub box above/behind; 4:5 portrait |
| 2 | Top-down flat lay | Whole set, centred, 4:5 |
| 3 | Eye-level side on a low plinth | One half **tented** with legs deployed + hub, alexotos-style horizon line |
| 4 | Macro: the gull | Halves pushed together at G/H so both wings meet at one point; shallow DOF |
| 5 | Underside | Half flipped / low angle showing stainless weight + internals through clear bottom |
| 6 | Hub close-up | OLED lit, stainless knob, ports |

Final res 1600 × 2000 (4:5); drafts at 25–40 % and low samples with denoise.

## Code layout (deliverables)

- `blender/design.json` — all parameters + `"assumptions"`.
- `blender/build_scene.py` — reads `keys_8.json` + `design.json` + gull curve, builds everything into named collections (`L`, `R`, `Hub`, `Studio`); `--pose flat|tented|together`.
- `blender/render_shots.py` — cameras/lights per shot, `--shots 1,2,… --draft|--final`.
- `blender/chasm_v1.blend` — saved scene.
- `renders/stills/v1/draft/*.png`, later `renders/stills/v1/final/*.png`; contact sheet `renders/review/v1_contact.jpg`.
- Look at your own renders (open the PNGs) and fix what's wrong before reporting: floating objects, intersections, caps not seated, legends unreadable or garish, blown highlights, wrong logo position/shape, case outline lumps.

## Reporting (for orchestration)

Crash-safe: usage can end at any moment. After every meaningful step append to PROGRESS.md and overwrite `blender/NEXT.md` (done / half-done / exact next commands / open problems) so a fresh agent can continue from it alone.


Append to `blender/PROGRESS.md` after every milestone, newest last, format:
`- [YYYY-MM-DD HH:MM] <STATUS> <what you did> | next: <...> | files: <paths>`
STATUS ∈ `WORKING`, `CHECKPOINT`, `BLOCKED`, `DONE`.

**Checkpoint 1 (stop here this session):** scene builds from numbers, all 6 shots rendered as **drafts**, contact sheet made. Write a `CHECKPOINT` line with: what looks good, what you'd fix next, open questions, render times per shot at draft settings + estimated final times. Then end your session with a short summary. Do not start finals.

If blocked (Blender crash, CUDA error, missing info), write `BLOCKED` with the exact error and what you tried, then stop.
